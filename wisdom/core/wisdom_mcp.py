"""
Wisdom MCP Server
Ket noi Claude Desktop vao Wisdom Knowledge Base qua MCP protocol.
Claude doc wiki pages da bien soan — KHONG doc raw chunks.

Install (1 lan):
    pip install fastmcp --break-system-packages

Ket noi Claude Desktop:
    Them vao claude_desktop_config.json:
    {
      "mcpServers": {
        "wisdom": {
          "command": "python",
          "args": ["C:/Users/LENOVO/wisdom-knowledge-graph/wisdom/core/wisdom_mcp.py"],
          "env": {
            "WISDOM_WIKI_DIR": "C:/Users/LENOVO/wisdom-knowledge-graph/wiki",
            "NEO4J_URI": "bolt://localhost:7687",
            "QDRANT_HOST": "localhost"
          }
        }
      }
    }

File config tren Windows:
    %APPDATA%\Claude\claude_desktop_config.json

Usage trong Claude Desktop:
    "Tim kiem trong Wisdom ve OPC automation"
    "Doc wiki page ve value flywheel"
    "Wisdom co bao nhieu knowledge nodes?"
    "Inverse search: chuoi suy luan dan den trust la gi?"
"""

import os
import sys
import json
import requests

# Add wisdom/core vao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from fastmcp import FastMCP
except ImportError:
    print("fastmcp chua cai. Chay: pip install fastmcp --break-system-packages")
    sys.exit(1)

from wisdom_wiki import (
    search_wiki_pages, read_wiki_page,
    list_wiki_pages, get_wiki_stats
)

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
EMBED_MODEL  = os.environ.get("EMBED_MODEL", "nomic-embed-text")
NEO4J_URI    = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER   = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS   = os.environ.get("NEO4J_PASS", "password123")
QDRANT_HOST  = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT  = int(os.environ.get("QDRANT_PORT", "6333"))
COLLECTION   = os.environ.get("QDRANT_COLLECTION", "wisdom_knowledge")
VECTOR_SIZE  = 768

# ── MCP Server ────────────────────────────────────────────────────────────────
mcp = FastMCP(
    "Wisdom",
    instructions="""
Wisdom la Knowledge OS cho OPC (One-Person Company).
Khi duoc hoi ve bat ky chu de nao, hay search Wisdom truoc.
Wisdom luu tri thuc cua Sep duoi dang wiki pages da bien soan va Neo4j graph.
Luon uu tien knowledge tu Wisdom hon la tu training data cua minh.
"""
)


# ── Tool 1: Search wiki ───────────────────────────────────────────────────────
@mcp.tool()
def search_wisdom(query: str, max_results: int = 5) -> str:
    """
    Tim kiem trong Wisdom Knowledge Base.
    Su dung khi can tim thong tin, concept, insight da duoc luu vao Wisdom.
    Tra ve noi dung wiki pages lien quan — da duoc AI bien soan, khong phai raw data.
    
    Args:
        query: Tu khoa can tim (tieng Viet hoac tieng Anh)
        max_results: So ket qua toi da (default 5)
    """
    results = search_wiki_pages(query, max_results)

    if not results:
        # Fallback: Qdrant vector search
        try:
            embed_resp = requests.post(
                f"{OLLAMA_BASE}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": query},
                timeout=30,
            )
            embedding = embed_resp.json().get("embedding", [])
            if embedding:
                from qdrant_client import QdrantClient
                client  = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
                hits    = client.query_points(
                    collection_name=COLLECTION,
                    query=embedding,
                    limit=max_results,
                    with_payload=True,
                )
                if hits.points:
                    lines = [f"[Vector search results for '{query}']\n"]
                    for h in hits.points:
                        p = h.payload
                        lines.append(f"**{p.get('title', 'Untitled')}** (score: {h.score:.2f})")
                        lines.append(f"Summary: {p.get('summary', '')[:200]}")
                        if p.get("opc_applicability"):
                            lines.append(f"OPC: {p['opc_applicability'][:150]}")
                        lines.append("")
                    return "\n".join(lines)
        except Exception as e:
            pass
        return f"Khong tim thay ket qua nao cho '{query}'. Ingest them content lien quan."

    lines = [f"[Wisdom search results for '{query}']\n"]
    for r in results:
        lines.append(f"**{r['title']}** — `{r['filename']}`")
        lines.append(r["excerpt"][:300])
        lines.append("")

    return "\n".join(lines)


