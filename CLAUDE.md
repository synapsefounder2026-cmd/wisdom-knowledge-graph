# CLAUDE.md — Wisdom Factory
> Last updated: 2026-05-07 | Read this FIRST every session.

---

## WHY
Wisdom = He dieu hanh OPC (One Person Company).
KHONG PHAI chatbot. LA amplifier cho tacit knowledge cua Sep.
Formula: 1 Founder + AI Labor Force + N Partners.
"Co the thue ngoai suy nghi. Khong the thue ngoai thau hieu."

---

## MAP — File Structure
```
wisdom-knowledge-graph/
├── CLAUDE.md              <- Doc truoc tien (file nay)
├── PENDING.md             <- Tasks + trang thai
├── backup_now.sh          <- Chay hang toi: bash backup_now.sh
├── wisdom_backup.py       <- Docker volume backup
├── wisdom_app.py          <- Entry point
├── wisdom_server.py       <- FastAPI server
├── wisdom/core/
│   ├── wisdom_ingest.py   <- Layer 1: Ingest web/text
│   ├── wisdom_upload.py   <- Layer 1: Upload files
│   ├── wisdom_fb_ingest.py<- Layer 1: FB (cho P-043 Wisdom Lens)
│   ├── wisdom_query.py    <- Layer 3: Search + Query
│   ├── wisdom_validator.py<- Layer 4: Council + Validation
│   ├── wisdom_decay.py    <- Temporal decay function
│   ├── wisdom_dedup.py    <- SHA-256 dedup
│   ├── wisdom_payment.py  <- Unified Ledger
│   └── wisdom_schema.py   <- Node schema
├── docs/
│   ├── WISDOM_ARCHITECTURE.md  <- Chi tiet kien truc
│   ├── WISDOM_VOICE.md         <- Output writing standard (P-029)
│   ├── wisdom_node_schema.md   <- Node properties (P-026)
│   └── CLAUDE_STRATEGY_HANDOVER.md
└── templates/
    ├── FORM_LIBRARY.md
    └── WISDOM_SKILL_TEMPLATE.md
```

---

## RULES — Bat buoc khi viet code

**[RULE-A]** Neo4j = SOURCE OF TRUTH. Qdrant = SEARCH INDEX.
Write Neo4j TRUOC -> lay node_id -> write Qdrant.

**[RULE-B]** Moi KnowledgeNode phai co du fields:
trust_score, decay_lambda, valid_from, valid_until,
epistemic_status, cultural_context, source_type
→ Xem chi tiet: docs/wisdom_node_schema.md

**[RULE-C]** Decay: trust_score(t) = base * exp(-lambda * age_days)

**[RULE-D]** Validation ASYNC — khong block ingest pipeline.
PENDING → DB ngay. Background job validate. Chi VERIFIED vao Global Pool.

**[RULE-E]** Tacit knowledge = explicit opt-in. Khong auto-push.

**[RULE-F]** Mau thuan → tao CONTRADICTS node. Khong bao gio xoa.

**[RULE-G]** Qdrant collections: wisdom_public | wisdom_private_{uid} | wisdom_shadow

**[RULE-H]** Obsidian bridge (P-025) chi lam SAU P-007 stable.

---

## WORKFLOW — Bat dau moi session

```
1. Doc CLAUDE.md nay (xong roi)
2. Doc PENDING.md — xem task uu tien
3. Hoi Sep: "Hom nay lam gi?"
4. Ship. Khong over-engineer.
```

---

## CHECKLIST TRUOC KHI VIET CODE

- [ ] strip_emoji() cho moi xu ly text
- [ ] encoding='utf-8' cho moi open()
- [ ] try/except cho moi DB call
- [ ] os.environ.get() — khong hardcode key
- [ ] Windows subprocess → dung Git Bash exe
- [ ] Write Neo4j TRUOC Qdrant (RULE-A)
- [ ] KnowledgeNode du fields (RULE-B)

---

## STACK
Python + Neo4j + Qdrant + Ollama (local) + FastAPI
Docker: wisdom-neo4j (port 7474/7687) + wisdom-qdrant (port 6333/6334)
OS: Windows 11, Git Bash terminal

