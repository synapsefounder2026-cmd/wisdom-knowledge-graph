"""
Wisdom Knowledge Ingestion Pipeline
watch-cli -> Ollama (phan tich) -> Neo4j + Qdrant (luu tru)

Fixes:
  P-004: Neo4j -> Qdrant node_id bridge (return real Neo4j node ID)
  P-012: SHA-256 dedup check truoc khi ingest
  RULE-B: Du 6 required fields (source_type added)
  Syntax fix: trailing comma trong Cypher SET

Usage:
    python wisdom_ingest.py <youtube_url>
"""

import subprocess
import requests
import json
import hashlib
import sys
import re
from datetime import datetime

try:
    import sys as _sys, os as _os
    _sys.path.append(_os.path.dirname(_os.path.abspath(__file__)))
    from wisdom_dedup import WisdomDedup
    _dedup = WisdomDedup()
except Exception as e:
    print(f"  Dedup warning: {e}")
    _dedup = None

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# ── Strip emoji ───────────────────────────────────────────────────────────────
def strip_emoji(text: str) -> str:
    """Strip emoji va ky tu dac biet gay loi encoding."""
    if not isinstance(text, str):
        return str(text) if text else ""
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002600-\U000027BF"
        u"\U0001F900-\U0001F9FF"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"
NEO4J_URI    = "bolt://localhost:7687"
NEO4J_USER   = "neo4j"
NEO4J_PASS   = "password123"
QDRANT_HOST  = "localhost"
QDRANT_PORT  = 6333
COLLECTION   = "wisdom_knowledge"
EMBED_MODEL  = "nomic-embed-text"
VECTOR_SIZE  = 768


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_watch_cli(url: str) -> dict:
    """Chay watch-cli va parse output thanh dict."""
    print(f"[1/4]  Downloading & transcribing: {url}")
    result = subprocess.run(
        ["C:/Program Files/Git/bin/bash.exe", "-c", f"watch '{url}' --cookies-from-browser chrome"],
        capture_output=True, text=True, encoding="utf-8",
    )
    data = {"url": url, "video": "", "duration": 0, "frames": [], "transcript": ""}
    section = None
    transcript_lines = []

    for line in result.stdout.split("\n"):
        line = line.strip()
        if line.startswith("VIDEO:"):
            data["video"] = line.replace("VIDEO:", "").strip()
        elif line.startswith("DURATION:"):
            try:
                data["duration"] = int(line.replace("DURATION:", "").strip())
            except Exception:
                pass
        elif line.startswith("FRAMES:"):
            section = "frames"
        elif line.startswith("TRANSCRIPT:"):
            section = "transcript"
        elif section == "frames" and line.startswith("/tmp/"):
            data["frames"].append(line)
        elif section == "transcript" and line:
            transcript_lines.append(line)

    data["transcript"] = " ".join(transcript_lines).strip()
    return data


def analyze_with_ollama(transcript: str, url: str) -> dict:
    """Gui transcript len Ollama de phan tich va extract knowledge."""
    transcript = strip_emoji(transcript)
    url = strip_emoji(url)
    print(f"[2/4]  Analyzing with {OLLAMA_MODEL}...")
    prompt = f"""Analyze this video transcript and extract structured knowledge.
Return ONLY valid JSON, no markdown, no explanation.

URL: {url}
Transcript: {transcript[:3000]}

Return this exact JSON structure:
{{
  "title": "video title or topic",
  "summary": "2-3 sentence summary",
  "key_concepts": ["concept1", "concept2", "concept3"],
  "insights": ["insight1", "insight2"],
  "tags": ["tag1", "tag2", "tag3"],
  "language": "vi or en",
  "value_flywheel": "which layer: learning/experience/earning/contribution/growth"
}}"""

    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    raw = response.json().get("response", "{}").strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("    JSON parse failed, using defaults")
        return {
            "title": "Unknown",
            "summary": transcript[:200],
            "key_concepts": [],
            "insights": [],
            "tags": [],
            "language": "en",
            "value_flywheel": "learning",
        }


