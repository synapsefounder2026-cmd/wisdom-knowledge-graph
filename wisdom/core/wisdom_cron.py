"""
wisdom_cron.py
===============
P-015: Scheduled auto-ingest tu wisdom_sources.json
Chay nhu Windows Task Scheduler hoac thu cong.

Schedule mac dinh:
  07:00 — ingest sources (websites + youtube)
  20:00 — decay update + backup

Usage:
    python wisdom/core/wisdom_cron.py --ingest-sources   # Ingest tat ca sources enabled
    python wisdom/core/wisdom_cron.py --decay            # Chay decay update
    python wisdom/core/wisdom_cron.py --backup           # Chay backup
    python wisdom/core/wisdom_cron.py --all              # Tat ca (dung cho scheduled task)
    python wisdom/core/wisdom_cron.py --list             # Liet ke tat ca sources
    python wisdom/core/wisdom_cron.py --add-url URL      # Them URL nhanh vao sources

Sources config: wisdom_sources.json (root folder)
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent.parent
SOURCES_FILE = ROOT / "wisdom_sources.json"
CORE_DIR    = ROOT / "wisdom" / "core"

sys.path.insert(0, str(CORE_DIR))

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def load_sources() -> dict:
    if not SOURCES_FILE.exists():
        log(f"WARNING: {SOURCES_FILE} not found — tao file moi")
        default = {
            "_comment": "Wisdom Auto-Ingest Sources",
            "youtube": [], "websites": [], "academic": [], "rss": []
        }
        with open(SOURCES_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        return default
    with open(SOURCES_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_sources(sources: dict):
    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)


def should_ingest(source: dict, cadence_filter: str = None) -> bool:
    """Kiem tra source co nen ingest hom nay khong."""
    if not source.get("enabled", True):
        return False
    if cadence_filter:
        return source.get("cadence", "daily") == cadence_filter
    return True


# ── Ingest functions ──────────────────────────────────────────────────────────

def ingest_website(source: dict) -> bool:
    """Ingest website qua wisdom_cleaner.py."""
    url = source.get("url", "")
    if not url:
        return False
    log(f"  [WEB] {source.get('label', url)[:60]}")
    try:
        from wisdom_cleaner import WisdomCleaner
        from neo4j import GraphDatabase
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct, VectorParams, Distance
        import hashlib
        import requests as req

        cleaner = WisdomCleaner()
        result  = cleaner.clean_url(url)

        if not result["success"] or not result["content"]:
            log(f"    SKIP: {result.get('error', 'No content')}")
            return False

        # Save to Neo4j
        NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
        NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
        NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")

        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        node_id = hashlib.md5(url.encode()).hexdigest()[:12]
        now     = datetime.now().isoformat()

        with driver.session() as s:
            # Dedup check
            existing = s.run(
                "MATCH (n {id: $id}) RETURN n.id AS id LIMIT 1", id=node_id
            ).single()
            if existing:
                log(f"    SKIP: Already exists ({node_id})")
                driver.close()
                return False

            rec = s.run("""
                MERGE (n:Document {id: $id})
                SET n.url              = $url,
                    n.title            = $title,
                    n.summary          = $summary,
                    n.filename         = $label,
                    n.language         = $lang,
                    n.word_count       = $wc,
                    n.ingested_at      = $now,
                    n.valid_from       = $now,
                    n.valid_until      = null,
                    n.trust_score      = 0.75,
                    n.decay_lambda     = $lambda,
                    n.epistemic_status = 'PENDING',
                    n.cultural_context = 'GLOBAL',
                    n.source_type      = 'WEB',
                    n.domain           = $domain
                RETURN elementId(n) AS neo4j_node_id
            """,
                id=node_id, url=url,
                title=result["title"][:200],
                summary=result["content"][:300],
                label=source.get("label", ""),
                lang=result["language"],
                wc=result["word_count"],
                now=now,
                domain=source.get("domain", "tech_news"),
                **{"lambda": 0.003 if source.get("domain") in ["principle","science"] else 0.01}
            ).single()
            neo4j_node_id = rec["neo4j_node_id"] if rec else None

        driver.close()
        log(f"    Neo4j: {node_id} | neo4j_node_id={neo4j_node_id}")

        # Save to Qdrant
        try:
            QDRANT_HOST = "localhost"
            QDRANT_PORT = 6333
            COLLECTION  = "wisdom_knowledge"
            VECTOR_SIZE = 768
            OLLAMA_BASE = "http://localhost:11434"
            EMBED_MODEL = "nomic-embed-text"

            embed_resp = req.post(
                f"{OLLAMA_BASE}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": f"{result['title']} {result['content'][:500]}"},
                timeout=60,
            )
            embedding = embed_resp.json().get("embedding", [])

            if len(embedding) == VECTOR_SIZE:
                client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
                existing_cols = [c.name for c in client.get_collections().collections]
                if COLLECTION not in existing_cols:
                    client.create_collection(
                        collection_name=COLLECTION,
                        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
                    )
                point_id = int(hashlib.md5(node_id.encode()).hexdigest()[:8], 16)
                client.upsert(
                    collection_name=COLLECTION,
                    points=[PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "neo4j_node_id": neo4j_node_id,
                            "content_id":    node_id,
                            "url":           url,
                            "title":         result["title"],
                            "summary":       result["content"][:300],
                            "source_type":   "WEB",
                            "domain":        source.get("domain", ""),
                            "ingested_at":   now,
                        },
                    )]
                )
                log(f"    Qdrant: vector saved")
        except Exception as e:
            log(f"    Qdrant WARNING (non-blocking): {e}")

        return True

    except Exception as e:
        log(f"    ERROR: {e}")
        return False


def ingest_youtube(source: dict) -> bool:
    """Ingest YouTube URL qua wisdom_ingest.py."""
    url = source.get("url", "")
    if not url:
        return False
    log(f"  [YT] {source.get('label', url)[:60]}")
    try:
        from wisdom_ingest import ingest
        result = ingest(url)
        if result:
            log(f"    OK: {result.get('analysis', {}).get('title', '')[:60]}")
            return True
        log("    SKIP: No transcript")
        return False
    except Exception as e:
        log(f"    ERROR: {e}")
        return False


# ── Main commands ─────────────────────────────────────────────────────────────

def cmd_ingest_sources(cadence: str = None):
    """Ingest tat ca sources enabled trong wisdom_sources.json."""
    log("=" * 60)
    log("WISDOM CRON — INGEST SOURCES")
    if cadence:
        log(f"Filter: cadence={cadence}")
    log("=" * 60)

    sources = load_sources()
    total = ok = skip = 0

    # Websites
    for src in sources.get("websites", []):
        if should_ingest(src, cadence):
            total += 1
            ok += 1 if ingest_website(src) else 0
        else:
            skip += 1

    # Academic
    for src in sources.get("academic", []):
        if should_ingest(src, cadence):
            total += 1
            ok += 1 if ingest_website(src) else 0
        else:
            skip += 1

    # YouTube
    for src in sources.get("youtube", []):
        if should_ingest(src, cadence):
            total += 1
            ok += 1 if ingest_youtube(src) else 0
        else:
            skip += 1

    log(f"\nDone: {ok}/{total} ingested | {skip} skipped (disabled/cadence)")


def cmd_decay():
    """Chay decay update."""
    log("WISDOM CRON — DECAY UPDATE")
    try:
        from wisdom_decay import WisdomDecay
        decay = WisdomDecay()
        decay.run_decay(dry_run=False)
        decay.close()
        log("Decay update complete")
    except Exception as e:
        log(f"Decay ERROR: {e}")


def cmd_backup():
    """Chay backup script."""
    log("WISDOM CRON — BACKUP")
    backup_script = ROOT / "backup_now.sh"
    if backup_script.exists():
        result = subprocess.run(
            ["C:/Program Files/Git/bin/bash.exe", str(backup_script)],
            capture_output=True, text=True, encoding="utf-8"
        )
        log(result.stdout or "Backup done")
        if result.stderr:
            log(f"Backup stderr: {result.stderr[:200]}")
    else:
        log(f"WARNING: {backup_script} not found")


def cmd_list():
    """Liet ke tat ca sources."""
    sources = load_sources()
    print(f"\n{'='*60}")
    print(f"  WISDOM SOURCES — {SOURCES_FILE}")
    print(f"{'='*60}")
    for category in ["youtube", "websites", "academic", "rss"]:
        items = sources.get(category, [])
        if not items:
            continue
        print(f"\n  [{category.upper()}]")
        for i, src in enumerate(items):
            status = "✓" if src.get("enabled") else "✗"
            print(f"  {status} [{i}] {src.get('label', src.get('url', ''))[:50]}")
            print(f"       {src.get('url', '')[:70]}")
            print(f"       cadence={src.get('cadence','daily')} | domain={src.get('domain','')}")
    print()


def cmd_add_url(url: str, category: str = "websites", label: str = "",
                cadence: str = "daily", domain: str = "tech_news"):
    """Them URL moi vao sources file."""
    sources = load_sources()
    if category not in sources:
        sources[category] = []

    # Check duplicate
    for src in sources[category]:
        if src.get("url") == url:
            log(f"URL da ton tai: {url}")
            return

    new_source = {
        "url":     url,
        "label":   label or url[:60],
        "enabled": True,
        "cadence": cadence,
        "domain":  domain,
    }
    sources[category].append(new_source)
    save_sources(sources)
    log(f"Added: {url} -> {category} (cadence={cadence}, domain={domain})")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wisdom Cron — Auto-ingest scheduler")
    parser.add_argument("--ingest-sources", action="store_true", help="Ingest tat ca sources enabled")
    parser.add_argument("--decay",          action="store_true", help="Chay decay update")
    parser.add_argument("--backup",         action="store_true", help="Chay backup")
    parser.add_argument("--all",            action="store_true", help="Ingest + decay + backup")
    parser.add_argument("--list",           action="store_true", help="Liet ke sources")
    parser.add_argument("--add-url",        type=str,            help="Them URL vao sources")
    parser.add_argument("--category",       type=str, default="websites",
                        help="Category: websites/youtube/academic/rss")
    parser.add_argument("--label",          type=str, default="", help="Ten hien thi")
    parser.add_argument("--cadence",        type=str, default="daily",
                        help="daily/weekly/monthly")
    parser.add_argument("--domain",         type=str, default="tech_news",
                        help="tech_news/market/mmo/framework/principle/science/learning")
    parser.add_argument("--morning",        action="store_true", help="Morning job (07:00)")
    parser.add_argument("--evening",        action="store_true", help="Evening job (20:00)")
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.add_url:
        cmd_add_url(args.add_url, args.category, args.label, args.cadence, args.domain)
    elif args.morning:
        cmd_ingest_sources(cadence="daily")
    elif args.evening:
        cmd_decay()
        cmd_backup()
    elif args.all:
        cmd_ingest_sources()
        cmd_decay()
        cmd_backup()
    elif args.ingest_sources:
        cmd_ingest_sources()
    elif args.decay:
        cmd_decay()
    elif args.backup:
        cmd_backup()
    else:
        parser.print_help()
        print("\n  Quick start:")
        print("  python wisdom/core/wisdom_cron.py --list")
        print("  python wisdom/core/wisdom_cron.py --add-url https://vnexpress.net/kinh-doanh --label 'VNExpress' --domain market")
        print("  python wisdom/core/wisdom_cron.py --ingest-sources")
        print("  python wisdom/core/wisdom_cron.py --morning   # 07:00 job")
        print("  python wisdom/core/wisdom_cron.py --evening   # 20:00 job")


if __name__ == "__main__":
    main()
