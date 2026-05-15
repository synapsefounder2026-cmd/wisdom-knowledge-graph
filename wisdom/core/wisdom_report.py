"""
Wisdom Weekly Report Generator
Query Neo4j -> Tong hop insights tuan -> Markdown report

Usage:
    python wisdom_report.py              # Report tuan nay
    python wisdom_report.py --days 14    # Report 14 ngay gan nhat
    python wisdom_report.py --email      # Gui email (can SMTP config)

Setup cron (Git Bash / WSL):
    # Them vao wisdom_cron.py hoac Task Scheduler Windows
    # Moi thu 2 luc 07:00: python wisdom/core/wisdom_report.py
"""

import os
import sys
import re
import json
import requests
import argparse
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from neo4j import GraphDatabase

# ── Config (lay tu env, khong hardcode) ──────────────────────────────────────
OLLAMA_BASE   = "http://localhost:11434"
OLLAMA_MODEL  = "llama3.1:8b"
NEO4J_URI     = "bolt://localhost:7687"
NEO4J_USER    = "neo4j"
NEO4J_PASS    = "password123"
REPORT_DIR    = os.environ.get("WISDOM_REPORT_DIR", "reports")
SMTP_HOST     = os.environ.get("WISDOM_SMTP_HOST", "")
SMTP_PORT     = int(os.environ.get("WISDOM_SMTP_PORT", "587"))
SMTP_USER     = os.environ.get("WISDOM_SMTP_USER", "")
SMTP_PASS     = os.environ.get("WISDOM_SMTP_PASS", "")
REPORT_EMAIL  = os.environ.get("WISDOM_REPORT_EMAIL", "")

OPC_DOMAINS   = ["knowledge", "workflow", "monetization", "tools", "mindset"]


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


# ── Query Neo4j ───────────────────────────────────────────────────────────────

def query_recent_nodes(days: int = 7) -> list[dict]:
    """Lay tat ca nodes duoc ingest trong N ngay gan nhat."""
    since = (datetime.now() - timedelta(days=days)).isoformat()
    nodes = []
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:

            # Video nodes
            result = session.run("""
                MATCH (v:Video)
                WHERE v.ingested_at >= $since
                OPTIONAL MATCH (v)-[:HAS_CONCEPT]->(c:Concept)
                RETURN
                    v.title            AS title,
                    v.summary          AS summary,
                    v.url              AS url,
                    v.value_flywheel   AS flywheel,
                    v.opc_domain       AS opc_domain,
                    v.opc_applicability AS opc_applicability,
                    v.reasoning_chain  AS reasoning_chain,
                    v.action_steps     AS action_steps,
                    v.key_quotes       AS key_quotes,
                    v.ingested_at      AS ingested_at,
                    v.source_type      AS source_type,
                    collect(DISTINCT c.name) AS concepts
                ORDER BY v.ingested_at DESC
            """, since=since)

            for r in result:
                nodes.append({
                    "title":            r["title"] or "",
                    "summary":          r["summary"] or "",
                    "url":              r["url"] or "",
                    "flywheel":         r["flywheel"] or "learning",
                    "opc_domain":       r["opc_domain"] or [],
                    "opc_applicability": r["opc_applicability"] or "",
                    "reasoning_chain":  r["reasoning_chain"] or [],
                    "action_steps":     r["action_steps"] or [],
                    "key_quotes":       r["key_quotes"] or [],
                    "ingested_at":      r["ingested_at"] or "",
                    "source_type":      r["source_type"] or "VIDEO",
                    "concepts":         r["concepts"] or [],
                })

            # Document nodes
            result = session.run("""
                MATCH (d:Document)
                WHERE d.ingested_at >= $since
                OPTIONAL MATCH (d)-[:HAS_CONCEPT]->(c:Concept)
                RETURN
                    d.title          AS title,
                    d.summary        AS summary,
                    d.filename       AS url,
                    d.value_flywheel AS flywheel,
                    d.ingested_at    AS ingested_at,
                    d.source_type    AS source_type,
                    collect(DISTINCT c.name) AS concepts
                ORDER BY d.ingested_at DESC
            """, since=since)

            for r in result:
                nodes.append({
                    "title":            r["title"] or "",
                    "summary":          r["summary"] or "",
                    "url":              r["url"] or "",
                    "flywheel":         r["flywheel"] or "learning",
                    "opc_domain":       [],
                    "opc_applicability": "",
                    "reasoning_chain":  [],
                    "action_steps":     [],
                    "key_quotes":       [],
                    "ingested_at":      r["ingested_at"] or "",
                    "source_type":      r["source_type"] or "DOCUMENT",
                    "concepts":         r["concepts"] or [],
                })

        driver.close()
    except Exception as e:
        print(f"  Neo4j ERROR: {e}")

    return nodes


