"""
wisdom_app.py
==============
Wisdom Web UI — FastAPI + HTML
Chay: python wisdom_app.py
Truy cap: http://localhost:8000
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ── Add wisdom/core to path ───────────────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), 'wisdom', 'core'))

# ── Config ────────────────────────────────────────────────────────────────────
NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")

app = FastAPI(title="Wisdom Factory", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── HTML Template ─────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wisdom Factory</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #0a0a0f; color: #e0e0e0; min-height: 100vh; }

.header { background: linear-gradient(135deg, #1a1a2e, #16213e);
          padding: 20px 40px; border-bottom: 1px solid #2a2a4a;
          display: flex; align-items: center; justify-content: space-between; }
.logo { font-size: 24px; font-weight: 700; color: #7F77DD; }
.logo span { color: #fff; }
.stats { display: flex; gap: 20px; }
.stat { text-align: center; }
.stat-num { font-size: 20px; font-weight: 700; color: #7F77DD; }
.stat-label { font-size: 11px; color: #888; }

.main { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }

.search-box { background: #1a1a2e; border: 1px solid #2a2a4a;
              border-radius: 12px; padding: 20px; margin-bottom: 30px; }
.search-title { font-size: 14px; color: #7F77DD; margin-bottom: 12px;
                font-weight: 600; letter-spacing: 0.05em; }
.search-row { display: flex; gap: 10px; }
.search-input { flex: 1; padding: 12px 16px; background: #0a0a0f;
                border: 1px solid #2a2a4a; border-radius: 8px;
                color: #e0e0e0; font-size: 14px; outline: none; }
.search-input:focus { border-color: #7F77DD; }
.btn { padding: 12px 20px; border-radius: 8px; border: none;
       cursor: pointer; font-size: 13px; font-weight: 600; }
.btn-primary { background: #7F77DD; color: #fff; }
.btn-primary:hover { background: #6a63c4; }
.btn-secondary { background: #2a2a4a; color: #e0e0e0; }
.btn-secondary:hover { background: #3a3a5a; }

.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
        margin-bottom: 30px; }
.card { background: #1a1a2e; border: 1px solid #2a2a4a;
        border-radius: 12px; padding: 20px; }
.card-title { font-size: 13px; font-weight: 600; color: #7F77DD;
              margin-bottom: 16px; letter-spacing: 0.05em; }

.ingest-form { display: flex; flex-direction: column; gap: 10px; }
.ingest-input { padding: 10px 14px; background: #0a0a0f;
                border: 1px solid #2a2a4a; border-radius: 8px;
                color: #e0e0e0; font-size: 13px; outline: none; }
.ingest-input:focus { border-color: #7F77DD; }

.nodes-list { display: flex; flex-direction: column; gap: 8px;
              max-height: 300px; overflow-y: auto; }
.node-item { padding: 10px 14px; background: #0a0a0f;
             border: 1px solid #2a2a4a; border-radius: 8px;
             cursor: pointer; transition: border-color 0.2s; }
.node-item:hover { border-color: #7F77DD; }
.node-title { font-size: 13px; font-weight: 500; }
.node-meta { font-size: 11px; color: #888; margin-top: 4px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 20px;
         font-size: 10px; font-weight: 600; margin-right: 4px; }
.badge-pending { background: #2a2a1a; color: #f0a500; }
.badge-verified { background: #1a2a1a; color: #4caf50; }
.badge-contested { background: #2a1a1a; color: #f44336; }

.answer-box { background: #1a1a2e; border: 1px solid #7F77DD;
              border-radius: 12px; padding: 20px; margin-bottom: 20px;
              display: none; }
.answer-label { font-size: 11px; font-weight: 600; color: #7F77DD;
                margin-bottom: 10px; letter-spacing: 0.05em; }
.answer-text { font-size: 14px; line-height: 1.6; }

.status { padding: 10px 14px; border-radius: 8px; font-size: 13px;
          margin-top: 10px; display: none; }
.status-ok { background: #1a2a1a; color: #4caf50; border: 1px solid #2a4a2a; }
.status-err { background: #2a1a1a; color: #f44336; border: 1px solid #4a2a2a; }

.full-width { grid-column: 1 / -1; }
</style>
</head>
<body>

<div class="header">
  <div class="logo"><span>Wisdom</span> Factory</div>
  <div class="stats" id="stats">
    <div class="stat"><div class="stat-num" id="stat-nodes">-</div>
      <div class="stat-label">NODES</div></div>
    <div class="stat"><div class="stat-num" id="stat-verified">-</div>
      <div class="stat-label">VERIFIED</div></div>
    <div class="stat"><div class="stat-num" id="stat-pending">-</div>
      <div class="stat-label">PENDING</div></div>
    <div class="stat"><div class="stat-num" id="stat-blueprints">-</div>
      <div class="stat-label">BLUEPRINTS</div></div>
  </div>
</div>

<div class="main">

  <!-- Search / Ask -->
  <div class="search-box">
    <div class="search-title">ASK YOUR SECOND BRAIN</div>
    <div class="search-row">
      <input class="search-input" id="ask-input"
             placeholder="Ask anything... (Enter to search)"
             onkeydown="if(event.key==='Enter') askBrain()"/>
      <button class="btn btn-primary" onclick="askBrain()">Ask</button>
      <button class="btn btn-secondary" onclick="loadNodes()">Refresh</button>
    </div>
    <div class="answer-box" id="answer-box">
      <div class="answer-label">WISDOM ANSWER</div>
      <div class="answer-text" id="answer-text"></div>
    </div>
  </div>

  <div class="grid">

    <!-- Ingest URL -->
    <div class="card">
      <div class="card-title">INGEST URL</div>
      <div class="ingest-form">
        <input class="ingest-input" id="ingest-url"
               placeholder="YouTube / Facebook / TikTok URL..."/>
        <button class="btn btn-primary" onclick="ingestUrl()">
          Ingest Video
        </button>
        <div class="status" id="ingest-status"></div>
      </div>
    </div>

    <!-- Stats -->
    <div class="card">
      <div class="card-title">KNOWLEDGE STATS</div>
      <div id="stats-detail" style="font-size:13px; line-height:2;">
        Loading...
      </div>
    </div>

    <!-- Recent Nodes -->
    <div class="card full-width">
      <div class="card-title">RECENT KNOWLEDGE NODES</div>
      <div class="nodes-list" id="nodes-list">
        <div style="color:#888; font-size:13px;">Loading...</div>
      </div>
    </div>

  </div>
</div>

<script>
async function loadStats() {
  try {
    const r = await fetch('/api/stats');
    const d = await r.json();
    document.getElementById('stat-nodes').textContent = d.total || 0;
    document.getElementById('stat-verified').textContent = d.verified || 0;
    document.getElementById('stat-pending').textContent = d.pending || 0;
    document.getElementById('stat-blueprints').textContent = d.blueprints || 0;
    document.getElementById('stats-detail').innerHTML =
      `Total nodes: <b>${d.total}</b><br>
       Verified: <b style="color:#4caf50">${d.verified}</b><br>
       Pending: <b style="color:#f0a500">${d.pending}</b><br>
       Contested: <b style="color:#f44336">${d.contested}</b><br>
       Blueprints: <b style="color:#7F77DD">${d.blueprints}</b>`;
  } catch(e) {
    document.getElementById('stats-detail').textContent = 'Neo4j not connected';
  }
}

async function loadNodes() {
  try {
    const r = await fetch('/api/nodes');
    const d = await r.json();
    const list = document.getElementById('nodes-list');
    if (!d.nodes || d.nodes.length === 0) {
      list.innerHTML = '<div style="color:#888;font-size:13px;">No nodes yet. Ingest some content!</div>';
      return;
    }
    list.innerHTML = d.nodes.map(n => `
      <div class="node-item">
        <div class="node-title">${n.title || 'Untitled'}</div>
        <div class="node-meta">
          <span class="badge badge-${(n.status||'pending').toLowerCase()}">${n.status||'PENDING'}</span>
          <span>${n.label || 'Node'}</span> &bull;
          <span>score: ${n.trust_score || '-'}</span> &bull;
          <span>${(n.ingested_at||'').slice(0,10)}</span>
        </div>
      </div>
    `).join('');
  } catch(e) {
    document.getElementById('nodes-list').innerHTML =
      '<div style="color:#f44336;font-size:13px;">Error loading nodes</div>';
  }
}

async function askBrain() {
  const q = document.getElementById('ask-input').value.trim();
  if (!q) return;
  const box  = document.getElementById('answer-box');
  const text = document.getElementById('answer-text');
  box.style.display = 'block';
  text.textContent = 'Searching your knowledge base...';
  try {
    const r = await fetch('/api/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: q})
    });
    const d = await r.json();
    text.textContent = d.answer || 'No answer found.';
  } catch(e) {
    text.textContent = 'Error connecting to Wisdom API.';
  }
}

async function ingestUrl() {
  const url    = document.getElementById('ingest-url').value.trim();
  const status = document.getElementById('ingest-status');
  if (!url) return;
  status.style.display = 'block';
  status.className = 'status status-ok';
  status.textContent = 'Ingesting... (this may take a few minutes)';
  try {
    const r = await fetch('/api/ingest', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url: url})
    });
    const d = await r.json();
    if (d.status === 'ok') {
      status.textContent = 'Ingested successfully! ' + (d.message || '');
      loadStats(); loadNodes();
    } else {
      status.className = 'status status-err';
      status.textContent = 'Error: ' + (d.message || 'Unknown error');
    }
  } catch(e) {
    status.className = 'status status-err';
    status.textContent = 'Connection error.';
  }
}

// Init
loadStats();
loadNodes();
setInterval(loadStats, 30000);
</script>
</body>
</html>"""


# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.get("/api/stats")
async def get_stats():
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            r = session.run("""
                MATCH (n) WHERE n.trust_score IS NOT NULL
                RETURN
                    count(n) AS total,
                    sum(CASE WHEN n.epistemic_status='VERIFIED' THEN 1 ELSE 0 END) AS verified,
                    sum(CASE WHEN n.epistemic_status='PENDING' THEN 1 ELSE 0 END) AS pending,
                    sum(CASE WHEN n.epistemic_status='CONTESTED' THEN 1 ELSE 0 END) AS contested
            """).single()
            b = session.run("MATCH (n:Blueprint) RETURN count(n) AS c").single()
        driver.close()
        return {"total": r["total"], "verified": r["verified"],
                "pending": r["pending"], "contested": r["contested"],
                "blueprints": b["c"]}
    except Exception as e:
        return {"total": 0, "verified": 0, "pending": 0,
                "contested": 0, "blueprints": 0, "error": str(e)}


@app.get("/api/nodes")
async def get_nodes():
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            result = session.run("""
                MATCH (n) WHERE n.title IS NOT NULL
                RETURN n.id AS id, n.title AS title,
                       n.epistemic_status AS status,
                       n.trust_score AS trust_score,
                       n.ingested_at AS ingested_at,
                       labels(n)[0] AS label
                ORDER BY n.ingested_at DESC
                LIMIT 20
            """)
            nodes = [dict(r) for r in result]
        driver.close()
        return {"nodes": nodes}
    except Exception as e:
        return {"nodes": [], "error": str(e)}


