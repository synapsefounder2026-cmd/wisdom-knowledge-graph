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

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wisdom — OPC Knowledge OS</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,400&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0a0a0f;
  --surface: #111118;
  --surface2: #1a1a24;
  --border: #2a2a3a;
  --accent: #7c6af7;
  --accent2: #4ecca3;
  --accent3: #f7a94b;
  --text: #e8e8f0;
  --text2: #8888aa;
  --danger: #f74b6a;
  --creator: #4ecca3;
  --curator: #f7a94b;
  --hoarder: #f74b6a;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Syne', sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
}
/* Background grid */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(124,106,247,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(124,106,247,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* Header */
header {
  position: relative;
  z-index: 10;
  padding: 1.5rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  background: rgba(10,10,15,0.8);
  backdrop-filter: blur(12px);
}
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo-mark {
  width: 36px; height: 36px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 800;
  color: white;
}
.logo-text { font-size: 1.2rem; font-weight: 700; letter-spacing: -0.02em; }
.logo-sub { font-size: 0.7rem; color: var(--text2); font-family: 'DM Mono', monospace; }
.status-dot {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.75rem; color: var(--text2); font-family: 'DM Mono', monospace;
}
.dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent2);
  box-shadow: 0 0 8px var(--accent2);
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* Layout */
main {
  position: relative; z-index: 1;
  max-width: 1200px; margin: 0 auto;
  padding: 2rem;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: auto auto auto;
  gap: 1rem;
}

/* Cards */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s;
}
.card:hover { border-color: var(--accent); }
.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: 0;
  transition: opacity 0.2s;
}
.card:hover::before { opacity: 1; }