def query_all_concepts(days: int = 7) -> list[str]:
    """Lay toan bo unique concepts trong period."""
    since = (datetime.now() - timedelta(days=days)).isoformat()
    concepts = set()
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            result = session.run("""
                MATCH (n)-[:HAS_CONCEPT]->(c:Concept)
                WHERE n.ingested_at >= $since
                RETURN DISTINCT c.name AS concept
                ORDER BY concept
            """, since=since)
            for r in result:
                if r["concept"]:
                    concepts.add(r["concept"])
        driver.close()
    except Exception as e:
        print(f"  Neo4j concepts ERROR: {e}")
    return sorted(concepts)


def query_total_stats() -> dict:
    """Lay tong so nodes trong toan bo Knowledge Base."""
    stats = {"total_videos": 0, "total_docs": 0, "total_concepts": 0}
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            r = session.run("MATCH (v:Video) RETURN count(v) AS n").single()
            stats["total_videos"] = r["n"] if r else 0
            r = session.run("MATCH (d:Document) RETURN count(d) AS n").single()
            stats["total_docs"] = r["n"] if r else 0
            r = session.run("MATCH (c:Concept) RETURN count(c) AS n").single()
            stats["total_concepts"] = r["n"] if r else 0
        driver.close()
    except Exception as e:
        print(f"  Neo4j stats ERROR: {e}")
    return stats


# ── Ollama synthesis ──────────────────────────────────────────────────────────

def synthesize_with_ollama(nodes: list[dict], days: int) -> dict:
    """Dung Ollama tong hop insights tu cac nodes."""
    if not nodes:
        return {"top_insights": [], "action_items": [], "connections": [], "recommended_next": ""}

    print(f"  Synthesizing {len(nodes)} nodes with {OLLAMA_MODEL}...")

    # Chuan bi context ngan gon
    context_parts = []
    for n in nodes[:10]:  # Top 10 de khong qua context window
        part = f"Title: {n['title']}\nSummary: {n['summary'][:200]}"
        if n.get("opc_applicability"):
            part += f"\nOPC: {n['opc_applicability'][:150]}"
        if n.get("action_steps"):
            part += f"\nActions: {'; '.join(n['action_steps'][:3])}"
        context_parts.append(part)

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are Wisdom AI. Synthesize the knowledge ingested in the last {days} days for an OPC (One-Person Company) operator.
Return ONLY valid JSON, no markdown, no explanation.

Knowledge ingested:
{context}

Return this exact JSON:
{{
  "top_insights": ["3-5 most important insights for OPC, each 1-2 sentences"],
  "action_items": ["3-5 concrete actions the OPC owner should take this week"],
  "connections": ["2-3 interesting connections found between different knowledge pieces"],
  "recommended_next": "1 specific topic or skill to learn next based on knowledge gaps"
}}"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        raw = response.json().get("response", "{}").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"  Ollama synthesis ERROR: {e}")
        return {"top_insights": [], "action_items": [], "connections": [], "recommended_next": ""}


# ── Report builder ────────────────────────────────────────────────────────────

def group_by_domain(nodes: list[dict]) -> dict:
    """Group nodes theo opc_domain."""
    groups = {d: [] for d in OPC_DOMAINS}
    groups["other"] = []
    for node in nodes:
        domains = node.get("opc_domain") or []
        if isinstance(domains, str):
            domains = [domains]
        placed = False
        for d in domains:
            if d in groups:
                groups[d].append(node)
                placed = True
                break
        if not placed:
            groups["other"].append(node)
    return groups


