"""
Wisdom Knowledge Ingestion Pipeline
watch-cli -> Ollama/Gemini (phan tich) -> Neo4j + Qdrant (luu tru)

Fixes:
  P-004: Neo4j -> Qdrant node_id bridge
  P-012: SHA-256 dedup check
  RULE-B: Du 6 required fields
  P-075: Chunk transcript (fix [:3000] bug)
  P-075: Fallback transcript (yt-dlp + youtube_transcript_api)
  P-075: Dark Matter schema fields
  P-075: Gemini fallback cho video > 10 phut
  P-075: OPC domain filter

Usage:
    python wisdom_ingest.py <youtube_url>
    python wisdom_ingest.py <youtube_url> --deep   # Force Gemini
"""

import subprocess
import requests
import json
import hashlib
import sys
import re
import os
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
OLLAMA_BASE   = "http://localhost:11434"
OLLAMA_MODEL  = "llama3.1:8b"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL  = "gemini-2.0-flash"
GEMINI_URL    = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
NEO4J_URI     = "bolt://localhost:7687"
NEO4J_USER    = "neo4j"
NEO4J_PASS    = "password123"
QDRANT_HOST   = "localhost"
QDRANT_PORT   = 6333
COLLECTION    = "wisdom_knowledge"
EMBED_MODEL   = "nomic-embed-text"
VECTOR_SIZE   = 768
CHUNK_SIZE    = 3000   # ky tu moi chunk
DEEP_THRESHOLD = 600  # giay — video > 10 phut dung Gemini

# OPC domain tags
OPC_DOMAINS = ["knowledge", "workflow", "monetization", "tools", "mindset"]


# ── P-075 Fix 1: Chunk + Merge transcript ────────────────────────────────────