.card-label {
  font-size: 0.65rem; font-weight: 600;
  color: var(--text2);
  text-transform: uppercase; letter-spacing: 0.1em;
  font-family: 'DM Mono', monospace;
  margin-bottom: 0.75rem;
}
.card-value {
  font-size: 2.5rem; font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  background: linear-gradient(135deg, var(--text), var(--text2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.card-sub { font-size: 0.75rem; color: var(--text2); margin-top: 0.5rem; }

/* Status card */
.status-card {
  grid-column: span 3;
  display: flex; align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.output-rate-bar {
  flex: 1;
  height: 6px;
  background: var(--surface2);
  border-radius: 3px;
  overflow: hidden;
}
.output-rate-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 1s ease;
}
.status-badge {
  padding: 4px 12px;
  border-radius: 100px;
  font-size: 0.7rem; font-weight: 700;
  font-family: 'DM Mono', monospace;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.badge-creator { background: rgba(78,204,163,0.15); color: var(--creator); border: 1px solid rgba(78,204,163,0.3); }
.badge-curator { background: rgba(247,169,75,0.15); color: var(--curator); border: 1px solid rgba(247,169,75,0.3); }
.badge-hoarder { background: rgba(247,75,106,0.15); color: var(--hoarder); border: 1px solid rgba(247,75,106,0.3); }

/* Search card */
.search-card { grid-column: span 3; }
.search-row {
  display: flex; gap: 0.75rem; margin-bottom: 1rem;
}
.search-input {
  flex: 1;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: var(--text);
  font-family: 'DM Mono', monospace;
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s;
}
.search-input:focus { border-color: var(--accent); }
.search-input::placeholder { color: var(--text2); }
.btn {
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  border: none;
  font-family: 'Syne', sans-serif;
  font-size: 0.8rem; font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.02em;
}
.btn-primary {
  background: var(--accent);
  color: white;
}
.btn-primary:hover { background: #6a58e5; transform: translateY(-1px); }
.btn-secondary {
  background: var(--surface2);
  color: var(--accent2);
  border: 1px solid var(--border);
}
.btn-secondary:hover { border-color: var(--accent2); }

.answer-box {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  font-family: 'DM Mono', monospace;
  font-size: 0.8rem;
  line-height: 1.7;
  color: var(--text2);
  min-height: 80px;
  white-space: pre-wrap;
  display: none;
}
.answer-box.visible { display: block; }

/* Nodes list */
.nodes-card { grid-column: span 2; }
.node-item {
  display: flex; align-items: center;
  gap: 10px; padding: 0.6rem 0;
  border-bottom: 1px solid var(--border);
}
.node-item:last-child { border-bottom: none; }
.node-label {
  font-size: 0.6rem; padding: 2px 6px;
  border-radius: 4px;
  font-family: 'DM Mono', monospace;
  font-weight: 600; flex-shrink: 0;
}
.label-video { background: rgba(124,106,247,0.15); color: var(--accent); }
.label-doc   { background: rgba(78,204,163,0.15); color: var(--accent2); }
.label-other { background: rgba(255,255,255,0.05); color: var(--text2); }
.node-title { font-size: 0.82rem; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-status {
  font-size: 0.6rem; font-family: 'DM Mono', monospace;
  padding: 2px 6px; border-radius: 4px; flex-shrink: 0;
}
.status-verified { background: rgba(78,204,163,0.1); color: var(--accent2); }
.status-pending  { background: rgba(255,255,255,0.05); color: var(--text2); }

/* Ingest card */
.ingest-card {
  grid-column: span 1;
  display: flex; flex-direction: column; gap: 0.75rem;
}
.ingest-input {
  width: 100%;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem;
  color: var(--text);
  font-family: 'DM Mono', monospace;
  font-size: 0.75rem;
  outline: none;
  resize: none;
  height: 80px;
  transition: border-color 0.2s;
}
.ingest-input:focus { border-color: var(--accent3); }
.ingest-status {
  font-size: 0.72rem; font-family: 'DM Mono', monospace;
  color: var(--text2); min-height: 20px;
}
.ingest-status.ok { color: var(--accent2); }
.ingest-status.err { color: var(--danger); }

/* Loading spinner */
.spinner {
  display: inline-block;
  width: 12px; height: 12px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  vertical-align: middle; margin-right: 6px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Footer */
footer {
  position: relative; z-index: 1;
  text-align: center; padding: 1.5rem;
  font-size: 0.7rem; color: var(--text2);
  font-family: 'DM Mono', monospace;
  border-top: 1px solid var(--border);
}

/* Responsive */
@media (max-width: 768px) {
  main { grid-template-columns: 1fr; }
  .status-card, .search-card, .nodes-card { grid-column: span 1; }
}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-mark">W</div>
    <div>
      <div class="logo-text">Wisdom</div>
      <div class="logo-sub">OPC Knowledge OS</div>
    </div>
  </div>
  <div class="status-dot">
    <div class="dot"></div>
    <span id="server-status">connecting...</span>
  </div>
</header>

<main>
  <!-- Stats row -->
  <div class="card">
    <div class="card-label">Total Nodes</div>
    <div class="card-value" id="stat-total">—</div>
    <div class="card-sub">Knowledge units</div>
  </div>
  <div class="card">
    <div class="card-label">Verified</div>
    <div class="card-value" id="stat-verified">—</div>
    <div class="card-sub">Creator-confirmed</div>
  </div>
  <div class="card">
    <div class="card-label">Blueprints</div>
    <div class="card-value" id="stat-blueprints">—</div>
    <div class="card-sub">Packaged products</div>
  </div>

  <!-- Output Health -->
  <div class="card status-card">
    <div>
      <div class="card-label">Output Health</div>
      <span class="status-badge" id="output-badge">—</span>
    </div>
    <div style="flex:1; padding: 0 1.5rem;">
      <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
        <span style="font-size:0.7rem;color:var(--text2);font-family:'DM Mono',monospace;">Output Rate</span>
        <span style="font-size:0.7rem;color:var(--text);font-family:'DM Mono',monospace;" id="output-rate">0%</span>
      </div>
      <div class="output-rate-bar">
        <div class="output-rate-fill" id="rate-fill" style="width:0%;background:var(--creator)"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:4px;font-size:0.6rem;color:var(--text2);font-family:'DM Mono',monospace;">
        <span>Hoarder</span><span>Curator</span><span>Creator</span>
      </div>
    </div>
    <div style="font-size:0.7rem;color:var(--text2);font-family:'DM Mono',monospace;text-align:right;">
      Target: <span style="color:var(--creator);">&gt; 30%</span>
    </div>
  </div>

  <!-- Search -->
  <div class="card search-card">
    <div class="card-label">Ask Wisdom</div>
    <div class="search-row">
      <input class="search-input" id="search-input"
        placeholder="Hỏi bất cứ điều gì... / Ask anything..."
        onkeydown="if(event.key==='Enter')search()">
      <button class="btn btn-primary" onclick="search()">Search</button>
      <button class="btn btn-secondary" onclick="inverseSearch()">↩ Inverse</button>
    </div>
    <div class="answer-box" id="answer-box"></div>
  </div>

  <!-- Recent Nodes -->
  <div class="card nodes-card">
    <div class="card-label">Recent Knowledge</div>
    <div id="nodes-list">
      <div style="color:var(--text2);font-size:0.8rem;font-family:'DM Mono',monospace;">Loading...</div>
    </div>
  </div>

  <!-- Ingest -->
  <div class="card ingest-card">
    <div class="card-label">Quick Ingest</div>
    <textarea class="ingest-input" id="ingest-url"
      placeholder="YouTube URL&#10;https://youtube.com/watch?v=..."></textarea>
    <button class="btn btn-primary" onclick="ingestUrl()" style="width:100%">
      ▶ Ingest Video
    </button>
    <div class="ingest-status" id="ingest-status">
      Paste YouTube URL và click Ingest
    </div>
    <div style="border-top:1px solid var(--border);padding-top:0.75rem;margin-top:0.25rem;">
      <div class="card-label" style="margin-bottom:0.5rem;">Quick Actions</div>
      <div style="display:flex;flex-direction:column;gap:0.5rem;">
        <button class="btn btn-secondary" onclick="openVerify()" style="font-size:0.75rem;text-align:left;">
          ✓ Verify Nodes (Creator Mode)
        </button>
        <button class="btn btn-secondary" onclick="openReport()" style="font-size:0.75rem;text-align:left;">
          📋 Weekly Report
        </button>
        <button class="btn btn-secondary" onclick="openScore()" style="font-size:0.75rem;text-align:left;">
          🏆 OPC Score
        </button>
      </div>
    </div>
  </div>
</main>

<footer>
  Wisdom OPC Knowledge OS — v1.0 — Chạy 100% local · Neo4j + Qdrant + Ollama
</footer>

<script>
async function loadStats() {
  try {
    const r = await fetch('/api/stats');
    const d = await r.json();
    document.getElementById('stat-total').textContent = d.total ?? 0;
    document.getElementById('stat-blueprints').textContent = d.blueprints ?? 0;
    document.getElementById('server-status').textContent = 'online';

    // Output rate
    const verified = d.verified ?? 0;
    const used = d.nodes_used ?? 0;
    document.getElementById('stat-verified').textContent = verified;
    const rate = verified > 0 ? Math.round(used / verified * 100) : 0;
    document.getElementById('output-rate').textContent = rate + '%';
    document.getElementById('rate-fill').style.width = Math.min(rate, 100) + '%';

    let badgeClass = 'badge-hoarder', badgeText = '🔴 Hoarder';
    if (rate >= 30) { badgeClass = 'badge-creator'; badgeText = '✅ Creator'; }
    else if (rate >= 10) { badgeClass = 'badge-curator'; badgeText = '⚠ Curator'; }
    const badge = document.getElementById('output-badge');
    badge.className = 'status-badge ' + badgeClass;
    badge.textContent = badgeText;
  } catch(e) {
    document.getElementById('server-status').textContent = 'error';
  }
}

async function loadNodes() {
  try {
    const r = await fetch('/api/nodes');
    const d = await r.json();
    const list = document.getElementById('nodes-list');
    if (!d.nodes || d.nodes.length === 0) {
      list.innerHTML = '<div style="color:var(--text2);font-size:0.8rem;font-family:\'DM Mono\',monospace;">No nodes yet. Ingest content to start.</div>';
      return;
    }
    list.innerHTML = d.nodes.map(n => {
      const lbl = n.label === 'Video' ? 'label-video' : n.label === 'Document' ? 'label-doc' : 'label-other';
      const st  = n.status === 'VERIFIED' ? 'status-verified' : 'status-pending';
      return `<div class="node-item">
        <span class="node-label ${lbl}">${n.label||'?'}</span>
        <span class="node-title" title="${n.title||''}">${(n.title||'Untitled').substring(0,55)}</span>
        <span class="node-status ${st}">${n.status||'PENDING'}</span>
      </div>`;
    }).join('');
  } catch(e) {}
}

async function search() {
  const q = document.getElementById('search-input').value.trim();
  if (!q) return;
  const box = document.getElementById('answer-box');
  box.className = 'answer-box visible';
  box.innerHTML = '<span class="spinner"></span>Searching Wisdom...';
  try {
    const r = await fetch('/api/ask', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({question: q})
    });
    const d = await r.json();
    box.textContent = d.answer || 'No results found.';
  } catch(e) { box.textContent = 'Error: ' + e.message; }
}

async function inverseSearch() {
  const q = document.getElementById('search-input').value.trim();
  if (!q) { alert('Nhập concept cần tìm chuỗi suy luận'); return; }
  const box = document.getElementById('answer-box');
  box.className = 'answer-box visible';
  box.innerHTML = '<span class="spinner"></span>Inverse searching Dark Matter...';
  try {
    const r = await fetch('/api/inverse', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({concept: q})
    });
    const d = await r.json();
    box.textContent = d.answer || 'No reasoning chains found.';
  } catch(e) { box.textContent = 'Error connecting to Wisdom.'; }
}

function ingestUrl() {
  const url = document.getElementById('ingest-url').value.trim();
  if (!url) return;
  const st = document.getElementById('ingest-status');
  st.className = 'ingest-status';
  st.innerHTML = '<span class="spinner"></span>Ingesting... (3-8 min trên CPU)';
  fetch('/api/ingest', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({url})
  }).then(r => r.json()).then(d => {
    if (d.success) {
      st.className = 'ingest-status ok';
      st.textContent = '✓ Ingested: ' + (d.title||url).substring(0,40);
      loadStats(); loadNodes();
    } else {
      st.className = 'ingest-status err';
      st.textContent = '✗ ' + (d.error||'Failed');
    }
  }).catch(e => {
    st.className = 'ingest-status err';
    st.textContent = '✗ Server error: ' + e.message;
  });
}

function openVerify() {
  alert('Chạy trong terminal:\\npython wisdom/core/wisdom_verify.py');
}
function openReport() {
  alert('Chạy trong terminal:\\npython wisdom/core/wisdom_report.py');
}
function openScore() {
  alert('Chạy trong terminal:\\npython wisdom/core/wisdom_passport.py --score');
}

// Init
loadStats();
loadNodes();
setInterval(loadStats, 30000);
setInterval(loadNodes, 60000);
</script>
</body>
</html>'''

@app.get("/", response_class=HTMLResponse)
async def index():
    # Pre-load stats server-side de tranh CORS/fetch issues
    try:
        from neo4j import GraphDatabase as _GD
        _driver = _GD.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with _driver.session() as _s:
            _r = _s.run("""
                MATCH (n) WHERE n:Video OR n:Document
                RETURN count(n) AS total,
                  sum(CASE WHEN n.epistemic_status='VERIFIED' THEN 1 ELSE 0 END) AS verified,
                  sum(CASE WHEN coalesce(n.reuse_count,0)>0 THEN 1 ELSE 0 END) AS nodes_used
            """).single()
            _b = _s.run("MATCH (n:Blueprint) RETURN count(n) AS c").single()
        _driver.close()
        _total    = _r["total"] or 0
        _verified = _r["verified"] or 0
        _used     = _r["nodes_used"] or 0
        _bp       = _b["c"] or 0
        _rate     = round(_used / _verified * 100) if _verified > 0 else 0
    except:
        _total = _verified = _used = _bp = _rate = 0

    html = DASHBOARD_HTML
    html = html.replace('id="stat-total">—', f'id="stat-total">{_total}')
    html = html.replace('id="stat-verified">—', f'id="stat-verified">{_verified}')
    html = html.replace('id="stat-blueprints">—', f'id="stat-blueprints">{_bp}')
    html = html.replace('id="output-rate">0%', f'id="output-rate">{_rate}%')
    html = html.replace(
        'id="rate-fill" style="width:0%',
        f'id="rate-fill" style="width:{min(_rate,100)}%'
    )
    # Status badge
    if _rate >= 30:
        badge = 'badge-creator" textContent="Creator"'
        badge_html = 'class="status-badge badge-creator" id="output-badge">✅ Creator'
    elif _rate >= 10:
        badge_html = 'class="status-badge badge-curator" id="output-badge">⚠ Curator'
    else:
        badge_html = 'class="status-badge badge-hoarder" id="output-badge">🔴 Hoarder'
    html = html.replace('class="status-badge" id="output-badge">—', badge_html)
    html = html.replace(
        'connecting...',
        f'online · {_total} nodes'
    )
    return html

@app.get("/api/stats")
async def get_stats():
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            r = s.run("""
                MATCH (n) WHERE n:Video OR n:Document
                RETURN
                  count(n) AS total,
                  sum(CASE WHEN n.epistemic_status='VERIFIED' THEN 1 ELSE 0 END) AS verified,
                  sum(CASE WHEN coalesce(n.reuse_count,0)>0 THEN 1 ELSE 0 END) AS nodes_used
            """).single()
            b = s.run("MATCH (n:Blueprint) RETURN count(n) AS c").single()
        driver.close()
        return {
            "total": r["total"] or 0, "total_nodes": r["total"] or 0,
            "verified": r["verified"] or 0,
            "nodes_used": r["nodes_used"] or 0,
            "blueprints": b["c"] or 0
        }
    except Exception as e:
        return {"total":0,"total_nodes":0,"verified":0,"nodes_used":0,"blueprints":0,"error":str(e)}

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
        return {"nodes":[],"error":str(e)}

@app.post("/api/ask")
async def ask_brain(request: Request):
    body = await request.json()
    q = body.get("question","").strip()
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
                       n.epistemic_status AS status,
                       n.opc_applicability AS opc LIMIT 5
            """, q=q)
            nodes = [dict(r) for r in result]
        driver.close()
        if nodes:
            ans = f"{len(nodes)} result(s) found:\n\n"
            for n in nodes:
                ans += f"[{n.get('status','')}] {n.get('title','')}\n"
                if n.get('summary'): ans += f"{n['summary'][:200]}\n"
                if n.get('opc'):     ans += f"OPC: {n['opc'][:150]}\n"
                ans += "\n"
        else:
            ans = "No knowledge found for that query.\nTry ingesting related content first."
        return {"answer": ans}
    except Exception as e:
        return {"answer": f"Error: {e}"}

@app.post("/api/inverse")
async def inverse_search(request: Request):
    body = await request.json()
    concept = body.get("concept","").strip()
    if not concept:
        return {"answer": "Please enter a concept."}
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        chains = []
        with driver.session() as s:
            result = s.run("""
                MATCH (target)
                WHERE toLower(coalesce(target.title,target.name,''))
                      CONTAINS toLower($concept)
                MATCH path = (ancestor)-[:DERIVED_FROM|DISTILLED_TO|HAS_CONCEPT|
                              REFERRED_BY|COMPILED_INTO*1..4]->(target)
                WHERE ancestor <> target
                RETURN [node in nodes(path)|coalesce(node.title,node.name,'')] as chain,
                       [rel in relationships(path)|type(rel)] as rels,
                       length(path) as depth
                ORDER BY depth LIMIT 6
            """, concept=concept)
            for r in result:
                chains.append({"chain": r["chain"], "rels": r["rels"]})
        driver.close()
        if not chains:
            return {"answer": f"No reasoning chains found for '{concept}'.\nIngest more related content."}
        ans = f"Reasoning chains → '{concept}':\n\n"
        for i, c in enumerate(chains, 1):
            steps = " → ".join([s for s in c["chain"] if s])
            ans += f"{i}. {steps}\n   [{' / '.join(c['rels'])}]\n\n"
        return {"answer": ans}
    except Exception as e:
        return {"answer": f"Neo4j error: {e}"}

@app.post("/api/ingest")
async def ingest_url(request: Request):
    body = await request.json()
    url = body.get("url","").strip()
    if not url:
        return {"success": False, "error": "No URL provided"}
    try:
        import subprocess, sys
        script = os.path.join(os.path.dirname(__file__),
                              "wisdom", "core", "wisdom_ingest.py")
        result = subprocess.run(
            [sys.executable, script, url],
            capture_output=True, text=True, timeout=600, encoding="utf-8"
        )
        if result.returncode == 0:
            return {"success": True, "title": url, "output": result.stdout[-300:]}
        return {"success": False, "error": result.stderr[-200:]}
    except Exception as e:
        return {"success": False, "error": str(e)}


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



@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_v4():
    with open("wisdom_dashboard_v4.html", encoding="utf-8") as f:
        return f.read()
if __name__ == "__main__":
    print("Wisdom Factory at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
