"""
wisdom_decay.py
================
Temporal Decay Function — Tu dong giam trust_score theo thoi gian.
Chay nhu scheduled job hang ngay.

Formula: trust_score(t) = base_score * exp(-decay_lambda * age_days)

decay_lambda theo domain:
- Tech news/trends:  0.05  (outdated nhanh)
- Frameworks/Methods: 0.01
- Core principles:   0.003 (ben vung)
- Math/Science:      0.001 (gan nhu vinh vien)
- Market/MMO:        0.05  (thay doi hang ngay)

Usage:
    python wisdom/core/wisdom_decay.py --run
    python wisdom/core/wisdom_decay.py --report
    python wisdom/core/wisdom_decay.py --flag-outdated
"""

import os
import re
import math
import argparse
from datetime import datetime, timezone
from neo4j import GraphDatabase

# ── Config ────────────────────────────────────────────────────────────────────
NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")

# Nguong canh bao outdated
OUTDATED_THRESHOLD  = 0.3
WARNING_THRESHOLD   = 0.5

# Domain -> decay_lambda mac dinh
DOMAIN_DECAY = {
    "tech_news":    0.05,
    "mmo":          0.05,
    "market":       0.05,
    "framework":    0.01,
    "methodology":  0.01,
    "principle":    0.003,
    "science":      0.001,
    "math":         0.0001,
    "default":      0.003,
}


def strip_emoji(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text else ""
    p = re.compile(
        '[' + u'\U0001F600-\U0001F64F' + u'\U0001F300-\U0001F5FF'
        + u'\U0001F680-\U0001F6FF' + u'\U0001F1E0-\U0001F1FF'
        + u'\U00002600-\U000027BF' + u'\U0001F900-\U0001F9FF' + ']+',
        flags=re.UNICODE)
    return p.sub('', text).strip()


def compute_decay(base_score: float, decay_lambda: float,
                  age_days: float) -> float:
    """
    Tinh trust_score moi sau khi decay.
    trust_score(t) = base_score * exp(-lambda * age_days)
    """
    return round(base_score * math.exp(-decay_lambda * age_days), 4)


def get_age_days(ingested_at: str) -> float:
    """Tinh so ngay tu khi ingest den hom nay."""
    try:
        ingested = datetime.fromisoformat(ingested_at)
        if ingested.tzinfo is None:
            ingested = ingested.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - ingested).total_seconds() / 86400
    except Exception:
        return 0.0