def chunk_transcript(transcript: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Chia transcript thanh cac chunks de xu ly toan bo, khong cat ngan."""
    words = transcript.split()
    chunks, current, length = [], [], 0
    for word in words:
        current.append(word)
        length += len(word) + 1
        if length >= chunk_size:
            chunks.append(" ".join(current))
            current, length = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks


def merge_chunk_analyses(analyses: list[dict]) -> dict:
    """Gop ket qua phan tich tu nhieu chunks thanh 1 ket qua tong hop."""
    if not analyses:
        return {}
    if len(analyses) == 1:
        return analyses[0]

    merged = {
        "title": analyses[0].get("title", ""),
        "summary": " ".join([a.get("summary", "") for a in analyses[:3]]),
        "key_concepts": [],
        "insights": [],
        "tags": [],
        "reasoning_chain": [],
        "action_steps": [],
        "opc_applicability": "",
        "key_quotes": [],
        "contradictions": [],
        "related_concepts": [],
        "opc_domain": [],
        "language": analyses[0].get("language", "en"),
        "value_flywheel": analyses[0].get("value_flywheel", "learning"),
    }

    seen_concepts, seen_insights, seen_tags = set(), set(), set()
    for a in analyses:
        for c in a.get("key_concepts", []):
            if c not in seen_concepts:
                merged["key_concepts"].append(c)
                seen_concepts.add(c)
        for i in a.get("insights", []):
            if i not in seen_insights:
                merged["insights"].append(i)
                seen_insights.add(i)
        for t in a.get("tags", []):
            if t not in seen_tags:
                merged["tags"].append(t)
                seen_tags.add(t)
        merged["reasoning_chain"].extend(a.get("reasoning_chain", []))
        merged["action_steps"].extend(a.get("action_steps", []))
        merged["key_quotes"].extend(a.get("key_quotes", []))
        merged["contradictions"].extend(a.get("contradictions", []))
        merged["related_concepts"].extend(a.get("related_concepts", []))
        if not merged["opc_applicability"] and a.get("opc_applicability"):
            merged["opc_applicability"] = a["opc_applicability"]
        for d in a.get("opc_domain", []):
            if d in OPC_DOMAINS and d not in merged["opc_domain"]:
                merged["opc_domain"].append(d)

    # Gioi han de khong qua dai
    merged["key_concepts"]    = merged["key_concepts"][:15]
    merged["insights"]        = merged["insights"][:10]
    merged["tags"]            = merged["tags"][:10]
    merged["reasoning_chain"] = merged["reasoning_chain"][:5]
    merged["action_steps"]    = merged["action_steps"][:8]
    merged["key_quotes"]      = merged["key_quotes"][:5]
    merged["contradictions"]  = merged["contradictions"][:3]
    merged["related_concepts"]= merged["related_concepts"][:8]

    return merged


# ── P-075 Fix 2: Fallback transcript ─────────────────────────────────────────

def run_watch_cli(url: str) -> dict:
    """Chay watch-cli. Neu that bai → fallback sang yt-dlp + youtube_transcript_api."""
    print(f"[1/4]  Downloading & transcribing: {url}")
    data = {"url": url, "video": "", "duration": 0, "frames": [], "transcript": ""}

    # --- Primary: watch-cli ---
    try:
        result = subprocess.run(
            ["C:/Program Files/Git/bin/bash.exe", "-c", f"watch '{url}' --cookies-from-browser chrome"],
            capture_output=True, text=True, encoding="utf-8", timeout=120,
        )
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
    except Exception as e:
        print(f"   watch-cli failed: {e}")

    # --- Fallback: youtube_transcript_api ---
    if not data["transcript"]:
        print("   watch-cli: no transcript. Trying youtube_transcript_api fallback...")
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            video_id = re.search(r"(?:v=|youtu\.be/)([^&?/]+)", url)
            if video_id:
                vid = video_id.group(1)
                transcript_list = YouTubeTranscriptApi.get_transcript(vid, languages=["vi", "en"])
                data["transcript"] = " ".join([t["text"] for t in transcript_list])
                print(f"   Fallback OK: {len(data['transcript'])} chars from youtube_transcript_api")
        except Exception as e:
            print(f"   youtube_transcript_api failed: {e}")

    # --- Fallback 2: yt-dlp subtitle ---
    if not data["transcript"]:
        print("   Trying yt-dlp subtitle fallback...")
        try:
            result = subprocess.run(
                ["yt-dlp", "--skip-download", "--write-auto-sub",
                 "--sub-lang", "vi,en", "--sub-format", "vtt",
                 "-o", "/tmp/wisdom_sub", url],
                capture_output=True, text=True, timeout=60,
            )
            for ext in ["vi.vtt", "en.vtt"]:
                sub_path = f"/tmp/wisdom_sub.{ext}"
                if os.path.exists(sub_path):
                    with open(sub_path, encoding="utf-8") as f:
                        lines = [l.strip() for l in f if l.strip()
                                 and not l.startswith("WEBVTT")
                                 and not re.match(r"^\d+:\d+", l)
                                 and "-->" not in l]
                    data["transcript"] = " ".join(lines)
                    print(f"   yt-dlp fallback OK: {len(data['transcript'])} chars")
                    break
        except Exception as e:
            print(f"   yt-dlp fallback failed: {e}")

    return data


# ── LLM helpers ───────────────────────────────────────────────────────────────

ANALYSIS_PROMPT = """Analyze this video transcript chunk and extract structured knowledge.
Return ONLY valid JSON, no markdown, no explanation.

URL: {url}
Transcript chunk ({chunk_num}/{total_chunks}):
{chunk}

Return EXACTLY this JSON structure:
{{
  "title": "video title or topic",
  "summary": "2-3 sentence summary of THIS chunk",
  "key_concepts": ["concept1", "concept2", "concept3"],
  "insights": ["actionable insight1", "insight2"],
  "tags": ["tag1", "tag2", "tag3"],
  "reasoning_chain": ["premise1 → premise2 → conclusion"],
  "action_steps": ["Step 1: ...", "Step 2: ..."],
  "opc_applicability": "How to apply this specifically for a One Person Company",
  "key_quotes": ["most memorable quote from transcript"],
  "contradictions": ["point that could be debated or challenged"],
  "related_concepts": ["concept to research further"],
  "opc_domain": ["one or more of: knowledge, workflow, monetization, tools, mindset"],
  "language": "vi or en",
  "value_flywheel": "learning or experience or earning or contribution or growth"
}}"""


def parse_llm_response(raw: str, transcript: str) -> dict:
    """Parse JSON tu LLM response, fallback neu loi."""
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "title": "Unknown", "summary": transcript[:200],
            "key_concepts": [], "insights": [], "tags": [],
            "reasoning_chain": [], "action_steps": [],
            "opc_applicability": "", "key_quotes": [],
            "contradictions": [], "related_concepts": [],
            "opc_domain": [], "language": "en", "value_flywheel": "learning",
        }


def analyze_chunk_ollama(chunk: str, url: str, chunk_num: int, total: int) -> dict:
    prompt = ANALYSIS_PROMPT.format(
        url=url, chunk=chunk, chunk_num=chunk_num, total_chunks=total
    )
    try:
        response = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        raw = response.json().get("response", "{}").strip()
        return parse_llm_response(raw, chunk)
    except Exception as e:
        print(f"   Ollama chunk {chunk_num} ERROR: {e}")
        return {}


def analyze_chunk_gemini(chunk: str, url: str, chunk_num: int, total: int) -> dict:
    """Dung Gemini API cho video dai (> 10 phut). Lay key tu .env."""
    if not GEMINI_API_KEY:
        print("   GEMINI_API_KEY not set, falling back to Ollama")
        return analyze_chunk_ollama(chunk, url, chunk_num, total)

    prompt = ANALYSIS_PROMPT.format(
        url=url, chunk=chunk, chunk_num=chunk_num, total_chunks=total
    )
    try:
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
        raw = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return parse_llm_response(raw, chunk)
    except Exception as e:
        print(f"   Gemini chunk {chunk_num} ERROR: {e} — falling back to Ollama")
        return analyze_chunk_ollama(chunk, url, chunk_num, total)


# ── P-075 Fix 3: Full analyze với chunk + model routing ──────────────────────

def analyze_with_ollama(transcript: str, url: str, duration: int = 0, force_deep: bool = False) -> dict:
    """
    Phan tich TOAN BO transcript bang cach chia chunks.
    Video > 10 phut hoac --deep flag → dung Gemini.
    """
    transcript = strip_emoji(transcript)
    url = strip_emoji(url)

    use_gemini = force_deep or (duration > DEEP_THRESHOLD and bool(GEMINI_API_KEY))
    model_name = f"Gemini ({GEMINI_MODEL})" if use_gemini else OLLAMA_MODEL
    print(f"[2/4]  Analyzing with {model_name}...")
    print(f"   Transcript length: {len(transcript):,} chars")

    chunks = chunk_transcript(transcript, CHUNK_SIZE)
    total = len(chunks)
    print(f"   Chunks: {total} x ~{CHUNK_SIZE} chars")

    analyses = []
    for i, chunk in enumerate(chunks, 1):
        print(f"   Processing chunk {i}/{total}...")
        if use_gemini:
            result = analyze_chunk_gemini(chunk, url, i, total)
        else:
            result = analyze_chunk_ollama(chunk, url, i, total)
        if result:
            analyses.append(result)

    merged = merge_chunk_analyses(analyses)
    print(f"   Merged: {len(merged.get('key_concepts', []))} concepts | "
          f"{len(merged.get('reasoning_chain', []))} chains | "
          f"{len(merged.get('action_steps', []))} steps")
    return merged


# ── Neo4j + Qdrant (giu nguyen logic cu, them dark matter fields) ─────────────

def get_embedding(text: str) -> list[float]:
    response = requests.post(
        f"{OLLAMA_BASE}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    return response.json().get("embedding", [0.0] * VECTOR_SIZE)


def save_to_neo4j(data: dict, analysis: dict) -> tuple[str, int]:
    print("[3/4]  Saving to Neo4j...")
    content_id = hashlib.md5(data["url"].encode()).hexdigest()[:12]
    neo4j_node_id = None

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            result = session.run(
                """
                MERGE (v:Video {id: $id})
                SET v.url               = $url,
                    v.title             = $title,
                    v.summary           = $summary,
                    v.duration          = $duration,
                    v.language          = $language,
                    v.value_flywheel    = $flywheel,
                    v.ingested_at       = $ingested_at,
                    v.trust_score       = 0.8,
                    v.decay_lambda      = 0.003,
                    v.valid_from        = $valid_from,
                    v.valid_until       = null,
                    v.epistemic_status  = 'PENDING',
                    v.cultural_context  = 'GLOBAL',
                    v.source_type       = 'VIDEO',
                    v.opc_applicability = $opc_applicability,
                    v.opc_domain        = $opc_domain,
                    v.reasoning_chain   = $reasoning_chain,
                    v.action_steps      = $action_steps,
                    v.key_quotes        = $key_quotes,
                    v.contradictions    = $contradictions
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
                opc_applicability=analysis.get("opc_applicability", ""),
                opc_domain=analysis.get("opc_domain", []),
                reasoning_chain=analysis.get("reasoning_chain", []),
                action_steps=analysis.get("action_steps", []),
                key_quotes=analysis.get("key_quotes", []),
                contradictions=analysis.get("contradictions", []),
            )
            record = result.single()
            if record:
                neo4j_node_id = record["node_id"]

            for concept in analysis.get("key_concepts", []):
                session.run(
                    """
                    MERGE (c:Concept {name: $name})
                    WITH c MATCH (v:Video {id: $video_id})
                    MERGE (v)-[:HAS_CONCEPT]->(c)
                    """,
                    name=strip_emoji(concept), video_id=content_id,
                )

            for tag in analysis.get("tags", []):
                session.run(
                    """
                    MERGE (t:Tag {name: $name})
                    WITH t MATCH (v:Video {id: $video_id})
                    MERGE (v)-[:HAS_TAG]->(t)
                    """,
                    name=strip_emoji(tag), video_id=content_id,
                )

            # Related concepts → REFERS_TO edges (dark matter links)
            for related in analysis.get("related_concepts", []):
                session.run(
                    """
                    MERGE (c:Concept {name: $name})
                    WITH c MATCH (v:Video {id: $video_id})
                    MERGE (v)-[:REFERRED_BY]->(c)
                    """,
                    name=strip_emoji(related), video_id=content_id,
                )

        driver.close()
        print(f"   Neo4j: node_id={neo4j_node_id} | "
              f"{len(analysis.get('key_concepts', []))} concepts | "
              f"{len(analysis.get('reasoning_chain', []))} chains saved")

    except Exception as e:
        print(f"   Neo4j ERROR: {e}")

    return content_id, neo4j_node_id


