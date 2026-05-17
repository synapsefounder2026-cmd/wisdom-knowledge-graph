import re

with open('wisdom_app.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Kiem tra da co endpoints chua
if '/api/health' in c:
    print("Endpoints da co san, khong can them")
else:
    endpoints = '''
@app.get("/api/health")
async def health():
    results = {"status": "ok", "neo4j": False, "qdrant": False, "ollama": False}
    try:
        from neo4j import GraphDatabase
        d = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        d.verify_connectivity()
        d.close()
        results["neo4j"] = True
    except: pass
    try:
        from qdrant_client import QdrantClient
        QdrantClient(host="localhost", port=6333).get_collections()
        results["qdrant"] = True
    except: pass
    try:
        import requests as _r
        _r.get("http://localhost:11434", timeout=2)
        results["ollama"] = True
    except: pass
    return results

@app.get("/api/inbox")
async def get_inbox(limit: int = 5, status: str = None):
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            result = s.run("""
                MATCH (n) WHERE n.title IS NOT NULL
                RETURN n.title AS title,
                       n.epistemic_status AS status,
                       n.source_type AS source_type,
                       n.ingested_at AS created_at
                ORDER BY n.ingested_at DESC LIMIT $limit
            """, limit=limit)
            items = [dict(r) for r in result]
        driver.close()
        return {"count": len(items), "items": items}
    except Exception as e:
        return {"count": 0, "items": [], "error": str(e)}

@app.get("/api/decay")
async def get_decay():
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            result = s.run("""
                MATCH (n) WHERE n.trust_score IS NOT NULL
                RETURN coalesce(n.source_type, 'general') AS domain,
                       count(n) AS count,
                       avg(n.trust_score) AS avg_trust
                ORDER BY avg_trust LIMIT 5
            """)
            domains = [dict(r) for r in result]
        driver.close()
        return {"domains": domains}
    except Exception as e:
        return {"domains": [], "error": str(e)}

@app.post("/api/search")
async def search_api(request: Request):
    body = await request.json()
    q = body.get("query", "").strip()
    if not q:
        return {"results": []}
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            result = s.run("""
                MATCH (n) WHERE n.title IS NOT NULL
                AND toLower(coalesce(n.title,'') + ' ' + coalesce(n.summary,''))
                CONTAINS toLower($q)
                RETURN n.title AS title,
                       n.epistemic_status AS status,
                       n.trust_score AS trust,
                       n.source_type AS domain
                LIMIT 5
            """, q=q)
            results = [dict(r) for r in result]
        driver.close()
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}

@app.get("/api/opc_score")
async def opc_score():
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            r = s.run("""
                MATCH (n) WHERE n:Video OR n:Document
                RETURN count(n) AS total,
                sum(CASE WHEN n.epistemic_status='VERIFIED' THEN 1 ELSE 0 END) AS verified,
                sum(CASE WHEN coalesce(n.reuse_count,0)>0 THEN 1 ELSE 0 END) AS used
            """).single()
        driver.close()
        total    = r["total"] or 0
        verified = r["verified"] or 0
        used     = r["used"] or 0
        score    = 0
        passed   = []
        failed   = []
        if verified >= 1:  score += 20; passed.append(f"{verified} nodes da VERIFIED")
        else: failed.append("Can it nhat 1 node VERIFIED")
        if total >= 5:     score += 20; passed.append(f"Co {total} nodes")
        else: failed.append(f"Can 5+ nodes (hien co {total})")
        if used >= 1:      score += 20; passed.append("Da co output tu knowledge")
        else: failed.append("Chua dung node nao de tao output")
        status = "EARLY" if score < 40 else "GROWING" if score < 60 else "ELIGIBLE_PASSPORT"
        return {"score": score, "status": status, "passed": passed, "failed": failed,
                "total": total, "verified": verified, "used": used}
    except Exception as e:
        return {"score": 0, "status": "ERROR", "failed": [str(e)]}

'''
    c = c.replace('if __name__', endpoints + '\nif __name__')
    with open('wisdom_app.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Done — endpoints added")
