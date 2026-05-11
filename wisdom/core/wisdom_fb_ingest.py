"""
wisdom_fb_ingest.py
====================
Facebook & TikTok Knowledge Ingestion Pipeline

Fixes:
  P-004: save_to_neo4j returns (post_id, neo4j_node_id) — real Neo4j elementId
  P-012: SHA-256 dedup check truoc khi ingest
  RULE-B: Them valid_from, source_type fields

Usage:
    python wisdom_fb_ingest.py --page "page_name" --limit 20
    python wisdom_fb_ingest.py --page "page_name" --cookies cookies.txt
    python wisdom_fb_ingest.py --url "https://www.facebook.com/..."
    python wisdom_fb_ingest.py --saved --cookies cookies.txt
"""

import os
import re
import sys
import json
import hashlib
import argparse
import requests
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
OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"
EMBED_MODEL  = "nomic-embed-text"
NEO4J_URI    = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER   = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS   = os.environ.get("NEO4J_PASS", "password123")
QDRANT_HOST  = "localhost"
QDRANT_PORT  = 6333
COLLECTION   = "wisdom_knowledge"
VECTOR_SIZE  = 768

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_embedding(text: str) -> list:
    try:
        response = requests.post(
            f"{OLLAMA_BASE}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=60,
        )
        return response.json().get("embedding", [0.0] * VECTOR_SIZE)
    except Exception as e:
        print(f"  Embedding ERROR: {e}")
        return [0.0] * VECTOR_SIZE


def analyze_with_ollama(text: str, source_url: str = "") -> dict:
    text = strip_emoji(text)
    print(f"  Analyzing with {OLLAMA_MODEL}...")
    prompt = f"""Analyze this Facebook post and extract structured knowledge.
Return ONLY valid JSON, no markdown, no explanation.

Source: {source_url}
Content: {text[:2000]}

Return this exact JSON:
{{
  "title": "short title summarizing the post",
  "summary": "2-3 sentence summary",
  "key_concepts": ["concept1", "concept2"],
  "insights": ["insight1", "insight2"],
  "tags": ["tag1", "tag2"],
  "language": "vi or en",
  "value_flywheel": "learning or experience or earning or contribution or growth",
  "content_type": "educational or news or opinion or entertainment or promotion"
}}"""
    try:
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
        return json.loads(raw.strip())
    except Exception as e:
        print(f"  Ollama ERROR: {e}")
        return {
            "title": text[:60],
            "summary": text[:200],
            "key_concepts": [],
            "insights": [],
            "tags": ["facebook"],
            "language": "vi",
            "value_flywheel": "learning",
            "content_type": "unknown",
        }

# ── Storage ───────────────────────────────────────────────────────────────────

def save_to_neo4j(post_id: str, post: dict, analysis: dict, source: str) -> tuple[str, object]:
    """
    Luu SocialPost node vao Neo4j.

    Returns:
        (post_id, neo4j_node_id)
        neo4j_node_id: elementId(p) — bridge sang Qdrant (P-004)
    """
    print("  Saving to Neo4j...")
    neo4j_node_id = None
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            # P-004: RETURN elementId(p)
            # RULE-B: them valid_from, source_type
            result = session.run(
                """
                MERGE (p:SocialPost {id: $id})
                SET p.url              = $url,
                    p.title            = $title,
                    p.summary          = $summary,
                    p.source           = $source,
                    p.platform         = $platform,
                    p.language         = $language,
                    p.value_flywheel   = $flywheel,
                    p.content_type     = $content_type,
                    p.ingested_at      = $ingested_at,
                    p.trust_score      = 0.7,
                    p.decay_lambda     = 0.003,
                    p.valid_from       = $valid_from,
                    p.valid_until      = null,
                    p.epistemic_status = 'PENDING',
                    p.cultural_context = 'GLOBAL',
                    p.source_type      = 'SOCIAL'
                RETURN elementId(p) AS node_id
                """,
                id=post_id,
                url=post.get("post_url", ""),
                title=strip_emoji(analysis.get("title", "")),
                summary=strip_emoji(analysis.get("summary", "")),
                source=source,
                platform=post.get("platform", "facebook"),
                language=analysis.get("language", "vi"),
                flywheel=analysis.get("value_flywheel", "learning"),
                content_type=analysis.get("content_type", "unknown"),
                ingested_at=datetime.now().isoformat(),
                valid_from=datetime.now().isoformat(),
            )
            record = result.single()
            if record:
                neo4j_node_id = record["node_id"]

            for concept in analysis.get("key_concepts", []):
                concept = strip_emoji(concept)
                if concept:
                    session.run(
                        """
                        MERGE (c:Concept {name: $name})
                        WITH c MATCH (p:SocialPost {id: $post_id})
                        MERGE (p)-[:HAS_CONCEPT]->(c)
                        """,
                        name=concept, post_id=post_id,
                    )
            for tag in analysis.get("tags", []):
                tag = strip_emoji(tag)
                if tag:
                    session.run(
                        """
                        MERGE (t:Tag {name: $name})
                        WITH t MATCH (p:SocialPost {id: $post_id})
                        MERGE (p)-[:HAS_TAG]->(t)
                        """,
                        name=tag, post_id=post_id,
                    )

        driver.close()
        print(f"  Neo4j: node_id={neo4j_node_id} | {len(analysis.get('key_concepts', []))} concepts saved")
    except Exception as e:
        print(f"  Neo4j ERROR: {e}")
    return post_id, neo4j_node_id