class WisdomDecay:

    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
            print("WisdomDecay: Connected to Neo4j")
        except Exception as e:
            print(f"WisdomDecay: Connection failed: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def run_decay(self, dry_run: bool = False):
        """
        Chay decay cho tat ca nodes co trust_score va ingested_at.
        dry_run=True: chi tinh, khong update DB.
        """
        print(f"\n{'='*60}")
        print(f"  TEMPORAL DECAY — {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
        print(f"  Formula: trust_score * exp(-lambda * age_days)")
        print(f"{'='*60}\n")

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    WHERE n.trust_score IS NOT NULL
                    AND n.ingested_at IS NOT NULL
                    AND n.epistemic_status <> 'DEPRECATED'
                    RETURN n.id AS id, n.title AS title,
                           n.trust_score AS trust_score,
                           n.decay_lambda AS decay_lambda,
                           n.ingested_at AS ingested_at,
                           n.epistemic_status AS status,
                           labels(n)[0] AS label
                    ORDER BY n.trust_score ASC
                """)
                nodes = [dict(r) for r in result]
        except Exception as e:
            print(f"  Fetch ERROR: {e}")
            return

        if not nodes:
            print("  No nodes to decay.")
            return

        print(f"  Processing {len(nodes)} nodes...\n")
        outdated = []
        warning  = []
        updated  = 0

        for node in nodes:
            node_id     = node["id"]
            title       = strip_emoji(node.get("title") or "Unknown")
            base_score  = float(node.get("trust_score") or 0.8)
            decay_lambda= float(node.get("decay_lambda") or 0.003)
            ingested_at = node.get("ingested_at") or datetime.now().isoformat()
            status      = node.get("epistemic_status", "PENDING")

            age_days    = get_age_days(ingested_at)
            new_score   = compute_decay(base_score, decay_lambda, age_days)

            # Xac dinh trang thai moi
            if new_score < OUTDATED_THRESHOLD:
                new_status = "DEPRECATED"
                outdated.append({"id": node_id, "title": title,
                                 "score": new_score, "age": age_days})
            elif new_score < WARNING_THRESHOLD:
                new_status = status  # giu nguyen nhung flag warning
                warning.append({"id": node_id, "title": title,
                                "score": new_score, "age": age_days})
            else:
                new_status = status

            if not dry_run and abs(new_score - base_score) > 0.001:
                try:
                    with self.driver.session() as session:
                        session.run("""
                            MATCH (n {id: $id})
                            SET n.trust_score      = $new_score,
                                n.epistemic_status = $new_status,
                                n.last_decay_at    = $now
                        """, id=node_id, new_score=new_score,
                             new_status=new_status,
                             now=datetime.now().isoformat())
                    updated += 1
                except Exception as e:
                    print(f"  Update ERROR {node_id}: {e}")

        # Report
        print(f"  Results:")
        print(f"  Total nodes: {len(nodes)}")
        print(f"  Updated:     {updated}")
        print(f"  Outdated (< {OUTDATED_THRESHOLD}): {len(outdated)}")
        print(f"  Warning  (< {WARNING_THRESHOLD}): {len(warning)}")

        if outdated:
            print(f"\n  DEPRECATED nodes:")
            for n in outdated[:5]:
                print(f"  - {n['title'][:50]} (score: {n['score']:.3f}, age: {n['age']:.0f}d)")

        if warning:
            print(f"\n  WARNING nodes (needs review):")
            for n in warning[:5]:
                print(f"  - {n['title'][:50]} (score: {n['score']:.3f}, age: {n['age']:.0f}d)")

        print(f"\n  {'DRY RUN complete' if dry_run else 'DECAY UPDATE complete'}")

    def report(self):
        """Hien thi tong quan trust_score distribution."""
        print(f"\n{'='*60}")
        print(f"  DECAY REPORT — Trust Score Distribution")
        print(f"{'='*60}\n")

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    WHERE n.trust_score IS NOT NULL
                    RETURN
                        count(n) AS total,
                        avg(n.trust_score) AS avg_score,
                        min(n.trust_score) AS min_score,
                        max(n.trust_score) AS max_score,
                        sum(CASE WHEN n.trust_score < 0.3 THEN 1 ELSE 0 END) AS deprecated,
                        sum(CASE WHEN n.trust_score >= 0.3 AND n.trust_score < 0.5 THEN 1 ELSE 0 END) AS warning,
                        sum(CASE WHEN n.trust_score >= 0.5 THEN 1 ELSE 0 END) AS healthy
                """).single()

            if result:
                print(f"  Total nodes:  {result['total']}")
                print(f"  Avg score:    {result['avg_score']:.3f}" if result['avg_score'] else "  Avg score: N/A")
                print(f"  Min score:    {result['min_score']:.3f}" if result['min_score'] else "  Min score: N/A")
                print(f"  Max score:    {result['max_score']:.3f}" if result['max_score'] else "  Max score: N/A")
                print(f"  Healthy (>=0.5): {result['healthy']}")
                print(f"  Warning  (0.3-0.5): {result['warning']}")
                print(f"  Deprecated (<0.3): {result['deprecated']}")
        except Exception as e:
            print(f"  Report ERROR: {e}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wisdom Temporal Decay")
    parser.add_argument("--run",          action="store_true",
                        help="Run decay update on all nodes")
    parser.add_argument("--dry-run",      action="store_true",
                        help="Calculate decay without updating DB")
    parser.add_argument("--report",       action="store_true",
                        help="Show trust score distribution")
    parser.add_argument("--flag-outdated",action="store_true",
                        help="Flag outdated nodes as DEPRECATED")
    args = parser.parse_args()

    decay = WisdomDecay()

    if args.report:
        decay.report()
    elif args.dry_run:
        decay.run_decay(dry_run=True)
    elif args.run or args.flag_outdated:
        decay.run_decay(dry_run=False)
    else:
        decay.report()
        decay.run_decay(dry_run=True)

    decay.close()


if __name__ == "__main__":
    main()