@app.post("/api/ask")
async def ask_brain(request: Request):
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        return {"answer": "Please ask a question."}
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE n.title IS NOT NULL AND n.summary IS NOT NULL
                AND toLower(n.title + ' ' + n.summary) CONTAINS toLower($q)
                RETURN n.title AS title, n.summary AS summary,
                       n.epistemic_status AS status
                LIMIT 5
            """, q=question)
            nodes = [dict(r) for r in result]
        driver.close()

        if nodes:
            answer = f"Found {len(nodes)} relevant node(s):\n\n"
            for n in nodes:
                answer += f"[{n['status']}] {n['title']}\n{n['summary']}\n\n"
        else:
            answer = "No relevant knowledge found. Try ingesting more content first."
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}


@app.post("/api/ingest")
async def ingest_url(request: Request):
    body = await request.json()
    url = body.get("url", "").strip()
    if not url:
        return {"status": "error", "message": "No URL provided"}
    try:
        import subprocess
        BASH = "C:/Program Files/Git/bin/bash.exe"
        script = os.path.join(os.path.dirname(__file__),
                              "wisdom", "core", "wisdom_ingest.py")
        result = subprocess.run(
            [BASH, "-c", f"python '{script}' '{url}'"],
            capture_output=True, text=True,
            encoding="utf-8", timeout=300
        )
        if result.returncode == 0:
            return {"status": "ok", "message": f"Ingested: {url[:60]}"}
        else:
            return {"status": "error", "message": result.stderr[:200]}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Timeout — try again"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  WISDOM FACTORY — Web UI")
    print("  http://localhost:8000")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)