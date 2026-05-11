"""
P-003: Schema Migration Script
===============================
Migration cho cac nodes cu trong Neo4j:
  1. Video + Document -> them RULE-B fields con thieu
  2. Video + Document -> tao RawSource node tuong ung (4-layer)
  3. Concept + Tag -> them id + RULE-B fields
  4. Verify ket qua

Usage:
    python wisdom/core/wisdom_migrate_p003.py
    python wisdom/core/wisdom_migrate_p003.py --dry-run
"""

import os
import sys
import hashlib
from datetime import datetime

from neo4j import GraphDatabase

NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")

DRY_RUN = "--dry-run" in sys.argv


def run(session, query, params=None, label=""):
    if DRY_RUN:
        print(f"  [DRY-RUN] {label}: {query[:80]}...")
        return None
    try:
        result = session.run(query, params or {})
        return result
    except Exception as e:
        print(f"  ERROR [{label}]: {e}")
        return None


def migrate_video_nodes(session):
    """
    1. Them RULE-B fields con thieu vao Video nodes
    2. Tao RawSource node tuong ung de map vao 4-layer
    """
    print("\n  [1/4] Migrating Video nodes...")
    videos = session.run("MATCH (v:Video) RETURN v").data()
    print(f"  Found: {len(videos)} Video nodes")

    for row in videos:
        v = row["v"]
        vid_id = v.get("id", "")
        now = datetime.now().isoformat()

        # Them RULE-B fields con thieu
        run(session, """
            MATCH (v:Video {id: $id})
            SET v.valid_from       = COALESCE(v.valid_from, $now),
                v.valid_until      = COALESCE(v.valid_until, null),
                v.trust_score      = COALESCE(v.trust_score, 0.8),
                v.decay_lambda     = COALESCE(v.decay_lambda, 0.003),
                v.epistemic_status = COALESCE(v.epistemic_status, 'PENDING'),
                v.cultural_context = COALESCE(v.cultural_context, 'GLOBAL'),
                v.source_type      = COALESCE(v.source_type, 'VIDEO'),
                v.migrated_at      = $now
        """, {"id": vid_id, "now": now}, f"Video RULE-B fix: {vid_id}")

        # Tao RawSource node tuong ung (4-layer bridge)
        raw_id = f"raw_video_{vid_id}"
        content_hash = hashlib.sha256(f"video_{vid_id}".encode()).hexdigest()
        run(session, """
            MERGE (r:RawSource {id: $raw_id})
            SET r.content_hash       = $content_hash,
                r.ingested_timestamp = $now,
                r.source_url         = $url,
                r.raw_content        = $summary,
                r.qdrant_vector_id   = $vid_id,
                r.epistemic_status   = 'PENDING',
                r.source_type        = 'VIDEO',
                r.migrated_from      = 'Video'
            WITH r
            MATCH (v:Video {id: $vid_id})
            MERGE (v)-[:PROMOTED_TO]->(r)
        """, {
            "raw_id":       raw_id,
            "content_hash": content_hash,
            "now":          now,
            "url":          v.get("url", ""),
            "summary":      v.get("summary", "")[:500],
            "vid_id":       vid_id,
        }, f"RawSource bridge: {vid_id}")

        print(f"  OK: Video {vid_id} -> RawSource {raw_id}")


def migrate_document_nodes(session):
    """
    1. Them RULE-B fields con thieu vao Document nodes
    2. Tao RawSource node tuong ung de map vao 4-layer
    """
    print("\n  [2/4] Migrating Document nodes...")
    docs = session.run("MATCH (d:Document) RETURN d").data()
    print(f"  Found: {len(docs)} Document nodes")

    for row in docs:
        d = row["d"]
        doc_id = d.get("id", "")
        now = datetime.now().isoformat()

        # Them RULE-B fields con thieu
        run(session, """
            MATCH (d:Document {id: $id})
            SET d.valid_from       = COALESCE(d.valid_from, $now),
                d.valid_until      = COALESCE(d.valid_until, null),
                d.trust_score      = COALESCE(d.trust_score, 0.8),
                d.decay_lambda     = COALESCE(d.decay_lambda, 0.003),
                d.epistemic_status = COALESCE(d.epistemic_status, 'PENDING'),
                d.cultural_context = COALESCE(d.cultural_context, 'GLOBAL'),
                d.source_type      = COALESCE(d.source_type, 'DOCUMENT'),
                d.migrated_at      = $now
        """, {"id": doc_id, "now": now}, f"Document RULE-B fix: {doc_id}")

        # Tao RawSource node tuong ung (4-layer bridge)
        raw_id = f"raw_doc_{doc_id}"
        content_hash = hashlib.sha256(f"doc_{doc_id}".encode()).hexdigest()
        run(session, """
            MERGE (r:RawSource {id: $raw_id})
            SET r.content_hash       = $content_hash,
                r.ingested_timestamp = $now,
                r.source_url         = $path,
                r.raw_content        = $summary,
                r.qdrant_vector_id   = $doc_id,
                r.epistemic_status   = 'PENDING',
                r.source_type        = 'DOCUMENT',
                r.migrated_from      = 'Document'
            WITH r
            MATCH (d:Document {id: $doc_id})
            MERGE (d)-[:PROMOTED_TO]->(r)
        """, {
            "raw_id":       raw_id,
            "content_hash": content_hash,
            "now":          now,
            "path":         d.get("path", ""),
            "summary":      d.get("summary", "")[:500],
            "doc_id":       doc_id,
        }, f"RawSource bridge: {doc_id}")

        print(f"  OK: Document {doc_id} -> RawSource {raw_id}")


