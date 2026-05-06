"""
wisdom_schema.py
=================
Tao toan bo Neo4j Schema cho Wisdom 4-Layer Architecture.
Chay 1 lan duy nhat de setup database.

Usage:
    python wisdom/core/wisdom_schema.py
"""

import os
from neo4j import GraphDatabase

NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")

SCHEMA_QUERIES = [

    # ── CONSTRAINTS ───────────────────────────────────────────────
    # Tang 1: INBOX
    "CREATE CONSTRAINT inbox_id IF NOT EXISTS FOR (n:InboxItem) REQUIRE n.id IS UNIQUE",

    # Tang 2: RAW
    "CREATE CONSTRAINT raw_id IF NOT EXISTS FOR (n:RawSource) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT raw_hash IF NOT EXISTS FOR (n:RawSource) REQUIRE n.content_hash IS UNIQUE",

    # Tang 3: WIKI
    "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (n:Concept) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT rule_id IF NOT EXISTS FOR (n:Rule) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT case_id IF NOT EXISTS FOR (n:CaseStudy) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT framework_id IF NOT EXISTS FOR (n:Framework) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT insight_id IF NOT EXISTS FOR (n:Insight) REQUIRE n.id IS UNIQUE",

    # Tang 4: OUTBOX
    "CREATE CONSTRAINT blueprint_id IF NOT EXISTS FOR (n:Blueprint) REQUIRE n.id IS UNIQUE",

    # ── INDEXES ───────────────────────────────────────────────────
    # Tang 1: INBOX - tim kiem theo status va urgency
    "CREATE INDEX inbox_status IF NOT EXISTS FOR (n:InboxItem) ON (n.epistemic_status)",
    "CREATE INDEX inbox_urgency IF NOT EXISTS FOR (n:InboxItem) ON (n.urgency)",
    "CREATE INDEX inbox_checksum IF NOT EXISTS FOR (n:InboxItem) ON (n.sha256_checksum)",

    # Tang 2: RAW - tim kiem theo timestamp va source
    "CREATE INDEX raw_timestamp IF NOT EXISTS FOR (n:RawSource) ON (n.ingested_timestamp)",
    "CREATE INDEX raw_status IF NOT EXISTS FOR (n:RawSource) ON (n.epistemic_status)",

    # Tang 3: WIKI - tim kiem theo status, decay, review
    "CREATE INDEX wiki_status IF NOT EXISTS FOR (n:Concept) ON (n.epistemic_status)",
    "CREATE INDEX wiki_review IF NOT EXISTS FOR (n:Concept) ON (n.next_review)",
    "CREATE INDEX wiki_trust IF NOT EXISTS FOR (n:Concept) ON (n.trust_score)",
    "CREATE INDEX rule_status IF NOT EXISTS FOR (n:Rule) ON (n.epistemic_status)",
    "CREATE INDEX rule_review IF NOT EXISTS FOR (n:Rule) ON (n.next_review)",
    "CREATE INDEX rule_decay IF NOT EXISTS FOR (n:Rule) ON (n.decay_lambda)",

    # Tang 4: OUTBOX - tim kiem theo status va price
    "CREATE INDEX blueprint_status IF NOT EXISTS FOR (n:Blueprint) ON (n.status)",
    "CREATE INDEX blueprint_price IF NOT EXISTS FOR (n:Blueprint) ON (n.price)",
]

