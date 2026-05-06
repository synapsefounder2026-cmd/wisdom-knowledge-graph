# PENDING.md — Wisdom Factory
> **Doc nay TRUOC KHI bat dau session moi.**
> Cap nhat sau moi buoi lam viec.
> Last updated: 2026-05-06

---

## URGENT — Lam ngay khi co dieu kien

### [P-001] wisdom_fb_ingest.py — Can cookies.txt
- Van de: FB block anonymous scraping tu 2023
- Trang thai: Code xong, dang cho cookies
- Viec can lam:
  1. Login Facebook tren Chrome
  2. Cai extension: "Get cookies.txt LOCALLY" (Chrome Web Store)
  3. Mo facebook.com -> click extension -> Export
  4. Luu file cookies.txt vao C:\Users\LENOVO\wisdom-knowledge-graph\
  5. Chay: python wisdom/core/wisdom_fb_ingest.py --page "vnexpress.net" --limit 20 --cookies cookies.txt
- File lien quan: wisdom/core/wisdom_fb_ingest.py

---

## SPRINT 1 — Phase 2 (Lam theo thu tu)

### [P-003] Neo4j Schema Migration — 6 Required Fields
- Mo ta: Them 6 required fields vao moi KnowledgeNode theo RULE-B
- Fields can them: trust_score, decay_lambda, valid_from, valid_until, epistemic_status, cultural_context
- File can sua: wisdom_ingest.py, wisdom_upload.py, wisdom_fb_ingest.py
- Script migration: Chua co — can build wisdom_migrate.py

### [P-004] Neo4j <-> Qdrant node_id Bridge
- Mo ta: Them node_id lam cau noi Neo4j va Qdrant tranh data drift
- Nguyen tac: Neo4j ghi truoc -> lay node_id -> ghi Qdrant
- Viec can lam:
  1. Sua save_to_neo4j() de return node_id
  2. Sua save_to_qdrant() de nhan node_id lam payload
  3. Apply cho ca 3 files: ingest, upload, fb_ingest
- NOTE: Phai xong P-004 truoc khi lam P-003