def migrate_concept_nodes(session):
    """
    Them id + RULE-B fields vao Concept nodes cu (khong co id).
    """
    print("\n  [3/4] Migrating Concept nodes...")
    concepts = session.run("MATCH (c:Concept) RETURN c").data()
    print(f"  Found: {len(concepts)} Concept nodes")

    count = 0
    for row in concepts:
        c = row["c"]
        name = c.get("name", "")
        if not name:
            continue
        now = datetime.now().isoformat()
        concept_id = hashlib.md5(name.encode()).hexdigest()[:12]

        run(session, """
            MATCH (c:Concept {name: $name})
            SET c.id               = COALESCE(c.id, $id),
                c.trust_score      = COALESCE(c.trust_score, 0.7),
                c.decay_lambda     = COALESCE(c.decay_lambda, 0.003),
                c.valid_from       = COALESCE(c.valid_from, $now),
                c.valid_until      = COALESCE(c.valid_until, null),
                c.epistemic_status = COALESCE(c.epistemic_status, 'PENDING'),
                c.cultural_context = COALESCE(c.cultural_context, 'GLOBAL'),
                c.source_type      = COALESCE(c.source_type, 'CONCEPT'),
                c.migrated_at      = $now
        """, {"name": name, "id": concept_id, "now": now}, f"Concept: {name}")
        count += 1

    print(f"  OK: {count} Concept nodes migrated")


def migrate_tag_nodes(session):
    """
    Them id + basic fields vao Tag nodes cu.
    """
    print("\n  [4/4] Migrating Tag nodes...")
    tags = session.run("MATCH (t:Tag) RETURN t").data()
    print(f"  Found: {len(tags)} Tag nodes")

    count = 0
    for row in tags:
        t = row["t"]
        name = t.get("name", "")
        if not name:
            continue
        now = datetime.now().isoformat()
        tag_id = hashlib.md5(f"tag_{name}".encode()).hexdigest()[:12]

        run(session, """
            MATCH (t:Tag {name: $name})
            SET t.id          = COALESCE(t.id, $id),
                t.migrated_at = $now
        """, {"name": name, "id": tag_id, "now": now}, f"Tag: {name}")
        count += 1

    print(f"  OK: {count} Tag nodes migrated")


def verify(session):
    print("\n  VERIFICATION:")
    labels = ["Video", "Document", "Concept", "Tag", "RawSource", "InboxItem", "Rule", "Blueprint"]
    for label in labels:
        count = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
        print(f"  {label}: {count}")

    rels = session.run("MATCH ()-[r:PROMOTED_TO]->() RETURN count(r) AS c").single()["c"]
    print(f"  PROMOTED_TO relationships: {rels}")

    # Check RULE-B compliance
    missing = session.run("""
        MATCH (n)
        WHERE (n:Video OR n:Document)
        AND (n.source_type IS NULL OR n.valid_from IS NULL OR n.trust_score IS NULL)
        RETURN count(n) AS c
    """).single()["c"]
    print(f"  Nodes missing RULE-B fields: {missing} (should be 0)")


def main():
    print("\n" + "="*60)
    print("  P-003 SCHEMA MIGRATION")
    if DRY_RUN:
        print("  MODE: DRY-RUN (khong ghi vao DB)")
    print("="*60)

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            migrate_video_nodes(session)
            migrate_document_nodes(session)
            migrate_concept_nodes(session)
            migrate_tag_nodes(session)
            verify(session)
        driver.close()

        print("\n  P-003 MIGRATION COMPLETE!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n  FATAL ERROR: {e}")
        print("  Kiem tra Docker: docker ps")


if __name__ == "__main__":
    main()
