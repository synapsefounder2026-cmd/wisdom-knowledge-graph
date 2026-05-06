"""
wisdom_validator.py
====================
Devil's Advocate Agent — Red-teaming Knowledge Nodes
Chuc nang:
- Kiem tra mau thuan giua cac knowledge nodes
- Tao EpistemicConflict node khi phat hien mau thuan
- Promote PENDING -> VERIFIED sau khi pass validation
- Async — khong block ingest pipeline

Usage:
    python wisdom/core/wisdom_validator.py --validate
    python wisdom/core/wisdom_validator.py --promote
    python wisdom/core/wisdom_validator.py --conflicts
"""

import os
import re
import sys
import json
import argparse
import requests
from datetime import datetime
from neo4j import GraphDatabase

# ── EP-001 Fix ────────────────────────────────────────────────────────────────
def strip_emoji(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text else ""
    p = re.compile(
        '[' + u'\U0001F600-\U0001F64F' + u'\U0001F300-\U0001F5FF'
        + u'\U0001F680-\U0001F6FF' + u'\U0001F1E0-\U0001F1FF'
        + u'\U00002600-\U000027BF' + u'\U0001F900-\U0001F9FF' + ']+',
        flags=re.UNICODE)
    return p.sub('', text).strip()

# ── Config ────────────────────────────────────────────────────────────────────
NEO4J_URI    = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER   = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS   = os.environ.get("NEO4J_PASS", "password123")
OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"

# Nguong de promote PENDING -> VERIFIED
RIPENESS_THRESHOLD   = 0.7
RED_TEAM_THRESHOLD   = 0.6
MIN_TRUST_SCORE      = 0.5


class WisdomValidator:

    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
            print("WisdomValidator: Connected to Neo4j")
        except Exception as e:
            print(f"WisdomValidator: Connection failed: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    # ── Devil's Advocate — Red Team mot node ─────────────────────────────────

    def red_team_node(self, node_id: str, title: str, content: str) -> dict:
        """
        Dung Ollama de phan bien node.
        Tra ve: {passed, score, critique, suggestions}
        """
        content = strip_emoji(content)
        title   = strip_emoji(title)

        prompt = f"""You are a Devil's Advocate AI. Your job is to find flaws, 
contradictions, and weaknesses in this knowledge claim.

Title: {title}
Content: {content[:1000]}

Analyze critically and return ONLY valid JSON:
{{
  "passed": true or false,
  "score": 0.0-1.0,
  "critique": "main weakness or contradiction found",
  "is_outdated": true or false,
  "needs_evidence": true or false,
  "suggestions": ["improvement1", "improvement2"]
}}

Be strict. Score above 0.6 means knowledge is solid enough to verify."""

        try:
            response = requests.post(
                f"{OLLAMA_BASE}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=120
            )
            raw = response.json().get("response", "{}")
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            print(f"  Red-team score: {result.get('score', 0):.2f} | Passed: {result.get('passed')}")
            return result
        except Exception as e:
            print(f"  Red-team ERROR: {e}")
            return {"passed": False, "score": 0.5, "critique": "Could not validate",
                    "is_outdated": False, "needs_evidence": True, "suggestions": []}

    # ── Check Conflict giua 2 nodes ───────────────────────────────────────────

    def check_conflict(self, node1: dict, node2: dict) -> dict:
        """
        Kiem tra 2 nodes co mau thuan nhau khong.
        """
        prompt = f"""Do these two knowledge claims contradict each other?

Claim 1: {node1.get('title', '')} — {node1.get('summary', '')[:300]}
Claim 2: {node2.get('title', '')} — {node2.get('summary', '')[:300]}

Return ONLY valid JSON:
{{
  "contradicts": true or false,
  "confidence": 0.0-1.0,
  "reason": "why they contradict or why they dont"
}}"""

        try:
            response = requests.post(
                f"{OLLAMA_BASE}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=120
            )
            raw = response.json().get("response", "{}")
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except Exception as e:
            print(f"  Conflict check ERROR: {e}")
            return {"contradicts": False, "confidence": 0.0, "reason": "Could not check"}

    # ── Tao EpistemicConflict node ────────────────────────────────────────────

    def create_conflict_node(self, node1_id: str, node2_id: str,
                              confidence: float, reason: str):
        """
        Tao CONTRADICTS relationship giua 2 nodes.
        Giu ca 2, gan nhan CONTESTED — khong bao gio xoa.
        """
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (a {id: $id1})
                    MATCH (b {id: $id2})
                    MERGE (a)-[r:CONTRADICTS]->(b)
                    SET r.confidence   = $confidence,
                        r.reason       = $reason,
                        r.detected_at  = $detected_at
                    SET a.epistemic_status = 'CONTESTED'
                    SET b.epistemic_status = 'CONTESTED'
                """, id1=node1_id, id2=node2_id,
                     confidence=confidence,
                     reason=strip_emoji(reason),
                     detected_at=datetime.now().isoformat())
            print(f"  Conflict created: {node1_id} <-> {node2_id} (confidence: {confidence:.2f})")
            print(f"  Both nodes marked [CONTESTED]")
        except Exception as e:
            print(f"  Create conflict ERROR: {e}")

    # ── Promote PENDING -> VERIFIED ───────────────────────────────────────────

    def promote_node(self, node_id: str, red_team_score: float):
        """
        Promote node tu PENDING sang VERIFIED sau khi pass red-team.
        """
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (n {id: $id})
                    WHERE n.epistemic_status = 'PENDING'
                    SET n.epistemic_status = 'VERIFIED',
                        n.red_team_score   = $score,
                        n.verified_at      = $verified_at,
                        n.ripeness_score   = $score
                """, id=node_id, score=red_team_score,
                     verified_at=datetime.now().isoformat())
            print(f"  PROMOTED: {node_id} -> VERIFIED (score: {red_team_score:.2f})")
        except Exception as e:
            print(f"  Promote ERROR: {e}")

    # ── Main: Validate all PENDING nodes ──────────────────────────────────────

    def validate_pending(self, limit: int = 10):
        """
        Lay tat ca PENDING nodes, chay red-team, promote hoac flag.
        Chay async — goi sau khi ingest xong.
        """
        print(f"\n{'='*60}")
        print(f"  DEVIL'S ADVOCATE — Validating PENDING nodes")
        print(f"{'='*60}\n")

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    WHERE n.epistemic_status = 'PENDING'
                    AND (n.title IS NOT NULL OR n.summary IS NOT NULL)
                    RETURN n.id AS id, n.title AS title,
                           n.summary AS summary, labels(n)[0] AS label
                    LIMIT $limit
                """, limit=limit)
                nodes = [dict(r) for r in result]
        except Exception as e:
            print(f"  Fetch ERROR: {e}")
            return

        if not nodes:
            print("  No PENDING nodes found.")
            return

        print(f"  Found {len(nodes)} PENDING nodes\n")
        promoted = 0
        flagged  = 0

        for node in nodes:
            node_id = node["id"]
            title   = node.get("title") or ""
            summary = node.get("summary") or ""
            label   = node.get("label", "Node")

            print(f"  [{label}] {title[:60]}...")
            result = self.red_team_node(node_id, title, summary)
            score  = result.get("score", 0.5)

            if result.get("passed") and score >= RED_TEAM_THRESHOLD:
                self.promote_node(node_id, score)
                promoted += 1
            else:
                print(f"  FLAGGED: {result.get('critique', 'No critique')[:100]}")
                flagged += 1

        print(f"\n  DONE: {promoted} promoted | {flagged} flagged")

    # ── Check conflicts giua recent nodes ─────────────────────────────────────

    def check_recent_conflicts(self, limit: int = 5):
        """
        So sanh cac VERIFIED nodes moi nhat voi nhau de tim mau thuan.
        """
        print(f"\n{'='*60}")
        print(f"  CONFLICT DETECTOR — Checking recent nodes")
        print(f"{'='*60}\n")

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    WHERE n.epistemic_status = 'VERIFIED'
                    AND n.title IS NOT NULL
                    RETURN n.id AS id, n.title AS title, n.summary AS summary
                    ORDER BY n.ingested_at DESC
                    LIMIT $limit
                """, limit=limit)
                nodes = [dict(r) for r in result]
        except Exception as e:
            print(f"  Fetch ERROR: {e}")
            return

        if len(nodes) < 2:
            print("  Not enough VERIFIED nodes to check conflicts.")
            return

        conflicts_found = 0
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                n1, n2 = nodes[i], nodes[j]
                print(f"  Checking: {n1['title'][:40]} vs {n2['title'][:40]}")
                result = self.check_conflict(n1, n2)

                if result.get("contradicts") and result.get("confidence", 0) > 0.7:
                    self.create_conflict_node(
                        n1["id"], n2["id"],
                        result["confidence"],
                        result["reason"]
                    )
                    conflicts_found += 1

        print(f"\n  DONE: {conflicts_found} conflict(s) found")

    # ── Show all conflicts ────────────────────────────────────────────────────

    def show_conflicts(self):
        """Hien thi tat ca CONTESTED nodes."""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (a)-[r:CONTRADICTS]->(b)
                    RETURN a.title AS title1, b.title AS title2,
                           r.confidence AS confidence, r.reason AS reason,
                           r.detected_at AS detected_at
                    ORDER BY r.detected_at DESC
                """)
                rows = [dict(r) for r in result]

            if not rows:
                print("  No conflicts found in database.")
                return

            print(f"\n  {'='*60}")
            print(f"  CONTESTED NODES ({len(rows)} conflicts)")
            print(f"  {'='*60}")
            for r in rows:
                print(f"\n  [{r['detected_at'][:10]}]")
                print(f"  Node 1: {r['title1']}")
                print(f"  Node 2: {r['title2']}")
                print(f"  Confidence: {r['confidence']:.2f}")
                print(f"  Reason: {r['reason'][:100]}")
        except Exception as e:
            print(f"  Show conflicts ERROR: {e}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wisdom Devil's Advocate Validator")
    parser.add_argument("--validate",  action="store_true",
                        help="Validate all PENDING nodes")
    parser.add_argument("--promote",   action="store_true",
                        help="Promote PENDING -> VERIFIED")
    parser.add_argument("--conflicts", action="store_true",
                        help="Show all CONTESTED nodes")
    parser.add_argument("--limit",     type=int, default=10,
                        help="Max nodes to process (default: 10)")
    args = parser.parse_args()

    validator = WisdomValidator()

    if args.conflicts:
        validator.show_conflicts()
    elif args.promote:
        validator.validate_pending(args.limit)
    elif args.validate:
        validator.validate_pending(args.limit)
        validator.check_recent_conflicts(args.limit)
    else:
        # Default: validate + check conflicts
        validator.validate_pending(args.limit)
        validator.check_recent_conflicts(args.limit)

    validator.close()


if __name__ == "__main__":
    main()