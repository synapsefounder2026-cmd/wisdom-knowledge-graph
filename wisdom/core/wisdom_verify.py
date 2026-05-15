"""
Wisdom Verification System — Anti Collector's Fallacy
Buoc user phai "viet lai bang loi cua minh" truoc khi node len VERIFIED.

Usage:
    python wisdom_verify.py                    # Xem tat ca PENDING nodes
    python wisdom_verify.py --verify <node_id> # Verify 1 node cu the
    python wisdom_verify.py --stats            # Xem output rate
"""

import os
import sys
import re
import argparse
from datetime import datetime
from neo4j import GraphDatabase

NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")

def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def strip_emoji(text):
    if not isinstance(text, str): return str(text) if text else ""
    return re.compile("[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF" u"\U0001F1E0-\U0001F1FF"
        u"\U00002600-\U000027BF" u"\U0001F900-\U0001F9FF" "]+",
        flags=re.UNICODE).sub("", text).strip()


# ── Query nodes ───────────────────────────────────────────────────────────────

def get_pending_nodes(limit: int = 10) -> list[dict]:
    """Lay danh sach nodes chua duoc verify."""
    nodes = []
    try:
        driver = get_driver()
        with driver.session() as s:
            result = s.run("""
                MATCH (n)
                WHERE n.epistemic_status = 'PENDING'
                  AND (n:Video OR n:Document)
                RETURN
                    elementId(n) AS node_id,
                    coalesce(n.title, n.filename, 'Untitled') AS title,
                    n.summary AS summary,
                    n.ingested_at AS ingested_at,
                    n.source_type AS source_type,
                    coalesce(n.url, n.path, '') AS source_url
                ORDER BY n.ingested_at DESC
                LIMIT $limit
            """, limit=limit)
            for r in result:
                nodes.append({
                    "node_id":    r["node_id"],
                    "title":      r["title"] or "Untitled",
                    "summary":    r["summary"] or "",
                    "ingested_at": r["ingested_at"] or "",
                    "source_type": r["source_type"] or "",
                    "source_url":  r["source_url"] or "",
                })
        driver.close()
    except Exception as e:
        print(f"  Neo4j ERROR: {e}")
    return nodes


def get_output_stats() -> dict:
    """Tinh output rate — metric cot loi chong Collector's Fallacy."""
    stats = {
        "total_nodes": 0, "verified_nodes": 0, "pending_nodes": 0,
        "nodes_used": 0, "output_rate": 0.0, "status": "EARLY",
    }
    try:
        driver = get_driver()
        with driver.session() as s:
            r = s.run("""
                MATCH (n) WHERE n:Video OR n:Document
                RETURN
                    count(n) AS total,
                    sum(CASE WHEN n.epistemic_status = 'VERIFIED' THEN 1 ELSE 0 END) AS verified,
                    sum(CASE WHEN n.epistemic_status = 'PENDING' THEN 1 ELSE 0 END) AS pending,
                    sum(CASE WHEN n.reuse_count > 0 THEN 1 ELSE 0 END) AS used
            """).single()
            if r:
                stats["total_nodes"]   = r["total"] or 0
                stats["verified_nodes"] = r["verified"] or 0
                stats["pending_nodes"] = r["pending"] or 0
                stats["nodes_used"]    = r["used"] or 0
                if stats["verified_nodes"] > 0:
                    stats["output_rate"] = round(
                        stats["nodes_used"] / stats["verified_nodes"], 2
                    )
        driver.close()

        rate = stats["output_rate"]
        if stats["total_nodes"] < 5:
            stats["status"] = "EARLY"
        elif rate >= 0.3:
            stats["status"] = "CREATOR"
        elif rate >= 0.1:
            stats["status"] = "CURATOR"
        else:
            stats["status"] = "HOARDER"

    except Exception as e:
        print(f"  Neo4j ERROR: {e}")
    return stats


# ── Verify node ───────────────────────────────────────────────────────────────