def save_to_qdrant(post_id: str, neo4j_node_id, post: dict, analysis: dict):
    """P-004: nhan neo4j_node_id lam payload bridge."""
    print("  Saving to Qdrant...")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION not in existing:
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
        text_to_embed = strip_emoji(
            f"{analysis.get('title', '')} {analysis.get('summary', '')} "
            f"{' '.join(analysis.get('key_concepts', []))}"
        )
        embedding = get_embedding(text_to_embed)
        if len(embedding) != VECTOR_SIZE:
            print("  WARNING: Embedding size mismatch, skipping")
            return
        point_id = int(hashlib.md5(post_id.encode()).hexdigest()[:8], 16)
        client.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "neo4j_node_id":  neo4j_node_id,  # P-004
                    "post_id":        post_id,
                    "url":            post.get("post_url", ""),
                    "title":          analysis.get("title", ""),
                    "summary":        analysis.get("summary", ""),
                    "tags":           analysis.get("tags", []),
                    "key_concepts":   analysis.get("key_concepts", []),
                    "platform":       post.get("platform", "facebook"),
                    "value_flywheel": analysis.get("value_flywheel", "learning"),
                    "source":         "fb_ingest",
                    "ingested_at":    datetime.now().isoformat(),
                },
            )]
        )
        print(f"  Qdrant: vector saved | neo4j_node_id={neo4j_node_id}")
    except Exception as e:
        print(f"  Qdrant ERROR: {e}")

# ── P-012: shared dedup helper ────────────────────────────────────────────────

def _dedup_check(key: str, label: str) -> bool:
    """Returns True nếu đã tồn tại (should skip). Non-blocking."""
    if _dedup is None:
        return False
    try:
        h = hashlib.sha256(key.encode()).hexdigest()
        if _dedup.check_duplicate(h).get("is_duplicate", False):
            print(f"  [DEDUP] {label} da ton tai, skip.")
            return True
    except Exception as e:
        print(f"  [DEDUP] Check failed (non-blocking): {e}")
    return False


def _dedup_register(key: str):
    if _dedup is None:
        return
    try:
        _dedup.register_checksum("", hashlib.sha256(key.encode()).hexdigest(), key, datetime.now().isoformat())
    except Exception as e:
        print(f"  [DEDUP] Register failed (non-blocking): {e}")

# ── Ingest functions ──────────────────────────────────────────────────────────

def _process_post(post: dict, source: str, post_id: str):
    """Shared ingest logic cho 1 post sau khi da lay duoc text."""
    text     = strip_emoji(post.get("text") or post.get("post_text") or "")
    post_url = post.get("post_url", "")

    if _dedup_check(text, f"post {post_id}"):
        return

    analysis = analyze_with_ollama(text, post_url)
    print(f"  Title: {analysis.get('title', '')[:60]}")

    post_id, neo4j_node_id = save_to_neo4j(post_id, post, analysis, source)
    save_to_qdrant(post_id, neo4j_node_id, post, analysis)
    _dedup_register(text)
    _dedup_register(post_url)


