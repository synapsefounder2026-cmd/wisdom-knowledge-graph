import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")

app = FastAPI(title="Wisdom Factory")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

@app.get("/", response_class=HTMLResponse)
async def index():
    return "<h1>Wisdom Factory</h1><p>API running!</p>"

@app.get("/api/stats")
async def get_stats():
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            r = s.run("MATCH (n) WHERE n.trust_score IS NOT NULL RETURN count(n) AS total").single()
            b = s.run("MATCH (n:Blueprint) RETURN count(n) AS c").single()
        driver.close()
        return {"total": r["total"], "blueprints": b["c"]}
    except Exception as e:
        return {"total": 0, "blueprints": 0, "error": str(e)}

@app.get("/api/nodes")
async def get_nodes():
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            result = s.run("""
                MATCH (n) WHERE n.title IS NOT NULL
                RETURN n.id AS id, n.title AS title,
                       n.epistemic_status AS status,
                       n.trust_score AS trust_score,
                       labels(n)[0] AS label
                ORDER BY n.ingested_at DESC LIMIT 20
            """)
            nodes = [dict(r) for r in result]
        driver.close()
        return {"nodes": nodes}
    except Exception as e:
        return {"nodes": [], "error": str(e)}

@app.post("/api/ask")
async def ask_brain(request: Request):
    body = await request.json()
    q = body.get("question", "").strip()
    if not q:
        return {"answer": "Please ask a question."}
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
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
            ans = str(len(nodes)) + " result(s) found:\n\n"
            for n in nodes:
                ans += "[" + str(n.get("status","")) + "] "
                ans += str(n.get("title","")) + "\n"
                ans += str(n.get("summary","")) + "\n\n"
        else:
            ans = "No knowledge found. Try ingesting content first."
        return {"answer": ans}
    except Exception as e:
        return {"answer": "Error: " + str(e)}

if __name__ == "__main__":
    print("Wisdom Factory at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)