## INFRASTRUCTURE
- Phase 1: Laptop (hien tai) + OneDrive backup
- Phase 2: Hetzner CX32 $14/thang (khi P-007 xong)
- Phase 3: Hybrid $50-80/thang (khi co 50+ users)

## PRIORITY (Hom nay)
P-007 Web UI → P-026 node_schema → P-029 WISDOM_VOICE
→ Xem PENDING.md de biet toan bo

---
## SOUL OF WISDOM — Triet ly Nen tang (P-040)

**Explicit knowledge (99%)** = AI xu ly duoc
**Tacit knowledge (1%)** = Moat that su cua Sep — khong AI nao co duoc

Explicit: Quy trinh, checklist, framework, data
Tacit:    Mui thi truong, giac kinh doanh, kinh nghiem song

**Nguyen tac Above the Algorithm** (Sangeet Paul Choudary):
- AI gioi o tang duoi (xu ly, phan tich, thuc thi)
- Con nguoi phai o tang tren (dinh huong, phan quyet, thau hieu)
- Wisdom = Amplifier cho tang tren — KHONG phai replacement

**3 dieu AI khong the thue ngoai:**
1. Thau hieu van hoa dia phuong (thi truong VN)
2. Tin tuong tu cong dong (Sep la nguoi — AI la tool)
3. Truc giac tu trai nghiem that (khong the copy)

**Ap dung trong Wisdom:**
- Moi output phai amplify judgment cua Sep, khong thay the
- Tacit knowledge chi push vao wisdom_private khi Sep opt-in (RULE-E)
- Persona 5 (The Intuition) = so hoa truc giac cua Sep — moat lon nhat

**Quote:** Co the thue ngoai suy nghi. Khong the thue ngoai thau hieu.

---

## AI CODING BEHAVIOR — Karpathy Guidelines (v2026-05-14)
> Source: github.com/forrestchang/andrej-karpathy-skills (127K stars)

### 1. Think Before Coding
- Neu ro assumption cu the. Neu khong chac, hoi.
- Neu co nhieu cach hieu, trinh bay het.
- Neu co gi khong ro, DUNG LAI. Hoi.

### 2. Simplicity First
- Khong them feature ngoai yeu cau.
- Khong abstraction cho single-use code.
- Neu viet 200 dong ma co the 50 dong, viet lai.

### 3. Surgical Changes
- Khong "improve" adjacent code ngoai scope.
- Match existing style du co the lam khac.
- Moi dong thay doi phai trace duoc ve request cua Sep.

### 4. Goal-Driven Execution
- "Fix the bug" -> "Viet test reproduce bug, roi lam pass"
- Multi-step: neu plan truoc, verify tung buoc.

---

## REPO INTELLIGENCE (2026-05-14)
| Repo | Stars | Action |
|---|---|---|
| forrestchang/andrej-karpathy-skills | 127K | Da tich hop section tren |
| mattpocock/skills | 66K | Them .claude/skills/ |
| rohitg00/agentmemory | Growing | Nghien cuu sau Gumroad |
| addyosmani/agent-skills | 30K | Phase 2 |
| NousResearch/hermes-agent | 148K | Hoc pattern Phase 2 |
| apernet/hysteria | - | Skip |
| tinyhumansai/openhuman | - | GPL3, skip |
| CloakHQ/cloakbrowser | - | Giu cho P-016 |

---

## INVERSE KNOWLEDGE SEARCH — Dark Matter Layer (v2026-05-14)
Chi them 1 function: query_inverse() trong wisdom_query.py
KHONG build: RDT, LCoT pipeline, multi-solver.
Usage: python wisdom_query.py --inverse "concept"
RULE-I: Luu ca ket luan lan chuan suy luan khi ingest.

---

## DOMAIN & IDENTITY (v2026-05-15)
Domain    : synapsenetwork.io (Namecheap, 1 year từ Jan 15 2026)
Owner     : Nguyen — 23B3 Le Quang Dinh, Ho Chi Minh City, VN
Account   : Tamnd
GitHub    : synapsefounder2026-cmd
Product   : Wisdom Factory — OPC Knowledge OS

