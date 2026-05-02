"""
Wisdom Knowledge Ingestion Pipeline
watch-cli  Ollama (phn tch)  Neo4j + Qdrant (lu tr)

Usage:
    python wisdom_ingest.py <youtube_url>
"""

import subprocess
import requests
import json
import hashlib
import sys
from datetime import datetime
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

#  Config 
OLLAMA_BASE    = "http://localhost:11434"
OLLAMA_MODEL   = "llama3.1:8b"
NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASS     = "password123"
QDRANT_HOST    = "localhost"
QDRANT_PORT    = 6333
COLLECTION     = "wisdom_knowledge"
EMBED_MODEL    = "nomic-embed-text"  # ollama pull nomic-embed-text nu cha c
VECTOR_SIZE    = 768

#  Helpers 

def run_watch_cli(url: str) -> dict:
    """Chy watch-cli v parse output thnh dict."""
    print(f"[1/4]  Downloading & transcribing: {url}")
    result = subprocess.run(
        ["C:/Program Files/Git/bin/bash.exe", "-c", f"watch '{url}' --cookies-from-browser chrome"],

        capture_output=True, text=True, encoding="utf-8"
    )
    output = result.stdout
    data = {"url": url, "video": "", "duration": 0, "frames": [], "transcript": ""}

    lines = output.split("\n")
    section = None
    transcript_lines = []

    for line in lines:
        line = line.strip()
        if line.startswith("VIDEO:"):
            data["video"] = line.replace("VIDEO:", "").strip()
        elif line.startswith("DURATION:"):
            try:
                data["duration"] = int(line.replace("DURATION:", "").strip())
            except:
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
    """Gi transcript ln Ollama  phn tch v extract knowledge."""
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
        timeout=120
    )
    raw = response.json().get("response", "{}")

    # Strip markdown fences nu c
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"    JSON parse failed, using defaults")
        return {
            "title": "Unknown",
            "summary": transcript[:200],
            "key_concepts": [],
            "insights": [],
            "tags": [],
            "language": "en",
            "value_flywheel": "learning"
        }


def get_embedding(text: str) -> list[float]:
    """Ly embedding t Ollama."""
    response = requests.post(
        f"{OLLAMA_BASE}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    return response.json().get("embedding", [0.0] * VECTOR_SIZE)


def save_to_neo4j(data: dict, analysis: dict):
    """Lu knowledge graph vo Neo4j."""
    print(f"[3/4]   Saving to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

    with driver.session() as session:
        # To Video node
        video_id = hashlib.md5(data["url"].encode()).hexdigest()[:12]
        session.run("""
            MERGE (v:Video {id: $id})
            SET v.url = $url,
                v.title = $title,
                v.summary = $summary,
                v.duration = $duration,
                v.language = $language,
                v.value_flywheel = $flywheel,
                v.ingested_at = $ingested_at
        """, id=video_id, url=data["url"], title=analysis.get("title", ""),
             summary=analysis.get("summary", ""), duration=data["duration"],
             language=analysis.get("language", "en"),
             flywheel=analysis.get("value_flywheel", "learning"),
             ingested_at=datetime.now().isoformat())

        # To Concept nodes v relationships
        for concept in analysis.get("key_concepts", []):
            session.run("""
                MERGE (c:Concept {name: $name})
                WITH c
                MATCH (v:Video {id: $video_id})
                MERGE (v)-[:HAS_CONCEPT]->(c)
            """, name=concept, video_id=video_id)

        # To Tag nodes
        for tag in analysis.get("tags", []):
            session.run("""
                MERGE (t:Tag {name: $name})
                WITH t
                MATCH (v:Video {id: $video_id})
                MERGE (v)-[:HAS_TAG]->(t)
            """, name=tag, video_id=video_id)

    driver.close()
    print(f"   Neo4j: Video node + {len(analysis.get('key_concepts', []))} concepts saved")
    return video_id


def save_to_qdrant(video_id: str, data: dict, analysis: dict):
    """Lu vector embedding vo Qdrant."""
    print(f"[4/4]  Saving to Qdrant...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # To collection nu cha c
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"   Created collection: {COLLECTION}")

    # Embed summary + transcript
    text_to_embed = f"{analysis.get('title', '')} {analysis.get('summary', '')} {data['transcript'][:1000]}"
    embedding = get_embedding(text_to_embed)

    if len(embedding) != VECTOR_SIZE:
        print(f"    Embedding size mismatch: {len(embedding)} vs {VECTOR_SIZE}, skipping Qdrant")
        return

    point_id = int(hashlib.md5(video_id.encode()).hexdigest()[:8], 16)
    client.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "video_id": video_id,
                "url": data["url"],
                "title": analysis.get("title", ""),
                "summary": analysis.get("summary", ""),
                "tags": analysis.get("tags", []),
                "key_concepts": analysis.get("key_concepts", []),
                "value_flywheel": analysis.get("value_flywheel", "learning"),
                "ingested_at": datetime.now().isoformat()
            }
        )]
    )
    print(f"   Qdrant: Vector saved to '{COLLECTION}'")


#  Main 

def ingest(url: str):
    print(f"\n{'='*60}")
    print(f"  WISDOM KNOWLEDGE INGESTION")
    print(f"{'='*60}\n")

    # Step 1: watch-cli
    data = run_watch_cli(url)
    if not data["transcript"]:
        print(" No transcript found. Aborting.")
        return

    print(f"   Transcript: {data['transcript'][:100]}...")

    # Step 2: Ollama analysis
    analysis = analyze_with_ollama(data["transcript"], url)
    print(f"   Title: {analysis.get('title')}")
    print(f"    Concepts: {', '.join(analysis.get('key_concepts', []))}")

    # Step 3: Neo4j
    video_id = save_to_neo4j(data, analysis)

    # Step 4: Qdrant
    save_to_qdrant(video_id, data, analysis)

    print(f"\n{'='*60}")
    print(f"   INGESTION COMPLETE")
    print(f"  Video ID: {video_id}")
    print(f"  Flywheel: {analysis.get('value_flywheel', 'learning')}")
    print(f"{'='*60}\n")

    return {"video_id": video_id, "analysis": analysis}


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ingest(url)