def get_embedding(text: str) -> list[float]:
    """Lay embedding tu Ollama."""
    response = requests.post(
        f"{OLLAMA_BASE}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    return response.json().get("embedding", [0.0] * VECTOR_SIZE)


# ── P-004: save_to_neo4j returns REAL Neo4j internal node ID ─────────────────

def save_to_neo4j(data: dict, analysis: dict) -> tuple[str, int]:
    """
    Luu knowledge graph vao Neo4j.

    Returns:
        (content_id, neo4j_node_id)
        content_id   : MD5 hash cua URL (dung de dedup va reference)
        neo4j_node_id: Neo4j internal id(v) — dung lam bridge sang Qdrant (P-004)
    """
    print("[3/4]  Saving to Neo4j...")
    content_id = hashlib.md5(data["url"].encode()).hexdigest()[:12]
    neo4j_node_id = None

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            # RULE-B: Du 6 required fields + source_type
            # P-004: RETURN elementId(v) de lay Neo4j node ID
            result = session.run(
                """
                MERGE (v:Video {id: $id})
                SET v.url              = $url,
                    v.title            = $title,
                    v.summary          = $summary,
                    v.duration         = $duration,
                    v.language         = $language,
                    v.value_flywheel   = $flywheel,
                    v.ingested_at      = $ingested_at,
                    v.trust_score      = 0.8,
                    v.decay_lambda     = 0.003,
                    v.valid_from       = $valid_from,
                    v.valid_until      = null,
                    v.epistemic_status = 'PENDING',
                    v.cultural_context = 'GLOBAL',
                    v.source_type      = 'VIDEO'
                RETURN elementId(v) AS node_id
                """,
                id=content_id,
                url=data["url"],
                title=strip_emoji(analysis.get("title", "")),
                summary=strip_emoji(analysis.get("summary", "")),
                duration=data["duration"],
                language=analysis.get("language", "en"),
                flywheel=analysis.get("value_flywheel", "learning"),
                ingested_at=datetime.now().isoformat(),
                valid_from=datetime.now().isoformat(),
            )
            record = result.single()
            if record:
                neo4j_node_id = record["node_id"]

            # Concept nodes
            for concept in analysis.get("key_concepts", []):
                session.run(
                    """
                    MERGE (c:Concept {name: $name})
                    WITH c
                    MATCH (v:Video {id: $video_id})
                    MERGE (v)-[:HAS_CONCEPT]->(c)
                    """,
                    name=strip_emoji(concept),
                    video_id=content_id,
                )

            # Tag nodes
            for tag in analysis.get("tags", []):
                session.run(
                    """
                    MERGE (t:Tag {name: $name})
                    WITH t
                    MATCH (v:Video {id: $video_id})
                    MERGE (v)-[:HAS_TAG]->(t)
                    """,
                    name=strip_emoji(tag),
                    video_id=content_id,
                )

        driver.close()
        print(
            f"   Neo4j: node_id={neo4j_node_id} | "
            f"{len(analysis.get('key_concepts', []))} concepts saved"
        )

    except Exception as e:
        print(f"   Neo4j ERROR: {e}")

    return content_id, neo4j_node_id


# ── P-004: save_to_qdrant nhan neo4j_node_id lam payload ─────────────────────

def save_to_qdrant(content_id: str, neo4j_node_id, data: dict, analysis: dict):
    """
    Luu vector embedding vao Qdrant.
    neo4j_node_id duoc luu trong payload de bridge voi Neo4j (P-004).
    """
    print("[4/4]  Saving to Qdrant...")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION not in existing:
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            print(f"   Created collection: {COLLECTION}")

        text_to_embed = (
            f"{analysis.get('title', '')} "
            f"{analysis.get('summary', '')} "
            f"{data['transcript'][:1000]}"
        )
        embedding = get_embedding(text_to_embed)

        if len(embedding) != VECTOR_SIZE:
            print(f"    Embedding size mismatch: {len(embedding)} vs {VECTOR_SIZE}, skipping")
            return

        point_id = int(hashlib.md5(content_id.encode()).hexdigest()[:8], 16)
        client.upsert(
            collection_name=COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        # P-004: neo4j_node_id la cau noi chinh thuc
                        "neo4j_node_id": neo4j_node_id,
                        "content_id":    content_id,
                        "url":           data["url"],
                        "title":         analysis.get("title", ""),
                        "summary":       analysis.get("summary", ""),
                        "tags":          analysis.get("tags", []),
                        "key_concepts":  analysis.get("key_concepts", []),
                        "value_flywheel": analysis.get("value_flywheel", "learning"),
                        "ingested_at":   datetime.now().isoformat(),
                    },
                )
            ],
        )
        print(f"   Qdrant: vector saved | neo4j_node_id={neo4j_node_id}")

    except Exception as e:
        print(f"   Qdrant ERROR: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def ingest(url: str):
    print(f"\n{'='*60}")
    print("  WISDOM KNOWLEDGE INGESTION")
    print(f"{'='*60}\n")

    # P-012: Dedup check truoc moi thu
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    if _dedup is not None:
        try:
            if _dedup.check_duplicate(url_hash).get("is_duplicate", False):
                print(f"  [DEDUP] URL da ton tai, skip: {url}")
                return None
        except Exception as e:
            print(f"  [DEDUP] Check failed (non-blocking): {e}")

    # Step 1: watch-cli
    data = run_watch_cli(url)
    if not data["transcript"]:
        print("  No transcript found. Aborting.")
        return None

    # P-012: Dedup check tren transcript content
    transcript_hash = hashlib.sha256(data["transcript"].encode()).hexdigest()
    if _dedup is not None:
        try:
            if _dedup.check_duplicate(transcript_hash).get("is_duplicate", False):
                print("  [DEDUP] Noi dung da ton tai (transcript match), skip.")
                return None
        except Exception as e:
            print(f"  [DEDUP] Content check failed (non-blocking): {e}")

    print(f"   Transcript: {data['transcript'][:100]}...")

    # Step 2: Ollama analysis
    analysis = analyze_with_ollama(data["transcript"], url)
    print(f"   Title: {analysis.get('title')}")
    print(f"   Concepts: {', '.join(analysis.get('key_concepts', []))}")

    # Step 3: Neo4j — P-004: lay ca content_id va neo4j_node_id
    content_id, neo4j_node_id = save_to_neo4j(data, analysis)

    # Step 4: Qdrant — P-004: truyen neo4j_node_id vao
    save_to_qdrant(content_id, neo4j_node_id, data, analysis)

    # P-012: Dang ky hash sau khi ingest thanh cong
    if _dedup is not None:
        try:
            _dedup.register_checksum(str(neo4j_node_id), url_hash, url, datetime.now().isoformat())
            _dedup.register_checksum(str(neo4j_node_id), transcript_hash, data["url"], datetime.now().isoformat())
        except Exception as e:
            print(f"  [DEDUP] Register failed (non-blocking): {e}")

    print(f"\n{'='*60}")
    print("   INGESTION COMPLETE")
    print(f"  content_id:    {content_id}")
    print(f"  neo4j_node_id: {neo4j_node_id}")
    print(f"  Flywheel:      {analysis.get('value_flywheel', 'learning')}")
    print(f"{'='*60}\n")

    return {
        "content_id":    content_id,
        "neo4j_node_id": neo4j_node_id,
        "analysis":      analysis,
    }


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ingest(url)