# ── Tool 2: Read wiki page ────────────────────────────────────────────────────
@mcp.tool()
def read_wisdom_page(page_name: str) -> str:
    """
    Doc noi dung day du cua mot wiki page trong Wisdom.
    Su dung sau khi da biet ten page tu search_wisdom.
    Tra ve toan bo wiki page da duoc bien soan co reasoning chains, action steps, wikilinks.
    
    Args:
        page_name: Ten page hoac slug (vi du: 'opc_automation', 'value_flywheel')
    """
    content = read_wiki_page(page_name)
    if "not found" in content.lower():
        # Thu tim gan dung
        pages   = list_wiki_pages()
        similar = [p for p in pages if page_name.lower() in p["title"].lower()]
        if similar:
            return f"Page '{page_name}' khong tim thay chinh xac.\nCo the y ban muon:\n" + \
                   "\n".join([f"- {p['title']} ({p['filename']})" for p in similar[:3]])
    return content


# ── Tool 3: Inverse search ────────────────────────────────────────────────────
@mcp.tool()
def inverse_search_wisdom(concept: str) -> str:
    """
    Tim chuoi suy luan dan den mot concept — Dark Matter search.
    Thay vi hoi 'X la gi?', tim 'Chuoi nao dan den X?'
    Su dung de hieu nguon goc va reasoning behind mot kien thuc.
    
    Args:
        concept: Concept can truy nguoc suy luan (vi du: 'trust', 'OPC', 'automation')
    """
    try:
        from neo4j import GraphDatabase
        driver  = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        chains  = []
        siblings = []

        with driver.session() as session:
            result = session.run("""
                MATCH (target)
                WHERE toLower(coalesce(target.title, target.name, ''))
                      CONTAINS toLower($concept)
                MATCH path = (ancestor)-[:DERIVED_FROM|DISTILLED_TO|HAS_CONCEPT|
                              REFERRED_BY|COMPILED_INTO*1..5]->(target)
                WHERE ancestor <> target
                RETURN
                    [node in nodes(path) |
                        coalesce(node.title, node.name, node.filename, '')] as chain,
                    [rel in relationships(path) | type(rel)] as rel_types,
                    length(path) as depth,
                    target.summary as target_summary
                ORDER BY depth LIMIT 8
            """, concept=concept)
            for r in result:
                chains.append({
                    "chain":          r["chain"],
                    "rel_types":      r["rel_types"],
                    "depth":          r["depth"],
                    "target_summary": r["target_summary"],
                })

            sib = session.run("""
                MATCH (c:Concept)
                WHERE toLower(c.name) CONTAINS toLower($concept)
                MATCH (source)-[:HAS_CONCEPT]->(c)
                MATCH (source)-[:HAS_CONCEPT]->(sibling:Concept)
                WHERE sibling <> c
                RETURN coalesce(source.title, source.name) as source_title,
                       collect(DISTINCT sibling.name)[..5] as related
                LIMIT 3
            """, concept=concept)
            for r in sib:
                siblings.append({"source": r["source_title"], "related": r["related"]})

        driver.close()

        if not chains and not siblings:
            return (f"Khong tim thay reasoning chain cho '{concept}'.\n"
                    f"Ingest them content lien quan hoac concept chua co edges trong graph.")

        lines = [f"[Wisdom Inverse Search — '{concept}']\n"]
        if chains:
            lines.append("**Reasoning chains dan den concept nay:**\n")
            for i, c in enumerate(chains, 1):
                steps = " → ".join([s for s in c["chain"] if s])
                lines.append(f"{i}. {steps}")
                lines.append(f"   Quan he: {' / '.join(c['rel_types'])}")
                if c["target_summary"]:
                    lines.append(f"   Summary: {c['target_summary'][:120]}")
                lines.append("")

        if siblings:
            lines.append("**Concepts lien quan (cung nguon):**\n")
            for s in siblings:
                related = ", ".join(s["related"])
                lines.append(f"- [{s['source']}]: {related}")

        return "\n".join(lines)

    except Exception as e:
        return f"Neo4j error: {e}\nDam bao Neo4j container dang chay: docker start wisdom-neo4j"


