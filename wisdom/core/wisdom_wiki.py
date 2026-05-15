"""
Wisdom Wiki Writer
Bien analysis JSON thanh .md wiki pages co wikilinks — giong Arkon.
Claude doc wiki pages nay thay vi raw chunks → chat luong tot hon nhieu.

Usage:
    from wisdom_wiki import write_wiki_page, read_wiki_page, search_wiki_pages
    
    # Sau khi ingest:
    page_path = write_wiki_page(analysis, content_id, source_url)
    
    # Khi query:
    pages = search_wiki_pages("OPC automation")
"""

import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path

WIKI_DIR = os.environ.get("WISDOM_WIKI_DIR", "wiki")


def strip_emoji(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text else ""
    emoji_pattern = re.compile(
        "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF" u"\U0001F1E0-\U0001F1FF"
        u"\U00002600-\U000027BF" u"\U0001F900-\U0001F9FF" "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def slugify(text: str) -> str:
    """Chuyen text thanh slug an toan cho ten file."""
    text = strip_emoji(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:60].strip("_") or "untitled"


def concept_to_wikilink(concept: str) -> str:
    """Chuyen concept thanh [[wikilink]]."""
    slug = slugify(concept)
    return f"[[{slug}]]"


def write_wiki_page(analysis: dict, content_id: str,
                    source_url: str = "", source_type: str = "VIDEO") -> str:
    """
    Tao file .md wiki page tu analysis JSON.
    Format giong Arkon: co wikilinks, structured, Claude-readable.
    
    Returns: duong dan den file wiki da tao.
    """
    Path(WIKI_DIR).mkdir(parents=True, exist_ok=True)

    title    = strip_emoji(analysis.get("title", "Untitled"))
    slug     = slugify(title)
    filename = f"{slug}_{content_id[:8]}.md"
    filepath = os.path.join(WIKI_DIR, filename)

    # Concepts → wikilinks
    concepts     = [strip_emoji(c) for c in analysis.get("key_concepts", [])]
    wikilinks    = [concept_to_wikilink(c) for c in concepts]
    related      = [strip_emoji(c) for c in analysis.get("related_concepts", [])]
    related_wiki = [concept_to_wikilink(c) for c in related]

    # OPC domain tags
    opc_domains = analysis.get("opc_domain", [])
    if isinstance(opc_domains, str):
        opc_domains = [opc_domains]

    lines = []

    # --- Frontmatter (YAML-style, Claude doc duoc) ---
    lines += [
        "---",
        f"title: {title}",
        f"content_id: {content_id}",
        f"source_type: {source_type}",
        f"source_url: {source_url}",
        f"ingested_at: {datetime.now().isoformat()}",
        f"flywheel: {analysis.get('value_flywheel', 'learning')}",
        f"language: {analysis.get('language', 'en')}",
        f"epistemic_status: PENDING",
        f"opc_domain: {', '.join(opc_domains) if opc_domains else 'knowledge'}",
        "---",
        "",
    ]

    # --- Title ---
    lines += [f"# {title}", ""]

    # --- Summary ---
    summary = strip_emoji(analysis.get("summary", ""))
    if summary:
        lines += ["## Summary", "", summary, ""]

    # --- Key Concepts (wikilinks) ---
    if wikilinks:
        lines += ["## Key Concepts", ""]
        lines.append(" | ".join(wikilinks))
        lines.append("")

    # --- OPC Applicability (quan trong nhat cho OPC user) ---
    opc_app = strip_emoji(analysis.get("opc_applicability", ""))
    if opc_app:
        lines += [
            "## OPC Applicability",
            "",
            f"> {opc_app}",
            "",
        ]

    # --- Reasoning Chain (Dark Matter) ---
    chains = analysis.get("reasoning_chain", [])
    if chains:
        lines += ["## Reasoning Chain", ""]
        for i, chain in enumerate(chains, 1):
            lines.append(f"{i}. {strip_emoji(chain)}")
        lines.append("")

    # --- Action Steps ---
    steps = analysis.get("action_steps", [])
    if steps:
        lines += ["## Action Steps", ""]
        for step in steps:
            lines.append(f"- [ ] {strip_emoji(step)}")
        lines.append("")

    # --- Key Insights ---
    insights = analysis.get("insights", [])
    if insights:
        lines += ["## Insights", ""]
        for insight in insights:
            lines.append(f"- {strip_emoji(insight)}")
        lines.append("")

    # --- Key Quotes ---
    quotes = analysis.get("key_quotes", [])
    if quotes:
        lines += ["## Key Quotes", ""]
        for quote in quotes:
            lines.append(f'> "{strip_emoji(quote)}"')
        lines.append("")

    # --- Contradictions ---
    contradictions = analysis.get("contradictions", [])
    if contradictions:
        lines += ["## Contradictions / Debates", ""]
        for c in contradictions:
            lines.append(f"- {strip_emoji(c)}")
        lines.append("")

    # --- Related Concepts (wikilinks) ---
    if related_wiki:
        lines += ["## Related Concepts", ""]
        lines.append(" | ".join(related_wiki))
        lines.append("")

    # --- Tags ---
    tags = [strip_emoji(t) for t in analysis.get("tags", [])]
    if tags:
        tag_str = " ".join([f"#{t.replace(' ', '_')}" for t in tags])
        lines += ["## Tags", "", tag_str, ""]

    # --- Source ---
    lines += [
        "## Source",
        "",
        f"- **Type:** {source_type}",
        f"- **URL:** {source_url}" if source_url else "- **URL:** N/A",
        f"- **Content ID:** `{content_id}`",
        "",
        "---",
        f"*Wiki page generated by Wisdom | {datetime.now().strftime('%d/%m/%Y %H:%M')}*",
    ]

    content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Wiki: {filepath} ({len(content)} chars)")
    return filepath


def read_wiki_page(page_name: str) -> str:
    """
    Doc noi dung wiki page theo ten hoac slug.
    Dung trong MCP server: Claude goi khi can doc chi tiet.
    """
    wiki_path = Path(WIKI_DIR)
    if not wiki_path.exists():
        return f"Wiki directory not found: {WIKI_DIR}"

    # Tim file theo nhieu cach
    search_slug = slugify(page_name)
    for f in wiki_path.glob("*.md"):
        if search_slug in f.stem or page_name.lower() in f.stem.lower():
            with open(f, encoding="utf-8") as fp:
                return fp.read()

    return f"Wiki page not found: {page_name}"


def search_wiki_pages(query: str, max_results: int = 5) -> list[dict]:
    """
    Tim kiem wiki pages theo keyword.
    Dung trong MCP server: Claude goi khi can search.
    Returns list of {filename, title, excerpt, path}
    """
    wiki_path = Path(WIKI_DIR)
    if not wiki_path.exists():
        return []

    query_lower = query.lower()
    results = []

    for f in wiki_path.glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            if query_lower in content.lower():
                # Lay title tu dong dau tien co #
                title = f.stem
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                # Lay excerpt xung quanh query
                idx     = content.lower().find(query_lower)
                start   = max(0, idx - 100)
                excerpt = content[start:idx + 200].strip()

                results.append({
                    "filename": f.name,
                    "title":    title,
                    "excerpt":  excerpt,
                    "path":     str(f),
                    "score":    content.lower().count(query_lower),  # frequency score
                })
        except Exception:
            continue

    # Sort by frequency score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def list_wiki_pages() -> list[dict]:
    """Liet ke tat ca wiki pages. Dung trong MCP server."""
    wiki_path = Path(WIKI_DIR)
    if not wiki_path.exists():
        return []

    pages = []
    for f in sorted(wiki_path.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
            title   = f.stem
            for line in content.split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            pages.append({
                "filename": f.name,
                "title":    title,
                "size":     len(content),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"),
            })
        except Exception:
            continue
    return pages


def get_wiki_stats() -> dict:
    """Thong ke wiki. Dung trong MCP server."""
    wiki_path = Path(WIKI_DIR)
    if not wiki_path.exists():
        return {"total_pages": 0, "total_chars": 0, "wiki_dir": WIKI_DIR}

    pages      = list(wiki_path.glob("*.md"))
    total_chars = sum(f.stat().st_size for f in pages)
    return {
        "total_pages":  len(pages),
        "total_chars":  total_chars,
        "wiki_dir":     WIKI_DIR,
        "last_updated": max(
            (f.stat().st_mtime for f in pages), default=0
        ),
    }