# ── Sample nodes de verify schema ─────────────────────────────────────────────
SAMPLE_QUERIES = [
    # Tang 1: INBOX sample
    """
    MERGE (i:InboxItem {id: 'inbox_sample_001'})
    SET i.raw_content     = 'Sample inbox item',
        i.source_url      = 'https://example.com',
        i.sha256_checksum = 'sample_hash_001',
        i.ingested_at     = datetime(),
        i.epistemic_status= 'UNVERIFIED',
        i.urgency         = 'med',
        i.niche           = 'Tech',
        i.auto_tags       = ['sample', 'test']
    """,

    # Tang 2: RAW sample
    """
    MERGE (r:RawSource {id: 'raw_sample_001'})
    SET r.content_hash      = 'sha256_sample_001',
        r.ingested_timestamp= datetime(),
        r.source_url        = 'https://example.com',
        r.raw_content       = 'Sample raw content',
        r.qdrant_vector_id  = 'qdrant_001',
        r.epistemic_status  = 'PENDING'
    """,

    # Tang 3: WIKI Rule sample
    """
    MERGE (w:Rule {id: 'rule_sample_001'})
    SET w.title           = 'Sample Rule',
        w.content         = 'Sample rule content',
        w.epistemic_status= 'VERIFIED',
        w.trust_score     = 0.85,
        w.decay_lambda    = 0.003,
        w.valid_from      = datetime(),
        w.valid_until     = null,
        w.review_cadence  = 'weekly',
        w.last_reviewed   = datetime(),
        w.next_review     = datetime(),
        w.red_team_score  = 0.8,
        w.ripeness_score  = 0.75
    """,

    # Tang 4: OUTBOX Blueprint sample
    """
    MERGE (b:Blueprint {id: 'blueprint_sample_001'})
    SET b.title       = 'Sample Blueprint',
        b.description = 'Sample blueprint description',
        b.wiki_nodes  = ['rule_sample_001'],
        b.price       = 29.0,
        b.status      = 'draft',
        b.created_at  = datetime(),
        b.downloads   = 0,
        b.rating      = 0.0
    """,

    # Relationships
    """
    MATCH (i:InboxItem {id: 'inbox_sample_001'})
    MATCH (r:RawSource {id: 'raw_sample_001'})
    MERGE (i)-[:PROMOTED_TO]->(r)
    """,
    """
    MATCH (r:RawSource {id: 'raw_sample_001'})
    MATCH (w:Rule {id: 'rule_sample_001'})
    MERGE (r)-[:DISTILLED_TO]->(w)
    """,
    """
    MATCH (w:Rule {id: 'rule_sample_001'})
    MATCH (b:Blueprint {id: 'blueprint_sample_001'})
    MERGE (w)-[:COMPILED_INTO]->(b)
    MERGE (b)-[:DERIVED_FROM]->(w)
    """,
]


def setup_schema():
    print("\n" + "="*60)
    print("  WISDOM SCHEMA SETUP")
    print("  4-Layer: INBOX -> RAW -> WIKI -> OUTBOX")
    print("="*60 + "\n")

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

        with driver.session() as session:
            # Tao constraints va indexes
            print("  Creating constraints & indexes...")
            for i, query in enumerate(SCHEMA_QUERIES):
                try:
                    session.run(query)
                    name = query.split("IF NOT EXISTS")[0].split("CREATE")[1].strip()
                    print(f"  OK: {name}")
                except Exception as e:
                    print(f"  SKIP: {e}")

            # Tao sample nodes
            print("\n  Creating sample nodes...")
            for query in SAMPLE_QUERIES:
                try:
                    session.run(query)
                except Exception as e:
                    print(f"  Sample ERROR: {e}")

        # Verify
        print("\n  Verifying schema...")
        with driver.session() as session:
            counts = {
                "InboxItem":  session.run("MATCH (n:InboxItem) RETURN count(n) AS c").single()["c"],
                "RawSource":  session.run("MATCH (n:RawSource) RETURN count(n) AS c").single()["c"],
                "Rule":       session.run("MATCH (n:Rule) RETURN count(n) AS c").single()["c"],
                "Blueprint":  session.run("MATCH (n:Blueprint) RETURN count(n) AS c").single()["c"],
            }
            for label, count in counts.items():
                print(f"  {label}: {count} node(s)")

            rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            print(f"  Relationships: {rels} total")

        driver.close()
        print("\n  SCHEMA SETUP COMPLETE!")
        print("  4-Layer Architecture ready in Neo4j")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        print("  Kiem tra Docker: docker-compose up -d")


if __name__ == "__main__":
    setup_schema()