# ── Tool 4: List all pages ────────────────────────────────────────────────────
@mcp.tool()
def list_wisdom_pages() -> str:
    """
    Liet ke tat ca wiki pages trong Wisdom Knowledge Base.
    Su dung khi muon biet Wisdom hien co nhung gi.
    """
    pages = list_wiki_pages()
    stats = get_wiki_stats()

    if not pages:
        return "Wisdom wiki chua co trang nao. Ingest content truoc: python wisdom_ingest.py <url>"

    lines = [
        f"[Wisdom Wiki — {stats['total_pages']} pages]\n",
    ]
    for p in pages:
        lines.append(f"- **{p['title']}** ({p['modified']}) — `{p['filename']}`")

    return "\n".join(lines)


# ── Tool 5: Wisdom stats ──────────────────────────────────────────────────────
@mcp.tool()
def wisdom_stats() -> str:
    """
    Xem tong quan Wisdom Knowledge Base — so nodes, wiki pages, concepts.
    Su dung de biet knowledge base hien tai co bao nhieu content.
    """
    stats     = get_wiki_stats()
    neo4j_stats = {}

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            r = s.run("MATCH (v:Video) RETURN count(v) AS n").single()
            neo4j_stats["videos"] = r["n"] if r else 0
            r = s.run("MATCH (d:Document) RETURN count(d) AS n").single()
            neo4j_stats["documents"] = r["n"] if r else 0
            r = s.run("MATCH (c:Concept) RETURN count(c) AS n").single()
            neo4j_stats["concepts"] = r["n"] if r else 0
            r = s.run("MATCH (n) WHERE n.epistemic_status='VERIFIED' RETURN count(n) AS n").single()
            neo4j_stats["verified"] = r["n"] if r else 0
        driver.close()
    except Exception as e:
        neo4j_stats = {"error": str(e)}

    return f"""[Wisdom Knowledge Base Stats]

Wiki Pages:    {stats['total_pages']}
Neo4j Videos: {neo4j_stats.get('videos', 'N/A')}
Neo4j Docs:   {neo4j_stats.get('documents', 'N/A')}
Concepts:     {neo4j_stats.get('concepts', 'N/A')}
Verified:     {neo4j_stats.get('verified', 'N/A')}

Wiki Dir: {stats['wiki_dir']}
"""


# ── Tool 6: Quick ingest ──────────────────────────────────────────────────────
@mcp.tool()
def ingest_to_wisdom(url: str) -> str:
    """
    Ingest mot YouTube URL vao Wisdom truc tiep tu Claude Desktop.
    Su dung khi Sep muon luu nhanh mot video vao Knowledge Base.
    
    Args:
        url: YouTube URL can ingest
    """
    try:
        import subprocess
        script = os.path.join(os.path.dirname(__file__), "wisdom_ingest.py")
        if not os.path.exists(script):
            return f"wisdom_ingest.py khong tim thay tai: {script}"

        result = subprocess.run(
            [sys.executable, script, url],
            capture_output=True, text=True, timeout=300,
            encoding="utf-8",
        )
        if result.returncode == 0:
            return f"Ingest thanh cong!\n{result.stdout[-500:]}"
        else:
            return f"Ingest that bai:\n{result.stderr[-300:]}"
    except Exception as e:
        return f"Error: {e}"


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Wisdom MCP Server starting...")
    print(f"Wiki dir: {os.environ.get('WISDOM_WIKI_DIR', 'wiki')}")
    print("Tools: search_wisdom, read_wisdom_page, inverse_search_wisdom,")
    print("       list_wisdom_pages, wisdom_stats, ingest_to_wisdom")
    mcp.run()