### [P-005] EpistemicConflict Node Type
- Mo ta: Khi 2 nguon mau thuan -> tao Contradiction node, giu ca 2
- Schema: (:KnowledgeNode)-[:CONTRADICTS {confidence_diff: 0.02}]->(:KnowledgeNode)
- File can tao: wisdom_validator.py (Devil's Advocate Agent)

### [P-006] Temporal Decay Function
- Mo ta: Tu dong giam trust_score theo thoi gian
- Formula: trust_score(t) = base_score * exp(-decay_lambda * age_days)
- Viec can lam: Them scheduled job chay hang ngay

---

## PHASE 1 BUSINESS LAYER

### [P-007] Web UI Dashboard
- Tinh nang: Login, Search, Upload, Knowledge Graph view
- Stack: FastAPI + HTML
- Chua bat dau

### [P-008] Affiliate Link Generator
- Da co: affiliate_code trong wisdom_payment.py
- Con thieu: API endpoint, tracking middleware, dashboard
- File lien quan: wisdom_payment.py, wisdom_api.py

### [P-009] Blueprint Marketplace UI
- Da co: process_blueprint_sale() trong wisdom_payment.py
- Con thieu: UI listing, upload form, purchase flow
- Chua bat dau

### [P-010] wisdom_code_scout.py
- Mo ta: Auto scan GitHub/HuggingFace tim open source tools
- License filter: Chi ingest MIT/Apache/BSD
- Chua bat dau

### [P-010-REF] Graphify Research — Tich hop vao wisdom_code_scout.py
- Repo: github.com/safishamsi/graphify
- Ly do quan tam:
  AST parser 25 ngon ngu -> dung cho Code Scout
  EXTRACTED/INFERRED/SYNTHETIC tagging -> ap dung cho relationships
  71.5x token savings khi dung graph thay vi raw files
  Auto-rebuild graph sau moi commit -> hook cho Wisdom
- Viec can lam:
  1. Clone repo, doc code hieu AST extraction logic
  2. Evaluate: dung truc tiep hay hoc concept roi tu build?
  3. Neu MIT license -> tich hop vao wisdom_code_scout.py
- Lien ket: P-010 wisdom_code_scout.py
- Uu tien: Nghien cuu truoc khi build P-010

### [P-011] Knowledge Cadence System
- Mo ta: Moi knowledge node co review_cadence de nhac user xem lai dung luc
- Inspired by: Khang's AI OS — Skill Cadence Wheel (Daily/Weekly/Monthly)
- Fields can them vao Neo4j node:
  review_cadence: daily | weekly | monthly | archive
  last_reviewed: ISO date
  next_review: ISO date
  review_count: int        <- so lan da review
  retention_score: float   <- do bam dinh kien thuc 0.0-1.0
  decay_on_skip: bool      <- co giam trust_score neu bo qua khong
- Logic cadence mac dinh:
  Tech news/trends   -> daily   (decay_lambda = 0.05)
  Frameworks/Methods -> weekly  (decay_lambda = 0.01)
  Core principles    -> monthly (decay_lambda = 0.003)
  Historical ref     -> archive (decay_lambda = ~0)
- Spaced Repetition Integration (SM-2 algorithm giong Anki):
  "de" -> gian next_review ra
  "kho" -> rut ngan next_review lai
- Cadence Analytics Dashboard:
  Bao nhieu node qua han chua review?
  Domain nao dang bi "rot" nhieu nhat?
  Streak review hang ngay (gamification)
- Auto-Cadence Assignment:
  Khi ingest node moi -> Ollama tu dong phan loai cadence
  Dua tren: content_type, domain, decay_lambda
- Dependencies: P-003 (schema migration) phai xong truoc
- Chua bat dau

### [P-012] Tich hop wisdom_dedup.py vao 3 ingest files
- Mo ta: Them SHA-256 dedup check vao dau moi ingest pipeline
- Files can sua: wisdom_ingest.py, wisdom_upload.py, wisdom_fb_ingest.py
- Dependencies: wisdom_dedup.py da xong
- Uu tien: CAO

### [P-013] Meeting & Email Intelligence Layer
- Inspired by: GBrain Enterprise AI Brain concept
- Mo ta: Wisdom doc duoc meeting notes, email, Zalo/Telegram
- Input sources:
  Meeting: Zoom transcript, Google Meet, Teams export
  Email: Gmail (opt-in), Outlook
  Chat: Zalo, Telegram, Slack export
- Xu ly: trich xuat decision, action items, knowledge
- Dua vao EROCA pipeline: INBOX -> RAW -> WIKI
- Dieu kien: user opt-in ro rang, privacy-first
- Uu tien: Phase 2-3

### [P-014] wisdom_behavior_tracker.py
- Self-Improving Loop: detect hanh vi lap lai >= 3 lan
- Auto suggest: "Dong goi thanh Blueprint?"
- Chua bat dau — Phase 2

### [P-015] wisdom_cron.py
- Automation CRON Strip: 07:00 scout, 20:00 decay cleanup
- Every 30min heartbeat
- Chua bat dau — Phase 2

### [P-016] AutoBrowser Integration Research
- Tool: AutoBrowse skill cho Claude Code
- Ung dung cho Wisdom:
  1. FB/TikTok auto-login + scrape (thay cookies thu cong)
  2. wisdom_code_scout.py browser automation
  3. Blueprint execution engine
- SKILL.md output = Blueprint format cua Wisdom
- Lien ket: P-010 (code scout), P-014 (behavior tracker)
- Uu tien: Nghien cuu sau khi P-008, P-009 xong

### [P-017] Interactive Artifacts Engine
- Mo ta: Wisdom tra ve interactive components, khong chi text
- Output types:
  chart     -> bar/line/pie tu Neo4j data
  table     -> sortable, filterable knowledge table
  dashboard -> blueprint performance, decay analytics
  card      -> spaced repetition review cards
- Backend: JSON schema response co "artifact_type" field
- Frontend: Dynamic component renderer (D3.js Phase 2, R3F Phase 3)
- Dependencies: P-007 Web UI phai xong truoc
- Uu tien: Phase 2, sau P-008 P-009

### [P-018] AskUserQuestion UI Engine
- Mo ta: Backend tra ve JSON UI schema, Frontend tu render decision UI
- Kich hoat khi:
  Node chuan bi RAW -> WIKI (ripeness check)
  Conflict detected (EpistemicConflict)
  Cadence chua phan loai
  Trust score qua thap
- JSON Schema format:
  {type, message, options:[{label,value,color}], slider, multi_choice}
- UI cam giac: User dang dieu hanh empire, khong phai dung chatbot
- Tich hop voi: wisdom_validator.py (da co), wisdom_decay.py (da co)
- Dependencies: P-007 Web UI, P-017 Artifacts Engine
- Uu tien: Phase 2

### [P-019] Guided Tour Engine
- Mo ta: Khi user mua Blueprint -> auto-generate tour qua knowledge nodes
- Thu tu logic nhat dua tren ripeness_score + dependency
- Format: [{step, node_id, title, explanation, action}]
- Inspired by: tour-builder agent cua Understand-Anything (MIT)
- Tich hop voi: Blueprint Marketplace (P-009)
- Uu tien: Phase 2, sau P-009

### [P-020] Council Logic — Persona Agent System
- Mo ta: Persona Agents chay interrogation khi node len WIKI
- Khong phai "tai sinh vi nhan" — la Framework Filter + QC System
- Personas co ban:
  buffett -> Circle of Competence, Margin of Safety, Long-term
  jobs    -> User value, Simplicity, "Would I use this?"
  munger  -> Inversion, Mental models, Second-order effects
- Implementation:
  Step 1: council_check() trong wisdom_validator.py (prompt-based, lam ngay)
  Step 2: Nap PDF sach vao wisdom_personas Qdrant collection
  Step 3: Council Board UI (3 persona cards + glassmorphism)
- Neo4j: (:KnowledgeNode)-[:INTERROGATED_BY]->(:PersonaAgent)
- Lien ket: P-018 (AskUserQuestion), Section 17 CLAUDE.md
- Uu tien: Phase 2, sau P-018

### [P-021] Temporal Wisdom Axis — Live-Search Integration
- Mo ta: Query ve HIEN TAI phai trigger Live-Search truoc khi tra loi
- Khong dung cached knowledge cho trend/news/market data
- Domain TTL config:
  trend_tiktok/facebook: 7 ngay
  market_price:          1 ngay
  government_policy:     30 ngay
  framework/principle:   vinh vien
- Implementation:
  1. Them domain_ttl field vao Neo4j node
  2. Khi query -> check valid_until -> neu STALE -> trigger search
  3. Ket qua search -> tao INBOX node moi -> merge vao context
- Tools: AutoBrowse (P-016), Search API
- Lien ket: Section 18 CLAUDE.md, wisdom_decay.py
- Uu tien: Phase 2

### [P-022] Persona 4 & 5 — Street Smart + The Intuition
- Persona 4 (Street Smart):
  Source: FB groups MMO VN, TikTok creator community
  Framework: Nhan biet "mui" lua dao, theo doi algorithm change
  Build: Tu community data khi Wisdom du user
  decay_lambda: 0.05 (cap nhat lien tuc)
- Persona 5 (The Intuition — Sep Thang):
  Day la persona doc dao nhat — ban sao tu duy cua Sep
  Build tu: Lich su decision + Tacit Knowledge Extraction
  Unique moat: Khong AI tool nao co duoc
  Cau hoi: "Sep thay cai nay co 'mui' rui ro o thi truong VN khong?"
- Lien ket: P-020 (Council Logic), Section 17+18 CLAUDE.md
- Uu tien: Phase 2-3

---

## SESSION 2026-05-06 — Tasks Moi

### [P-023] wisdom_cleaner.py — Defuddle Pattern
- Mo ta: Clean web content truoc khi ingest vao RAW layer
- Inspired by: Defuddle trong obsidian-skills (kepano/obsidian-skills)
- Chuc nang:
  Remove: ads, nav, footer, cookie banners, scripts
  Extract: main content, title, author, publish date
  Convert: HTML -> clean Markdown
  Output: structured dict {title, content, url, date, word_count}
- Stack goi y: trafilatura hoac readability-lxml
- Optional: tich hop OpenDataLoader (P-031) khi input la PDF bang bieu
- Tich hop vao: wisdom_fb_ingest.py, wisdom_ingest.py (webpage mode)
- Uu tien: Phase 2 — lam TRUOC wisdom_obsidian_bridge.py

### [P-024] Mermaid Diagram Output
- Mo ta: Wisdom tra ve Mermaid diagram khi query relationships
- De build nhat trong P-017 — khong can D3.js
- Vi du output:
  "Show blueprint dependencies" -> Mermaid flowchart
  "Show knowledge conflicts"    -> Mermaid graph
  "Show decay timeline"         -> Mermaid gantt
  "Show council interrogation"  -> Mermaid sequenceDiagram
- Render trong Web UI bang mermaid.js CDN
- Lien ket: P-017, P-007 Web UI
- Uu tien: Phase 2 — lam truoc D3.js

### [P-025] wisdom_obsidian_bridge.py — Obsidian Local UI
- Mo ta: Dong bo 2 chieu Neo4j <-> Obsidian Vault
- Inspired by: kepano/obsidian-skills
- Chuc nang:
  Wisdom -> Obsidian: Export VERIFIED node thanh .md co Properties + WikiLinks
  Obsidian -> Wisdom: Watch vault, ingest .md moi vao INBOX
  Canvas export: Blueprint -> JSON Canvas (drag-drop)
  Offline mode: Obsidian chay khong can internet
- Node export format:
  ---
  id / title / trust_score / epistemic_status / valid_until
  decay_lambda / review_cadence / tags / related: [[WikiLink]]
  ---
  {content}
- Config: OBSIDIAN_VAULT_PATH trong .env
- CANH BAO: Tao sync complexity — phai lam SAU P-007 stable
- Uu tien: Phase 3

### [P-026] wisdom_node_schema.md — Properties Schema Reference
- Mo ta: Document chuan hoa tat ca properties cho KnowledgeNode
- Noi dung: fields, enum values, decay_lambda mac dinh, cadence mac dinh
- Quan he Neo4j: SUPPORTS, CONTRADICTS, DERIVED_FROM, INTERROGATED_BY, COMPILED_INTO
- Output: wisdom/docs/wisdom_node_schema.md
- Lien ket: RULE-B, P-011, P-020
- Uu tien: CAO — lam ngay, 1 session

### [P-027] KDP MMO Engine — Blueprint Mau Dau Tien
- Mo ta: Build Blueprint KDP 8-Agent lam use case dau tien P-009
- Muc tieu kep:
  1. Sep dung luon de scale KDP business
  2. Demo Blueprint Marketplace cho users tiem nang
- Cau truc Blueprint:
  steps: [niche_hunt, manuscript, cover, listing,
          quality_check, ads_setup, performance_track]
  triggers: ["Toi muon ban sach KDP"]
  human_in_loop: [chon ngach, duyet bia, xac nhan upload]
  expected_output: "1 cuon sach live tren Amazon KDP"
  success_metrics: don hang dau tien trong 30 ngay
- Council check bat buoc:
  Buffett: moat analysis, margin of safety
  Munger:  Amazon policy risk, second-order effects
  Jobs:    cover UX, listing readability
- NOTE: Sep co the bat dau Agent 1 (Niche Hunter) bang Claude Project
  NGAY HOM NAY ma khong can doi Wisdom
- Dependencies: P-009 Blueprint Marketplace
- Uu tien: Phase 2, lam song song P-009

### [P-028] KDP Performance Data Ingest
- Mo ta: Tu dong ingest sales data Amazon KDP vao Neo4j
- Input: Amazon KDP dashboard export (CSV)
- Output: KnowledgeNode voi sales metrics, cap nhat trust_score ngach
- Tich hop: wisdom_cron.py (P-015)
- Uu tien: Phase 2, lam sau P-027

### [P-029] WISDOM_VOICE.md — Output Writing Standard
- Mo ta: Dinh nghia giong van cho moi output cua Wisdom
- Inspired by: "How to get Claude to never sound like AI" writing rules
- 5 rule priority:
  1. Be accurate  2. Be clear  3. Be specific
  4. Sound human  5. Use style only when it improves
- Forbidden phrases:
  "Dua tren knowledge graph..."
  "Co the thay rang..."
  "Nhin chung..."
  "Theo phan tich..."
- Tone: direct, numbers-first, specific, no padding
  BAD:  "Dua tren du lieu, ngach nay co tiem nang kha cao"
  GOOD: "Ngach nay ban duoc. 3 users test, trust_score 0.82. Rui ro: Amazon siet Q1 2025."
- Apply cho: wisdom_query.py, wisdom_validator.py, tat ca output agents
- Output: wisdom/docs/WISDOM_VOICE.md
- Uu tien: CAO — lam ngay, 1 session

### [P-030] Docling Integration — Multi-format Ingest
- Mo ta: Them Docling lam primary document parser
- Repo: github.com/docling-project/docling | License: Apache 2.0
- Input formats mo rong:
  Hien tai: HTML, text, FB posts
  Them: PDF, DOCX, PPTX, XLSX, WAV, MP3
- Dac biet quan trong:
  WAV/MP3 -> WebVTT -> P-013 Meeting Intelligence
  MCP Server -> tich hop truc tiep vao agentic pipeline
- So voi OpenDataLoader:
  Docling MANH HON o: da dinh dang, audio, MCP support
  OpenDataLoader MANH HON o: PDF table accuracy (0.928)
  => Dung Docling lam primary, OpenDataLoader optional cho PDF table
- Uu tien: Phase 2, lam song song P-023

### [P-031] OpenDataLoader — PDF Table Parser (Optional)
- Mo ta: Xu ly PDF co bang bieu phuc tap (bao cao tai chinh, research)
- Repo: github.com/opendataloader-project/opendataloader-pdf
- Diem manh: 0.928 table accuracy, 60+ trang/giay, 100% local
- KHONG phai priority — chi dung khi co use case cu the
- Tich hop nhu optional parser trong wisdom_cleaner.py (P-023)
- License: Apache 2.0
- Uu tien: Phase 2, sau P-030

### [P-032] Wisdom Eye — Vision Input (Mobile First)
- Mo ta: User upload anh -> Wisdom analyze -> tra loi co context
- Day la BUOC DEM truoc AI Glasses
- Input use cases:
  Anh chup san pham -> tra cuu gia tri, ngach thi truong
  Whiteboard meeting -> OCR + tao INBOX node
  Business card -> tao contact node
  Contract/document -> extract key terms, Council check
- Build tren: Docling vision + Claude vision API
- Uu tien: Phase 3, sau P-007 Web UI stable
- NOTE: AI Glasses chi lam sau P-032 stable

### [P-033] Voice-Pro Integration — Audio Ingest
- Mo ta: Tich hop Voice-Pro cho transcription + YouTube ingest
- Repo: github.com/abus-aikorea/voice-pro | MIT license | 8k stars
- Use cases DUOC PHEP:
  YouTube video -> transcript -> wisdom_ingest.py -> INBOX node
  Meeting recording -> tach giong -> tao INBOX node (P-013)
  Audio cleanup truoc khi transcribe
- USE CASE BI CAM: Voice clone tu dong khong co consent
  -> Bat buoc explicit user confirmation truoc khi clone bat ky giong nao
- Tich hop voi: P-013 Meeting Intelligence, P-030 Docling
- Uu tien: Phase 2

### [P-034] OPC Onboarding Flow — Web UI Content
- Mo ta: Giai thich dung OPC la gi cho user moi trong P-007 Web UI
- Key message:
  "OPC la mo hinh van hanh, khong phai 1 nguoi + 1 ly ca phe + 1 laptop"
  "AI la Labor Force, khong phai Tool"
  "Wisdom = He dieu hanh OPC, khong phai chatbot"
  Formula: 1 Founder + 1 AI Labor + N doi tac
- Onboarding screens:
  Screen 1: Ban la Freelancer, Solopreneur hay OPC?
  Screen 2: OPC can gi? -> Quy trinh chuan hoa + AI thuc thi
  Screen 3: Wisdom lam duoc gi cho OPC cua ban?
- Uu tien: Lam song song P-007

### [P-035] Open Access Research Ingest
- Mo ta: Ingest academic knowledge tu nguon hop phap
- Nguon DUOC PHEP: arXiv, Semantic Scholar, PubMed, Unpaywall
- TUYET DOI KHONG DUNG: Sci-Hub
  Ly do: Vi pham ban quyen -> legal risk cho commercial product
- Output: KnowledgeNode voi epistemic_status = ACADEMIC
- Uu tien: Phase 2

### [P-036] Curated Skill Library — Quality over Quantity
- Mo ta: Thu vien 50-100 skills chat luong cao, KHONG phai 10,000+ noise
- Nguon uu tien:
  Agentskill.sh — atomic packages, CLI verified
  Warp .agents/skills/ — hoc PATTERN, khong copy code (AGPL license!)
  Skill-hub.ai — persona playbooks (verify license truoc)
- Quy trinh nhap kho BAT BUOC:
  1. License check: chi MIT / Apache 2.0 / BSD
  2. Security scan: khong co malicious code
  3. Council interrogation (Buffett/Jobs/Munger)
  4. Sandbox test
- Muc tieu: 50 skills verified > 10,000 skills noise
- Uu tien: Phase 2, lam TRUOC P-037

### [P-037] Skill Mining Pipeline — Revised Scope
- DIEU CHINH: Giam scope tu "10,000+ tu dong" xuong "50-100 curated"
- Mo ta: Pipeline ban thu cong co security gate
  Module 1: harvester.py — chi lay metadata, khong auto-execute scripts
  Module 2: security_scan.py — quet ma doc, kiem tra license
  Module 3: sandbox_runner.py — chay thu trong Docker isolated
  Module 4: vault_manager.py — nhap vao wisdom/skills/ neu pass tat ca
- Human gate: Sep phai duyet tung skill truoc buoc 3
- Uu tien: Phase 3, sau P-036

### [P-038] Infrastructure Roadmap — OPC Server Strategy
- Giai doan 1 (Hien tai — Laptop):
  Muc tieu: Build loi, test, dev
  ACTION NGAY: Setup rclone sync Neo4j + Qdrant -> cloud storage
  wisdom_backup.py them vao P-015 cron
- Giai doan 2 (Khi P-007 xong):
  VPS: Hetzner CCX23 (~$40/thang) hoac DigitalOcean
  Chay: Neo4j + Qdrant + FastAPI + wisdom_cron.py
- Giai doan 3 (Khi co Marketplace revenue):
  Dedicated Server hoac Private Cluster
  GPU: can cho Voice-Pro + Docling heavy load
  Estimate: $200-500/thang tuy scale
- Mo hinh Hybrid:
  Private Server: Wisdom core (Neo4j, Qdrant)
  Cloud: Scale tasks (Voice-Pro, Docling batch)
  Laptop: Dev, test, prototype
- Uu tien: Backup script lam NGAY, Server la Phase 2-3

---

## DEPENDENCY TABLE (Cap nhat 2026-05-06)

| Pending | Phu thuoc vao | Ghi chu |
|---------|---------------|---------|
| P-004 node_id bridge | Lam truoc P-003 | - |
| P-005 Conflict node | Can P-003 truoc | - |
| P-007 Web UI | Can P-004 truoc | - |
| P-011 Cadence | Can P-003 truoc | - |
| P-023 wisdom_cleaner | Khong | Lam ngay |
| P-024 Mermaid output | P-007 | - |
| P-025 Obsidian bridge | P-007 stable | Phase 3 |
| P-026 node_schema.md | Khong | Lam ngay |
| P-027 KDP Blueprint | P-009 | Agent 1 lam ngay bang Claude Project |
| P-028 KDP Data Ingest | P-027, P-015 | - |
| P-029 WISDOM_VOICE.md | Khong | Lam ngay |
| P-030 Docling | Khong | Lam song song P-023 |
| P-031 OpenDataLoader | P-023 | Optional |
| P-032 Wisdom Eye | P-007 stable | Phase 3 |
| P-033 Voice-Pro | P-013, P-030 | - |
| P-034 OPC Onboarding | P-007 | Song song |
| P-035 Open Access | Khong | Phase 2 |
| P-036 Curated Skills | Khong | Truoc P-037 |
| P-037 Skill Mining | P-036 | Phase 3 |
| P-038 Infrastructure | Khong | Backup ngay |

---

## COMPLETED

- [x] CLAUDE.md day du den Section 19
- [x] wisdom_error_watcher.py chay on, 0 false positive — P-002
- [x] wisdom_ingest.py Fixed EP-001, EP-004
- [x] wisdom_query.py Fixed EP-001, EP-004
- [x] wisdom_upload.py Fixed EP-001, EP-002, EP-004
- [x] wisdom_payment.py Unified Ledger test passed 100%
- [x] wisdom_fb_ingest.py Code xong cho cookies
- [x] wisdom_dedup.py — SHA-256 dedup done
- [x] wisdom_decay.py — Temporal Decay Function done
- [x] wisdom_validator.py — EpistemicConflict + Extended Thinking
- [x] wisdom_schema.py — Schema chuẩn hóa
- [x] P-004 Neo4j <-> Qdrant node_id Bridge — 2026-05-04
- [x] P-003 Schema Migration 6 required fields — 2026-05-04
- [x] P-005 EpistemicConflict Node — 2026-05-04
- [x] P-006 Temporal Decay Function — 2026-05-04
- [x] P-007 Web UI Dashboard (FastAPI) — 2026-05-04
- [x] P-012 dedup tich hop vao 3 ingest files — 2026-05-04
- [x] Architecture thong nhat voi Antigravity
- [x] Business Strategy Section 10 CLAUDE.md
- [x] FB/TikTok Strategy Section 12 CLAUDE.md
- [x] Section 19 Obsidian Integration Strategy — 2026-05-06
- [x] Nghien cuu kepano/obsidian-skills — 2026-05-06
- [x] Phan tich KDP 8-Agent pipeline — 2026-05-06
- [x] Nghien cuu Docling + OpenDataLoader — 2026-05-06
- [x] Writing Rules "No AI voice" — 2026-05-06
- [x] Phan tich OPC Framework — dinh vi Wisdom = OPC OS — 2026-05-06
- [x] Danh gia Voice-Pro, Warp, Sci-Hub, 5 Skills sources — 2026-05-06
- [x] P-010-REF Understand-Anything Research Done — 2026-05-05

---

## NOTE CHIEN LUOC (2026-05-06)

### Wisdom = He Dieu Hanh OPC — Dinh Vi Chinh Thuc
- KHONG PHAI: Chatbot thong minh hon
- LA: He dieu hanh cho Doanh nghiep mot nguoi
- Formula: 1 Founder + 1 AI Labor Force + N doi tac
- Ky nang quan trong nhat cua OPC Founder:
  KHONG PHAI dung AI gioi
  LA chuan hoa quy trinh thanh thu AI co the thuc thi

### Phan cong trong he thong
- Antigravity: Expansion — tim co hoi, vision xa
- Claude: Stability — kiem tra tinh hop le, security, thu tu
- Sep: Quyet dinh cuoi cung

### Canh bao rui ro
- Warp license AGPL-3.0: hoc pattern duoc, copy code la sai
- Sci-Hub: tuyet doi khong tich hop (legal risk commercial)
- Voice clone: can explicit consent
- Skill mining: curate 50 > mining 10,000
- Server: backup truoc, scale sau

---

## NHAC NHO DAU SESSION TOI

Lam ngay (khong co dependency):
1. wisdom_backup.py — bao ve Neo4j + Qdrant khoi mat du lieu
2. P-026 wisdom_node_schema.md — 1 session
3. P-029 WISDOM_VOICE.md — 1 session

Sau do theo dependency chain:
P-004 (node_id bridge) -> P-003 (schema migration) -> P-007 (Web UI)

---
*PENDING.md — Doc dau moi session | Cap nhat cuoi moi buoi lam viec*
*Last updated: 2026-05-06 | Version: Full reconstructed*