def verify_node_interactive(node: dict) -> bool:
    """
    Interactive verification: buoc user viet lai bang loi cua minh.
    Returns True neu verified thanh cong.
    """
    print(f"\n{'='*60}")
    print(f"  VERIFY NODE")
    print(f"  Title: {strip_emoji(node['title'])[:60]}")
    print(f"  Type:  {node['source_type']}")
    if node['summary']:
        print(f"\n  Summary: {strip_emoji(node['summary'])[:200]}...")
    print(f"{'='*60}")
    print()
    print("RULE: Viet lai bang loi CUA BAN — khong copy-paste.")
    print("Dieu nay chung to ban hieu, khong chi luu tru.")
    print("(Toi thieu 2 cau. Go xong bam Enter 2 lan.)")
    print()

    lines = []
    print("Insight cua ban: ")
    while True:
        try:
            line = input()
            if line == "" and lines:
                break
            if line:
                lines.append(line)
        except EOFError:
            break

    user_insight = " ".join(lines).strip()

    if len(user_insight) < 20:
        print("\n  Qua ngan. Can it nhat 20 ky tu. Node giu nguyen PENDING.")
        return False

    # Action output
    print("\nBan da dung insight nay de lam gi? (chon so)")
    print("  1. Chua dung (chi hieu thoi)")
    print("  2. Viet bai / content")
    print("  3. Ra quyet dinh kinh doanh")
    print("  4. Day lai cho nguoi khac")
    print("  5. Ap dung vao workflow / SOP")

    choice = input("Chon (1-5, Enter = 1): ").strip() or "1"
    action_map = {
        "1": (False, False),
        "2": (True,  False),
        "3": (False, True),
        "4": (True,  False),
        "5": (False, True),
    }
    content_drafted, decision_made = action_map.get(choice, (False, False))

    # Update Neo4j
    try:
        driver = get_driver()
        with driver.session() as s:
            s.run("""
                MATCH (n) WHERE elementId(n) = $node_id
                SET n.epistemic_status = 'VERIFIED',
                    n.user_insight      = $insight,
                    n.verified_at       = $verified_at,
                    n.content_drafted   = $content_drafted,
                    n.decision_made     = $decision_made,
                    n.reuse_count       = COALESCE(n.reuse_count, 0) +
                                         CASE WHEN $content_drafted OR $decision_made
                                              THEN 1 ELSE 0 END,
                    n.decay_lambda      = 0.001,
                    n.trust_score       = CASE WHEN $content_drafted OR $decision_made
                                              THEN 0.95 ELSE 0.85 END
            """,
                node_id        = node["node_id"],
                insight        = user_insight,
                verified_at    = datetime.now().isoformat(),
                content_drafted = content_drafted,
                decision_made  = decision_made,
            )
        driver.close()
        print(f"\n  NODE VERIFIED ✓")
        print(f"  Insight saved: {user_insight[:80]}...")
        if content_drafted:
            print(f"  content_drafted = True → reuse_count +1")
        if decision_made:
            print(f"  decision_made = True → reuse_count +1")
        return True
    except Exception as e:
        print(f"  Neo4j ERROR: {e}")
        return False


def record_output(node_id: str, output_type: str = "content"):
    """Ghi nhan khi user dung node de tao output (goi tu content/report pipeline)."""
    try:
        driver = get_driver()
        with driver.session() as s:
            s.run("""
                MATCH (n) WHERE elementId(n) = $node_id
                SET n.reuse_count  = COALESCE(n.reuse_count, 0) + 1,
                    n.last_used_at = $now,
                    n.trust_score  = CASE WHEN n.trust_score < 0.95
                                         THEN n.trust_score + 0.05
                                         ELSE 0.95 END,
                    n.decay_lambda = 0.001
            """, node_id=node_id, now=datetime.now().isoformat())
        driver.close()
    except Exception as e:
        print(f"  record_output ERROR: {e}")


# ── Print helpers ─────────────────────────────────────────────────────────────

def print_stats(stats: dict):
    status_icon = {
        "CREATOR": "✅ CREATOR MODE",
        "CURATOR": "⚠️  CURATOR WARNING",
        "HOARDER": "🔴 HOARDER ALERT",
        "EARLY":   "📌 EARLY STAGE",
    }
    print(f"\n{'='*60}")
    print(f"  WISDOM OUTPUT STATS")
    print(f"{'='*60}")
    print(f"  Status:         {status_icon.get(stats['status'], stats['status'])}")
    print(f"  Total nodes:    {stats['total_nodes']}")
    print(f"  Verified:       {stats['verified_nodes']}")
    print(f"  Pending:        {stats['pending_nodes']}")
    print(f"  Nodes used:     {stats['nodes_used']}")
    print(f"  Output rate:    {stats['output_rate']*100:.0f}%  (target: > 30%)")
    print()

    if stats["status"] == "HOARDER":
        print("  Ban co nhieu nodes nhung chua dung node nao.")
        print("  Hay verify 1 node va output ngay hom nay.")
    elif stats["status"] == "CURATOR":
        print("  Output rate thap. Chon 1 node va viet/quyet dinh/day lai.")
    elif stats["status"] == "CREATOR":
        print("  Wisdom dang hoat dong dung muc dich. Tiep tuc!")
    print(f"{'='*60}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wisdom Verification — Anti Collector's Fallacy")
    parser.add_argument("--stats",  action="store_true", help="Xem output rate stats")
    parser.add_argument("--verify", metavar="NODE_ID",   help="Verify node cu the theo ID")
    parser.add_argument("--limit",  type=int, default=5, help="So PENDING nodes hien thi")
    args = parser.parse_args()

    if args.stats:
        stats = get_output_stats()
        print_stats(stats)
        sys.exit(0)

    if args.verify:
        nodes = get_pending_nodes(limit=50)
        node  = next((n for n in nodes if args.verify in n["node_id"]), None)
        if not node:
            print(f"Khong tim thay node: {args.verify}")
            sys.exit(1)
        verify_node_interactive(node)
        sys.exit(0)

    # Default: hien thi pending nodes va cho verify
    stats = get_output_stats()
    print_stats(stats)

    nodes = get_pending_nodes(args.limit)
    if not nodes:
        print("Khong co PENDING nodes. Ingest them content!")
        sys.exit(0)

    print(f"PENDING nodes can verify ({len(nodes)}):\n")
    for i, n in enumerate(nodes, 1):
        title = strip_emoji(n["title"])[:55]
        date  = n["ingested_at"][:10] if n["ingested_at"] else "?"
        print(f"  {i}. [{date}] {title}")

    print("\nChon so de verify (Enter = skip): ", end="")
    choice = input().strip()

    if choice.isdigit() and 1 <= int(choice) <= len(nodes):
        node = nodes[int(choice) - 1]
        verify_node_interactive(node)
        # Hien thi stats sau khi verify
        stats = get_output_stats()
        print_stats(stats)
    else:
        print("Skip. Chay lai: python wisdom_verify.py")