def build_markdown_report(nodes: list[dict], synthesis: dict,
                           stats: dict, all_concepts: list[str],
                           days: int) -> str:
    """Build markdown report theo template co dinh 5 sections."""
    now = datetime.now()
    week_start = (now - timedelta(days=days)).strftime("%d/%m/%Y")
    week_end   = now.strftime("%d/%m/%Y")
    groups     = group_by_domain(nodes)

    domain_icons = {
        "knowledge": "KNOWLEDGE", "workflow": "WORKFLOW",
        "monetization": "MONETIZE", "tools": "TOOLS",
        "mindset": "MINDSET", "other": "OTHER"
    }

    lines = []
    lines.append(f"# Wisdom Weekly Report")
    lines.append(f"**Period:** {week_start} — {week_end}  ")
    lines.append(f"**Generated:** {now.strftime('%H:%M %d/%m/%Y')}  ")
    lines.append(f"**Knowledge Base:** {stats['total_videos']} videos | "
                 f"{stats['total_docs']} docs | {stats['total_concepts']} concepts total")
    lines.append("")
    lines.append("---")

    # Section 1: Stats tuan nay
    lines.append("")
    lines.append("## 1. This Week")
    lines.append("")
    lines.append(f"- **New nodes ingested:** {len(nodes)}")
    lines.append(f"- **New concepts:** {len(all_concepts)}")

    flywheel_count = {}
    for n in nodes:
        f = n.get("flywheel", "learning")
        flywheel_count[f] = flywheel_count.get(f, 0) + 1
    if flywheel_count:
        fw_str = " | ".join([f"{k}: {v}" for k, v in sorted(flywheel_count.items())])
        lines.append(f"- **By flywheel:** {fw_str}")

    if all_concepts:
        lines.append(f"- **New concepts:** {', '.join(all_concepts[:15])}"
                     + (" ..." if len(all_concepts) > 15 else ""))

    # Section 2: Top Insights (Ollama synthesis)
    lines.append("")
    lines.append("## 2. Top Insights")
    lines.append("")
    insights = synthesis.get("top_insights", [])
    if insights:
        for insight in insights:
            lines.append(f"- {strip_emoji(insight)}")
    else:
        lines.append("*Ingest more content de co insights.*")

    # Section 3: Action Items
    lines.append("")
    lines.append("## 3. Action Items — Tuan Nay")
    lines.append("")
    actions = synthesis.get("action_items", [])
    if actions:
        for i, action in enumerate(actions, 1):
            lines.append(f"{i}. {strip_emoji(action)}")
    else:
        lines.append("*Chua du data de generate action items.*")

    # Section 4: By Domain
    lines.append("")
    lines.append("## 4. Knowledge by OPC Domain")
    lines.append("")
    for domain, domain_nodes in groups.items():
        if not domain_nodes:
            continue
        label = domain_icons.get(domain, domain.upper())
        lines.append(f"### [{label}] {domain.title()} ({len(domain_nodes)} items)")
        for n in domain_nodes[:3]:
            title = strip_emoji(n.get("title", "Untitled"))
            summary = strip_emoji(n.get("summary", ""))[:120]
            source = n.get("source_type", "")
            lines.append(f"- **{title}** ({source})")
            if summary:
                lines.append(f"  {summary}...")
            opc = strip_emoji(n.get("opc_applicability", ""))
            if opc:
                lines.append(f"  *OPC: {opc[:100]}*")
        if len(domain_nodes) > 3:
            lines.append(f"  *...va {len(domain_nodes)-3} items nua*")
        lines.append("")

    # Section 5: Connections + Recommended
    lines.append("## 5. Connections Found")
    lines.append("")
    connections = synthesis.get("connections", [])
    if connections:
        for conn in connections:
            lines.append(f"- {strip_emoji(conn)}")
    else:
        lines.append("*Ingest them de Wisdom tim thay connections giua cac chu de.*")

    lines.append("")
    lines.append("## Recommended Next")
    lines.append("")
    rec = strip_emoji(synthesis.get("recommended_next", ""))
    if rec:
        lines.append(f"> {rec}")
    else:
        lines.append("> Tiep tuc ingest content theo chu de hien tai.")

    lines.append("")
    lines.append("---")
    lines.append(f"*Wisdom Report | {now.strftime('%d/%m/%Y')}*  ")
    lines.append(f"*Query inverse: `python wisdom_query.py --inverse \"<concept>\"`*")

    return "\n".join(lines)


# ── Email sender ──────────────────────────────────────────────────────────────

