"""
wisdom_api.py — FastAPI Backend cho Wisdom Dashboard
Connect: Neo4j + Qdrant -> wisdom_dashboard_v3.html
Run: uvicorn wisdom_api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import math
from datetime import datetime

# ── NEO4J ──────────────────────────────────────────────────
try:
    from neo4j import GraphDatabase
    NEO4J_URI  = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASS = os.environ.get("NEO4J_PASS", "password")
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    print(f"✓ Neo4j connected: {NEO4J_URI}")
except Exception as e:
    neo4j_driver = None
    print(f"⚠ Neo4j not connected: {e}")

# ── QDRANT ─────────────────────────────────────────────────
try:
    from qdrant_client import QdrantClient
    QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print(f"✓ Qdrant connected: {QDRANT_HOST}:{QDRANT_PORT}")
except Exception as e:
    qdrant_client = None
    print(f"⚠ Qdrant not connected: {e}")

# ── OLLAMA ─────────────────────────────────────────────────
try:
    import ollama
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
    ollama_available = True
    print(f"✓ Ollama available: {OLLAMA_MODEL}")
except Exception as e:
    ollama_available = False
    print(f"⚠ Ollama not available: {e}")

# ── APP ────────────────────────────────────────────────────
app = FastAPI(title="Wisdom Factory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (dashboard)
if os.path.exists("wisdom_dashboard_v3.html"):
    @app.get("/")
    async def dashboard():
        return FileResponse("wisdom_dashboard_v3.html")

# ── HELPERS ────────────────────────────────────────────────
def neo4j_query(cypher: str, params: dict = None):
    if not neo4j_driver:
        return []
    try:
        with neo4j_driver.session() as session:
            result = session.run(cypher, params or {})
            return [dict(r) for r in result]
    except Exception as e:
        print(f"Neo4j error: {e}")
        return []

def calc_decay(trust_score: float, created_at: str, decay_lambda: float) -> float:
    try:
        created = datetime.fromisoformat(created_at)
        age_days = (datetime.now() - created).days
        return round(trust_score * math.exp(-decay_lambda * age_days), 4)
    except:
        return trust_score

# ── STATS ENDPOINT ─────────────────────────────────────────
@app.get("/api/stats")
async def get_stats():
    """Tra ve tong so node, verified, blueprints, review due"""
    try:
        # Total nodes
        total = neo4j_query("MATCH (n:KnowledgeNode) RETURN count(n) as count")
        total_count = total[0]["count"] if total else 0

        # Verified
        verified = neo4j_query(
            "MATCH (n:KnowledgeNode {epistemic_status: 'VERIFIED'}) RETURN count(n) as count"
        )
        verified_count = verified[0]["count"] if verified else 0

        # Blueprints
        blueprints = neo4j_query("MATCH (b:Blueprint) RETURN count(b) as count")
        blueprint_count = blueprints[0]["count"] if blueprints else 0

        # Review due (next_review <= today)
        today = datetime.now().date().isoformat()
        due = neo4j_query(
            "MATCH (n:KnowledgeNode) WHERE n.next_review <= $today RETURN count(n) as count",
            {"today": today}
        )
        due_count = due[0]["count"] if due else 0

        return {
            "total_nodes": total_count,
            "verified": verified_count,
            "blueprints": blueprint_count,
            "review_due": due_count,
            "trust_rate": round(verified_count / total_count * 100, 1) if total_count > 0 else 0
        }
    except Exception as e:
        return {"error": str(e), "total_nodes": 0, "verified": 0, "blueprints": 0, "review_due": 0}

# ── INBOX ENDPOINT ─────────────────────────────────────────
@app.get("/api/inbox")
async def get_inbox(limit: int = 10, status: str = None):
    """Lay danh sach nodes moi nhat trong INBOX"""
    cypher = """
    MATCH (n:KnowledgeNode)
    WHERE n.epistemic_status = 'PENDING'
    """ + (f"AND n.source_type = '{status}'" if status else "") + """
    RETURN n.id as id, n.title as title, n.source_url as url,
           n.epistemic_status as status, n.trust_score as trust,
           n.created_at as created_at, n.domain as domain
    ORDER BY n.created_at DESC
    LIMIT $limit
    """
    nodes = neo4j_query(cypher, {"limit": limit})
    return {"items": nodes, "count": len(nodes)}

# ── SEARCH ENDPOINT ────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    domain: str = None

@app.post("/api/search")
async def search(req: SearchRequest):
    """Search knowledge bằng semantic search qua Qdrant"""
    if not qdrant_client:
        # Fallback: text search trong Neo4j
        cypher = """
        MATCH (n:KnowledgeNode)
        WHERE toLower(n.title) CONTAINS toLower($query)
           OR toLower(n.content) CONTAINS toLower($query)
        RETURN n.id as id, n.title as title, n.trust_score as trust,
               n.epistemic_status as status, n.domain as domain,
               n.decay_lambda as decay_lambda, n.created_at as created_at
        ORDER BY n.trust_score DESC
        LIMIT $limit
        """
        results = neo4j_query(cypher, {"query": req.query, "limit": req.limit})
        return {"results": results, "method": "neo4j_text_search"}

    try:
        # Embed query voi Ollama
        if ollama_available:
            embed_response = ollama.embeddings(model=OLLAMA_MODEL, prompt=req.query)
            embedding = embed_response["embedding"]
        else:
            return {"results": [], "error": "Ollama not available for embedding"}

        # Search Qdrant
        search_results = qdrant_client.query_points(
            collection_name="wisdom_public",
            query=embedding,
            limit=req.limit,
            with_payload=True
        )

        results = []
        for r in search_results.points:
            results.append({
                "id": r.payload.get("node_id"),
                "title": r.payload.get("title"),
                "trust": r.payload.get("trust_score"),
                "status": r.payload.get("epistemic_status"),
                "domain": r.payload.get("domain"),
                "score": round(r.score, 4)
            })

        return {"results": results, "method": "semantic_search"}

    except Exception as e:
        return {"results": [], "error": str(e)}

# ── DECAY ENDPOINT ─────────────────────────────────────────
@app.get("/api/decay")
async def get_decay_stats():
    """Lay thong ke decay theo domain"""
    cypher = """
    MATCH (n:KnowledgeNode)
    WHERE n.epistemic_status IN ['VERIFIED', 'PENDING']
    RETURN n.domain as domain,
           avg(n.trust_score) as avg_trust,
           avg(n.decay_lambda) as avg_lambda,
           count(n) as count
    ORDER BY avg_trust ASC
    """
    rows = neo4j_query(cypher)
    return {"domains": rows}

# ── INGEST ENDPOINT ────────────────────────────────────────
class IngestRequest(BaseModel):
    url: str
    title: str = None
    content: str = None
    source_type: str = "COMMUNITY"
    domain: str = "GENERAL"

@app.post("/api/ingest")
async def ingest_url(req: IngestRequest):
    """Nap URL moi vao Wisdom INBOX"""
    try:
        # Import wisdom_ingest
        import sys
        sys.path.append("wisdom/core")
        from wisdom_ingest import ingest_url as do_ingest

        result = do_ingest(
            url=req.url,
            source_type=req.source_type,
            domain=req.domain
        )
        return {"status": "ok", "node_id": result.get("id"), "title": result.get("title")}
    except ImportError:
        # Fallback: tao node truc tiep trong Neo4j
        import uuid
        node_id = str(uuid.uuid4())
        cypher = """
        CREATE (n:KnowledgeNode {
            id: $id, title: $title, source_url: $url,
            epistemic_status: 'PENDING', trust_score: 0.6,
            decay_lambda: 0.01, valid_from: $today,
            source_type: $source_type, domain: $domain,
            created_at: $now, updated_at: $now
        }) RETURN n.id as id
        """
        result = neo4j_query(cypher, {
            "id": node_id,
            "title": req.title or req.url,
            "url": req.url,
            "today": datetime.now().date().isoformat(),
            "now": datetime.now().isoformat(),
            "source_type": req.source_type,
            "domain": req.domain
        })
        return {"status": "ok", "node_id": node_id, "method": "direct_neo4j"}

# ── CLIP ENDPOINT (Wisdom Lens) ────────────────────────────
class ClipRequest(BaseModel):
    url: str
    content: str
    title: str = None
    images: list = []
    metadata: dict = {}
    user_id: str = "default"

@app.post("/api/clip")
async def clip_content(req: ClipRequest):
    """Nhan du lieu tu Wisdom Lens Chrome Extension"""
    try:
        import uuid, hashlib
        node_id = str(uuid.uuid4())
        content_hash = hashlib.sha256(req.content.encode()).hexdigest()

        # Check dedup
        existing = neo4j_query(
            "MATCH (n:KnowledgeNode {content_hash: $hash}) RETURN n.id as id LIMIT 1",
            {"hash": content_hash}
        )
        if existing:
            return {
                "status": "duplicate",
                "existing_id": existing[0]["id"],
                "message": "Noi dung nay da co trong Wisdom"
            }

        # Tao node moi
        cypher = """
        CREATE (n:KnowledgeNode {
            id: $id, title: $title, content: $content,
            content_hash: $hash, source_url: $url,
            epistemic_status: 'PENDING', trust_score: 0.65,
            decay_lambda: 0.01, valid_from: $today,
            source_type: 'COMMUNITY', created_at: $now,
            updated_at: $now, review_cadence: 'weekly'
        }) RETURN n.id as id
        """
        neo4j_query(cypher, {
            "id": node_id,
            "title": req.title or req.url[:80],
            "content": req.content[:5000],
            "hash": content_hash,
            "url": req.url,
            "today": datetime.now().date().isoformat(),
            "now": datetime.now().isoformat()
        })

        return {
            "status": "ok",
            "node_id": node_id,
            "message": f"Da clip: {req.title or req.url[:50]}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── HEALTH CHECK ───────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "neo4j": neo4j_driver is not None,
        "qdrant": qdrant_client is not None,
        "ollama": ollama_available,
        "timestamp": datetime.now().isoformat()
    }

# ── RUN ────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)