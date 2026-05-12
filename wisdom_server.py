"""
wisdom_server.py
=================
FastAPI server cho Wisdom Dashboard v3.
Endpoints:
  GET  /                  — HTML index
  GET  /api/health        — Status check
  GET  /api/stats         — Node counts
  GET  /api/nodes         — Recent nodes (legacy)
  GET  /api/inbox         — Recent INBOX + RAW nodes
  GET  /api/decay         — Decay stats
  POST /api/ask           — Simple keyword search (legacy)
  POST /api/search        — Search nodes by query
  POST /api/ingest        — Trigger URL ingest
  POST /api/upload        — Upload file

Usage:
    python wisdom_server.py
    uvicorn wisdom_server:app --reload --port 8000
"""

import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ── Config ────────────────────────────────────────────────────────────────────
NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")

# Path den dashboard HTML
DASHBOARD_PATH = Path(__file__).parent / "wisdom_dashboard_v3.html"
if not DASHBOARD_PATH.exists():
    DASHBOARD_PATH = Path("wisdom_dashboard_v3.html")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Wisdom Factory", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB helper ─────────────────────────────────────────────────────────────────
def get_driver():
    from neo4j import GraphDatabase
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve dashboard HTML."""
    if DASHBOARD_PATH.exists():
        with open(DASHBOARD_PATH, encoding="utf-8") as f:
            return f.read()
    return "<h1>Wisdom Factory</h1><p>Dashboard not found. Place wisdom_dashboard_v3.html in root.</p>"


@app.get("/api/health")
async def health():
    """Health check — dashboard dung de check server status."""
    try:
        driver = get_driver()
        with driver.session() as s:
            s.run("RETURN 1")
        driver.close()
        return {
            "status": "ok",
            "neo4j": "connected",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "neo4j": "disconnected", "error": str(e)},
        )


@app.get("/api/stats")
async def get_stats():
    """Node counts theo tung label."""
    try:
        driver = get_driver()
        with driver.session() as s:
            labels = ["Video", "Document", "SocialPost", "RawSource",
                      "Concept", "Rule", "Blueprint", "InboxItem"]
            counts = {}
            for label in labels:
                r = s.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()
                counts[label.lower()] = r["c"] if r else 0

            total = s.run(
                "MATCH (n) WHERE n.trust_score IS NOT NULL RETURN count(n) AS c"
            ).single()["c"]

            pending = s.run(
                "MATCH (n) WHERE n.epistemic_status = 'PENDING' RETURN count(n) AS c"
            ).single()["c"]

            verified = s.run(
                "MATCH (n) WHERE n.epistemic_status = 'VERIFIED' RETURN count(n) AS c"
            ).single()["c"]

        driver.close()
        trust_rate = round(verified * 100 / total, 1) if total > 0 else 0
        return {
            "total":       total,
            "total_nodes": total,
            "pending":     pending,
            "verified":    verified,
            "trust_rate":  trust_rate,
            "review_due":  pending,
            **counts,
        }
    except Exception as e:
        return {"total": 0, "pending": 0, "verified": 0, "error": str(e)}


@app.get("/api/nodes")
async def get_nodes():
    """20 nodes moi nhat (legacy endpoint)."""
    try:
        driver = get_driver()
        with driver.session() as s:
            result = s.run("""
                MATCH (n) WHERE n.title IS NOT NULL
                RETURN n.id AS id, n.title AS title,
                       n.epistemic_status AS status,
                       n.trust_score AS trust_score,
                       n.ingested_at AS ingested_at,
                       labels(n)[0] AS label
                ORDER BY n.ingested_at DESC LIMIT 20
            """)
            nodes = [dict(r) for r in result]
        driver.close()
        return {"nodes": nodes}
    except Exception as e:
        return {"nodes": [], "error": str(e)}


@app.get("/api/inbox")
async def get_inbox(limit: int = 8):
    """Recent nodes cho INBOX panel trong dashboard."""
    try:
        driver = get_driver()
        with driver.session() as s:
            result = s.run("""
                MATCH (n)
                WHERE n.ingested_at IS NOT NULL
                AND (n.title IS NOT NULL OR n.filename IS NOT NULL)
                RETURN
                    coalesce(n.id, '') AS id,
                    coalesce(n.title, n.filename, 'Untitled') AS title,
                    coalesce(n.summary, '') AS summary,
                    coalesce(n.epistemic_status, 'PENDING') AS status,
                    coalesce(n.trust_score, 0.8) AS trust_score,
                    coalesce(n.source_type, 'UNKNOWN') AS source_type,
                    coalesce(n.ingested_at, '') AS ingested_at,
                    labels(n)[0] AS label
                ORDER BY n.ingested_at DESC
                LIMIT $limit
            """, limit=limit)
            nodes = [dict(r) for r in result]
        driver.close()
        return {"nodes": nodes, "items": nodes, "count": len(nodes)}
    except Exception as e:
        return {"nodes": [], "count": 0, "error": str(e)}


@app.get("/api/decay")
async def get_decay():
    """Decay stats cho Decay Tracker panel."""
    try:
        driver = get_driver()
        with driver.session() as s:
            result = s.run("""
                MATCH (n)
                WHERE n.trust_score IS NOT NULL
                RETURN
                    count(n) AS total,
                    avg(n.trust_score) AS avg_score,
                    sum(CASE WHEN n.trust_score >= 0.5 THEN 1 ELSE 0 END) AS healthy,
                    sum(CASE WHEN n.trust_score >= 0.3 AND n.trust_score < 0.5 THEN 1 ELSE 0 END) AS warning,
                    sum(CASE WHEN n.trust_score < 0.3 THEN 1 ELSE 0 END) AS deprecated
            """).single()

            # 5 nodes sap het han nhat
            at_risk = s.run("""
                MATCH (n)
                WHERE n.trust_score IS NOT NULL
                AND n.epistemic_status <> 'DEPRECATED'
                AND (n.title IS NOT NULL OR n.filename IS NOT NULL)
                RETURN
                    coalesce(n.title, n.filename, 'Untitled') AS title,
                    n.trust_score AS trust_score,
                    coalesce(n.source_type, 'UNKNOWN') AS source_type
                ORDER BY n.trust_score ASC
                LIMIT 5
            """)
            at_risk_nodes = [dict(r) for r in at_risk]

        driver.close()
        return {
            "total":      result["total"] if result else 0,
            "avg_score":  round(result["avg_score"] or 0, 3) if result else 0,
            "healthy":    result["healthy"] if result else 0,
            "warning":    result["warning"] if result else 0,
            "deprecated": result["deprecated"] if result else 0,
            "at_risk":    at_risk_nodes,
        }
    except Exception as e:
        return {"total": 0, "healthy": 0, "warning": 0, "deprecated": 0, "error": str(e)}


@app.post("/api/search")
async def search_nodes(request: Request):
    """Search nodes theo query — dung cho Search panel."""
    try:
        body  = await request.json()
        query = body.get("query", "").strip()
        limit = int(body.get("limit", 5))

        if not query:
            return {"results": [], "count": 0}

        driver = get_driver()
        with driver.session() as s:
            result = s.run("""
                MATCH (n)
                WHERE n.title IS NOT NULL
                AND (
                    toLower(coalesce(n.title, ''))    CONTAINS toLower($q)
                    OR toLower(coalesce(n.summary, '')) CONTAINS toLower($q)
                )
                RETURN
                    coalesce(n.id, '') AS id,
                    coalesce(n.title, 'Untitled') AS title,
                    coalesce(n.summary, '') AS summary,
                    coalesce(n.epistemic_status, 'PENDING') AS status,
                    coalesce(n.trust_score, 0.8) AS trust_score,
                    coalesce(n.source_type, 'UNKNOWN') AS source_type,
                    labels(n)[0] AS label
                ORDER BY n.trust_score DESC
                LIMIT $limit
            """, q=query, limit=limit)
            results = [dict(r) for r in result]
        driver.close()
        return {"results": results, "count": len(results), "query": query}
    except Exception as e:
        return {"results": [], "count": 0, "error": str(e)}


@app.post("/api/ask")
async def ask_brain(request: Request):
    """Legacy endpoint — keyword search, tra ve text."""
    body = await request.json()
    q    = body.get("question", "").strip()
    if not q:
        return {"answer": "Please ask a question."}
    try:
        driver = get_driver()
        with driver.session() as s:
            result = s.run("""
                MATCH (n) WHERE n.title IS NOT NULL
                AND toLower(coalesce(n.title,'') + ' ' + coalesce(n.summary,''))
                CONTAINS toLower($q)
                RETURN n.title AS title, n.summary AS summary,
                       n.epistemic_status AS status LIMIT 5
            """, q=q)
            nodes = [dict(r) for r in result]
        driver.close()
        if nodes:
            ans = f"{len(nodes)} result(s):\n\n"
            for n in nodes:
                ans += f"[{n.get('status','')}] {n.get('title','')}\n"
                ans += f"{n.get('summary','')}\n\n"
        else:
            ans = "No knowledge found. Try ingesting content first."
        return {"answer": ans}
    except Exception as e:
        return {"answer": f"Error: {e}"}


@app.post("/api/ingest")
async def ingest_url(request: Request):
    """Trigger URL ingest — goi wisdom_ingest.py."""
    try:
        body        = await request.json()
        url         = body.get("url", "").strip()
        source_type = body.get("source_type", "VIDEO")

        if not url:
            return JSONResponse(status_code=400, content={"error": "url required"})

        # Import va chay ingest
        sys.path.insert(0, str(Path(__file__).parent / "wisdom" / "core"))
        from wisdom_ingest import ingest
        result = ingest(url)

        if result:
            return {
                "success":      True,
                "content_id":   result.get("content_id", ""),
                "neo4j_node_id": result.get("neo4j_node_id", ""),
                "title":        result.get("analysis", {}).get("title", ""),
            }
        return {"success": False, "error": "Ingest returned None — check transcript"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload file va ingest vao Wisdom."""
    import tempfile

    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No file provided"})

    try:
        # Luu file tam thoi
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Import va chay upload
        sys.path.insert(0, str(Path(__file__).parent / "wisdom" / "core"))
        from wisdom_upload import upload
        result = upload(tmp_path)

        # Xoa file tam
        os.unlink(tmp_path)

        if result:
            return {
                "success":       True,
                "file_id":       result.get("file_id", ""),
                "neo4j_node_id": result.get("neo4j_node_id", ""),
                "title":         result.get("analysis", {}).get("title", ""),
                "filename":      file.filename,
            }
        return {"success": False, "error": "Upload failed — check file format"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  WISDOM FACTORY SERVER")
    print("  Dashboard: http://localhost:8000")
    print("  API docs:  http://localhost:8000/docs")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