def ingest_fb_page(page_name: str, limit: int = 10, cookies: str = None):
    print(f"\n{'='*60}")
    print(f"  FB PAGE INGEST: {page_name} (limit: {limit})")
    print(f"{'='*60}\n")
    try:
        from facebook_scraper import get_posts
    except ImportError:
        print("  ERROR: Chua cai facebook-scraper")
        print("  Chay: pip install facebook-scraper")
        return

    count = 0
    try:
        kwargs = {"pages": max(1, limit // 10), "options": {"posts_per_page": limit}}
        if cookies:
            kwargs["cookies"] = cookies
            print(f"  Using cookies: {cookies}")

        for post in get_posts(page_name, **kwargs):
            if count >= limit:
                break
            text = strip_emoji(post.get("text") or post.get("post_text") or "")
            if not text or len(text) < 30:
                continue
            post_url = post.get("post_url", "")
            post_id  = (
                hashlib.md5(post_url.encode()).hexdigest()[:12]
                if post_url
                else hashlib.md5(f"{page_name}{count}".encode()).hexdigest()[:12]
            )

            # P-012: dedup check
            if _dedup_check(post_url or text, f"[{count+1}/{limit}]"):
                count += 1
                continue

            post["platform"] = "facebook"
            print(f"\n  [{count+1}/{limit}] {text[:80]}...")
            analysis = analyze_with_ollama(text, post_url)
            post_id, neo4j_node_id = save_to_neo4j(post_id, post, analysis, page_name)
            save_to_qdrant(post_id, neo4j_node_id, post, analysis)
            _dedup_register(post_url or text)
            count += 1

    except Exception as e:
        print(f"  Scraping ERROR: {e}")
        print("  Tip: Thu them --cookies neu bi block")
    print(f"\n  DONE: {count} posts ingested from {page_name}")


def ingest_fb_saved(cookies: str):
    print(f"\n{'='*60}")
    print("  FB SAVED POSTS INGEST")
    print(f"{'='*60}\n")
    if not cookies or not os.path.exists(cookies):
        print("  ERROR: Can file cookies.txt")
        return
    try:
        from facebook_scraper import get_posts
        count = 0
        for post in get_posts("saved", cookies=cookies, pages=3):
            text = strip_emoji(post.get("text") or post.get("post_text") or "")
            if not text or len(text) < 30:
                continue
            post_url = post.get("post_url", "")
            post_id  = hashlib.md5(f"saved_{post_url}".encode()).hexdigest()[:12]

            if _dedup_check(post_url or text, f"saved post {count+1}"):
                count += 1
                continue

            post["platform"] = "facebook_saved"
            print(f"\n  [Saved {count+1}] {text[:80]}...")
            analysis = analyze_with_ollama(text, post_url)
            post_id, neo4j_node_id = save_to_neo4j(post_id, post, analysis, "fb_saved")
            save_to_qdrant(post_id, neo4j_node_id, post, analysis)
            _dedup_register(post_url or text)
            count += 1
        print(f"\n  DONE: {count} saved posts ingested")
    except Exception as e:
        print(f"  Saved posts ERROR: {e}")


def ingest_fb_url(url: str, cookies: str = None):
    print(f"\n{'='*60}")
    print(f"  FB URL INGEST: {url[:80]}")
    print(f"{'='*60}\n")

    if _dedup_check(url, f"URL {url[:60]}"):
        return

    try:
        from facebook_scraper import get_posts
        kwargs = {"pages": 1}
        if cookies:
            kwargs["cookies"] = cookies
        for post in get_posts(post_urls=[url], **kwargs):
            text = strip_emoji(post.get("text") or post.get("post_text") or "")
            if not text:
                print("  WARNING: Khong lay duoc text")
                return
            post_id = hashlib.md5(url.encode()).hexdigest()[:12]
            post["platform"] = "facebook"
            print(f"  Content: {text[:100]}...")
            analysis = analyze_with_ollama(text, url)
            post_id, neo4j_node_id = save_to_neo4j(post_id, post, analysis, url)
            save_to_qdrant(post_id, neo4j_node_id, post, analysis)
            _dedup_register(url)
            print("\n  DONE: Post ingested!")
            return
    except Exception as e:
        print(f"  URL ingest ERROR: {e}")

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wisdom FB Ingestion Pipeline")
    parser.add_argument("--page",    type=str,            help="Facebook page/group name")
    parser.add_argument("--url",     type=str,            help="Facebook post URL")
    parser.add_argument("--saved",   action="store_true", help="Ingest saved posts")
    parser.add_argument("--cookies", type=str,            help="Path den cookies.txt")
    parser.add_argument("--limit",   type=int, default=10, help="So posts (default: 10)")
    args = parser.parse_args()

    if args.url:
        ingest_fb_url(args.url, args.cookies)
    elif args.saved:
        ingest_fb_saved(args.cookies)
    elif args.page:
        ingest_fb_page(args.page, args.limit, args.cookies)
    else:
        parser.print_help()
        print("\n  Quick test:")
        print("  python wisdom_fb_ingest.py --page vnexpress.net --limit 3")


if __name__ == "__main__":
    main()