URLs ke hoach:
  synapsenetwork.io          → Landing page chinh
  app.synapsenetwork.io      → Wisdom Dashboard
  api.synapsenetwork.io      → Wisdom API
  docs.synapsenetwork.io     → INSTALLATION + QUICKSTART

Dung cho Payoneer:
  Business name : Synapse Network
  Website URL   : https://synapsenetwork.io
  Business type : Individual / Freelancer

---

## BLUEPRINT FACTORY — Chien luoc san pham (v2026-05-16)
> Wisdom = Nha may tao blueprints. Moi 100 videos ingest = 1 blueprint ban duoc.
> Nguon: Antigravity analysis + 2 case studies + phan bien thuc te

### Dinh nghia Blueprint
Blueprint = Tri thuc duoc cau truc thanh san pham ban duoc
  - Khong chi la PDF — la LIVING DOCUMENT (wiki nodes trong Neo4j)
  - Tu dong update khi co thong tin moi (ARCHIVIST)
  - Evidence-based: phai co case studies thuc te
  - Validation Gate: Sep tu chay thu truoc khi publish

### 5 Nguon Tao Blueprints
1. YouTube channels (da co pipeline) → wisdom_whisper.py
2. GitHub awesome-* repos → wisdom_code_scout.py (P-010)
3. Newsletters/Substack → Playwright MCP crawl
4. Reddit (r/SideProject, r/EntrepreneurRideAlong) → Tavily search
5. IndieHackers interviews → 3000+ revenue-validated cases

### Pipeline Tu Dong
INPUT → ARCHIVIST (ingest + extract) → ANALYST (cluster + validate)
     → SCRIBE (write structure) → VALIDATION GATE (Sep review)
     → PUBLISH tren Wisdom Marketplace

### Blueprint Structure (bat buoc)
1. Overview & outcomes (ket qua cu the)
2. Prerequisites (can gi truoc)
3. Step-by-step workflow
4. Tools & stack (co links)
5. Common mistakes (tu Dark Matter analysis)
6. Real examples (co citations tu KB)
7. Estimated ROI / timeline (validated)

### Phan bien quan trong
- Legal Graph Blueprint: TRANH thi truong VN (data khong public)
  → Thay bang "Business Intelligence Graph" (data public, khong rui ro)
- Validation Gate: moi blueprint Sep phai tu chay thu 1 lan truoc khi ban
  → Tranh refund + bao ve reputation

### Wisdom Blueprint Advantages
1. Living Documents: tu dong update khi co info moi
2. Graph-powered Recommendation: match blueprint voi profile user
3. Evidence-based: chi ban proven playbooks, khong ban ly thuyet

---

## BLUEPRINT ROADMAP — 10 San pham cu the (v2026-05-16)

### Tuan nay (data da co san)
| # | Blueprint | Gia | Tool | Status |
|---|-----------|-----|------|--------|
| 1 | YouTube OPC Pipeline Setup | $29 | wisdom_whisper.py | LAM NGAY |
| 2 | FreeLLM API Zero-Cost AI Stack | $19 | SW-002 | LAM NGAY |
| 3 | Wisdom Knowledge OS Starter | $49 | Wisdom itself | FLAGSHIP |

### Thang 1 (sau 10 nodes verified)
| # | Blueprint | Gia | Nguon |
|---|-----------|-----|-------|
| 4 | OPC AI Stack 2026 | $39 | awesome-* repos |
| 5 | MCP Server Quick Start | $39 | wisdom_mcp.py |
| 6 | IndieHacker $1K MRR Patterns | $79 | 50 interviews |

### Thang 2
| # | Blueprint | Gia | Nguon |
|---|-----------|-----|-------|
| 7 | AI Agent Weekend Build Kit | $49 | Case 2 pattern |
| 8 | Hidden Connection Finder | $79 | Neo4j Cypher |
| 9 | Competitor Intelligence Graph | $99 | BettaFish pattern |
| 10 | Vietnam OPC Legal Guide | $99 | VN market unique |

### Revenue projection (conservative)
Thang 1: 3 blueprints x 10 buyers x $29-49 avg = ~$1,200
Thang 2: 6 blueprints x 20 buyers x $39-79 avg = ~$5,000
Thang 3: Marketplace mo + commission = scaling