def save_to_qdrant(content_id: str, neo4j_node_id, data: dict, analysis: dict):
    print("[4/4]  Saving to Qdrant...")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION not in existing:
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

        # Embed: title + summary + reasoning + opc (rich context)
        text_to_embed = " ".join(filter(None, [
            analysis.get("title", ""),
            analysis.get("summary", ""),
            analysis.get("opc_applicability", ""),
            " ".join(analysis.get("reasoning_chain", [])),
            data["transcript"][:500],
        ]))
        embedding = get_embedding(text_to_embed)

        if len(embedding) != VECTOR_SIZE:
            print(f"   Embedding size mismatch: {len(embedding)}, skipping")
            return

        point_id = int(hashlib.md5(content_id.encode()).hexdigest()[:8], 16)
        client.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "neo4j_node_id":    neo4j_node_id,
                    "content_id":       content_id,
                    "url":              data["url"],
                    "title":            analysis.get("title", ""),
                    "summary":          analysis.get("summary", ""),
                    "tags":             analysis.get("tags", []),
                    "key_concepts":     analysis.get("key_concepts", []),
                    "value_flywheel":   analysis.get("value_flywheel", "learning"),
                    "opc_domain":       analysis.get("opc_domain", []),
                    "opc_applicability": analysis.get("opc_applicability", ""),
                    "reasoning_chain":  analysis.get("reasoning_chain", []),
                    "action_steps":     analysis.get("action_steps", []),
                    "ingested_at":      datetime.now().isoformat(),
                },
            )],
        )
        print(f"   Qdrant: vector saved | neo4j_node_id={neo4j_node_id}")

    except Exception as e:
        print(f"   Qdrant ERROR: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def ingest(url: str, force_deep: bool = False):
    print(f"\n{'='*60}")
    print("  WISDOM KNOWLEDGE INGESTION")
    print(f"{'='*60}\n")

    url_hash = hashlib.sha256(url.encode()).hexdigest()
    if _dedup is not None:
        try:
            if _dedup.check_duplicate(url_hash).get("is_duplicate", False):
                print(f"  [DEDUP] URL da ton tai, skip: {url}")
                return None
        except Exception as e:
            print(f"  [DEDUP] Check failed (non-blocking): {e}")

    # Step 1: Transcript (co fallback)
    data = run_watch_cli(url)
    if not data["transcript"]:
        print("  No transcript found from any source. Aborting.")
        return None

    transcript_hash = hashlib.sha256(data["transcript"].encode()).hexdigest()
    if _dedup is not None:
        try:
            if _dedup.check_duplicate(transcript_hash).get("is_duplicate", False):
                print("  [DEDUP] Noi dung da ton tai, skip.")
                return None
        except Exception as e:
            print(f"  [DEDUP] Content check failed (non-blocking): {e}")

    print(f"   Transcript: {len(data['transcript']):,} chars | Duration: {data['duration']}s")

    # Step 2: Analyze toan bo transcript
    analysis = analyze_with_ollama(
        data["transcript"], url,
        duration=data["duration"],
        force_deep=force_deep
    )
    print(f"   Title:  {analysis.get('title')}")
    print(f"   Domain: {analysis.get('opc_domain')}")
    print(f"   OPC:    {analysis.get('opc_applicability', '')[:80]}")

    # Step 3: Neo4j
    content_id, neo4j_node_id = save_to_neo4j(data, analysis)

    # Step 4: Qdrant
    save_to_qdrant(content_id, neo4j_node_id, data, analysis)

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
    print(f"  Flywheel:      {analysis.get('value_flywheel')}")
    print(f"  OPC Domain:    {analysis.get('opc_domain')}")
    print(f"  Chains:        {len(analysis.get('reasoning_chain', []))}")
    print(f"  Action steps:  {len(analysis.get('action_steps', []))}")
    print(f"{'='*60}\n")

    return {"content_id": content_id, "neo4j_node_id": neo4j_node_id, "analysis": analysis}


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: python wisdom_ingest.py <url> [--deep]")
        sys.exit(1)
    force_deep = "--deep" in args
    url = next((a for a in args if not a.startswith("--")), "")
    ingest(url, force_deep=force_deep)