def send_email(subject: str, body: str, to_email: str):
    """Gui report qua email. Can SMTP config trong .env."""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, to_email]):
        print("  Email skip: SMTP chua config. Set WISDOM_SMTP_HOST, WISDOM_SMTP_USER, "
              "WISDOM_SMTP_PASS, WISDOM_REPORT_EMAIL trong .env")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_USER
        msg["To"]      = to_email
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        print(f"  Email sent to: {to_email}")
        return True
    except Exception as e:
        print(f"  Email ERROR: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def generate_report(days: int = 7, send_mail: bool = False) -> str:
    print(f"\n{'='*60}")
    print("  WISDOM WEEKLY REPORT")
    print(f"  Period: last {days} days")
    print(f"{'='*60}\n")

    # Tao thu muc report neu chua co
    Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)

    print("[1/4] Querying recent nodes...")
    nodes = query_recent_nodes(days)
    print(f"  Found: {len(nodes)} nodes")

    print("[2/4] Querying concepts + stats...")
    all_concepts = query_all_concepts(days)
    stats        = query_total_stats()
    print(f"  Concepts this period: {len(all_concepts)}")
    print(f"  Total KB: {stats['total_videos']} videos, "
          f"{stats['total_docs']} docs, {stats['total_concepts']} concepts")

    print("[3/4] Synthesizing with Ollama...")
    synthesis = synthesize_with_ollama(nodes, days)

    print("[4/4] Building report...")
    report_md = build_markdown_report(nodes, synthesis, stats, all_concepts, days)
    report_md += get_output_rate_section()

    # Save file
    filename  = f"wisdom_report_{datetime.now().strftime('%Y%m%d')}.md"
    filepath  = os.path.join(REPORT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"\n  Report saved: {filepath}")

    # Preview
    preview = report_md[:800]
    print(f"\n{'='*60}")
    print("PREVIEW:")
    print(preview)
    if len(report_md) > 800:
        print(f"... [{len(report_md)} chars total]")
    print(f"{'='*60}\n")

    # Email
    if send_mail:
        print("Sending email...")
        subject = f"Wisdom Report — {datetime.now().strftime('%d/%m/%Y')}"
        send_email(subject, report_md, REPORT_EMAIL)

    return filepath


def get_output_rate_section() -> str:
    """
    Tinh output rate va tao section cho Weekly Report.
    Creator > 30% | Curator 10-30% | Hoarder < 10%
    """
    try:
        from neo4j import GraphDatabase as _GD
        driver = _GD.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            r = s.run("""
                MATCH (n) WHERE n:Video OR n:Document
                RETURN
                    count(n) AS total,
                    sum(CASE WHEN n.epistemic_status = 'VERIFIED' THEN 1 ELSE 0 END) AS verified,
                    sum(CASE WHEN n.epistemic_status = 'PENDING' THEN 1 ELSE 0 END) AS pending,
                    sum(CASE WHEN coalesce(n.reuse_count,0) > 0 THEN 1 ELSE 0 END) AS used
            """).single()
        driver.close()
        total    = r["total"]    or 0
        verified = r["verified"] or 0
        pending  = r["pending"]  or 0
        used     = r["used"]     or 0
        rate     = round(used / verified, 2) if verified > 0 else 0.0
    except Exception:
        return ""

    if total < 5:
        status = "EARLY STAGE — Ingest them content truoc"
        icon   = "📌"
        advice = "Hay bat dau ingest it nhat 10 videos/docs."
    elif rate >= 0.3:
        status = "CREATOR MODE"
        icon   = "OK"
        advice = "Wisdom dang hoat dong dung muc dich. Tiep tuc output!"
    elif rate >= 0.1:
        status = "CURATOR WARNING"
        icon   = "!!"
        advice = (f"Ban co {pending} nodes PENDING chua verify. "
                  f"Chay: python wisdom_verify.py")
    else:
        status = "HOARDER ALERT"
        icon   = "!!"
        advice = (f"Ban co {total} nodes nhung chi dung {used}. "
                  f"Collector Fallacy dang xay ra. "
                  f"Hay verify va output ngay: python wisdom_verify.py")

    lines = [
        "",
        "## Output Health Check",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total nodes | {total} |",
        f"| Verified | {verified} |",
        f"| Pending | {pending} |",
        f"| Nodes used for output | {used} |",
        f"| **Output Rate** | **{rate*100:.0f}%** (target > 30%) |",
        f"| **Status** | **{icon} {status}** |",
        "",
        f"> {advice}",
        "",
        "**3 kieu user — Ban dang o dau?**",
        "- Creator (> 30%): Viet, day, ap dung, ra quyet dinh tu Wisdom",
        "- Curator (10-30%): Sap xep dep nhung chua produce output",
        "- Hoarder (< 10%):  Luu nhieu, dung 0 — nghia dia thong tin",
        "",
        f"*Verify nodes: `python wisdom/core/wisdom_verify.py`*",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wisdom Weekly Report Generator")
    parser.add_argument("--days",  type=int, default=7,
                        help="So ngay can report (default: 7)")
    parser.add_argument("--email", action="store_true",
                        help="Gui report qua email (can SMTP config)")
    args = parser.parse_args()

    generate_report(days=args.days, send_mail=args.email)
