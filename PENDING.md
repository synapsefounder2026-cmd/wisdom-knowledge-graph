# PENDING.md — Wisdom Factory
> Doc nay TRUOC KHI bat dau session moi.
> Last updated: 2026-05-04

## COMPLETED
- [x] P-002 watcher fixed 2026-05-04
- [x] P-012 dedup tich hop vao 3 ingest files 2026-05-04

## NEXT
- [ ] P-004 Neo4j <-> Qdrant node_id Bridge
- [ ] P-003 Schema Migration 6 fields
- [ ] P-005 EpistemicConflict Node
- [ ] P-007 Web UI Dashboard
- [ ] P-008 Affiliate Link Generator
- [ ] P-009 Blueprint Marketplace UI
- [ ] P-010 wisdom_code_scout.py
- [ ] P-011 Knowledge Cadence System
- [ ] P-013 Meeting Email Intelligence
- [ ] P-014 wisdom_behavior_tracker.py
- [ ] P-015 wisdom_cron.py
- [x] P-004 Neo4j <-> Qdrant node_id Bridge — 2026-05-04
## COMPLETED TODAY (2026-05-04)
- [x] P-002 wisdom_error_watcher.py fixed
- [x] P-012 dedup tich hop vao 3 ingest files
- [x] P-004 Neo4j <-> Qdrant node_id Bridge
- [x] P-003 Schema Migration 6 required fields

- [x] P-005 EpistemicConflict Node + wisdom_validator.py — 2026-05-04
- [x] P-006 Temporal Decay Function + wisdom_decay.py — 2026-05-04

### [P-010-REF] Graphify Research — Tich hop vao wisdom_code_scout.py
- Repo: github.com/safishamsi/graphify
- Ly do quan tam:
  - AST parser 25 ngon ngu -> dung cho Code Scout
  - EXTRACTED/INFERRED/SYNTHETIC tagging -> ap dung cho relationships
  - 71.5x token savings khi dung graph thay vi raw files
  - Auto-rebuild graph sau moi commit -> hook cho Wisdom
- Viec can lam:
  1. Clone repo, doc code hieu AST extraction logic
  2. Evaluate: dung truc tiep hay hoc concept roi tu build?
  3. Neu MIT license -> tich hop vao wisdom_code_scout.py
- Lien ket: P-010 wisdom_code_scout.py
- Uu tien: Nghien cuu truoc khi build P-010

- [x] P-007 Web UI Dashboard (FastAPI) — 2026-05-04
### [P-017] Interactive Artifacts Engine
- Mo ta: Wisdom tra ve interactive components, khong chi text
- Inspired by: Claude Artifacts feature trong he sinh thai Claude
- Output types:
  chart     -> bar/line/pie tu Neo4j data
  table     -> sortable, filterable knowledge table
  dashboard -> blueprint performance, decay analytics
  card      -> spaced repetition review cards
- Backend: JSON schema response co "artifact_type" field
- Frontend: Dynamic component renderer (D3.js Phase 2, R3F Phase 3)
- Vi du use cases:
  "show knowledge decay" -> bar chart decay by domain
  "blueprint sales"      -> revenue dashboard
  "review due today"     -> spaced repetition cards
  "conflict map"         -> interactive graph
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
### [SESSION UPDATE 2026-05-05]
Thong nhat them voi Antigravity:
- Nature-Centric Design = brand positioning doc dao, khong AI tool nao dang lam
- Blueprints = Skills (SOP cao cap co the thuc thi lap lai)
- Extended Thinking da duoc implement trong wisdom_validator.py
- Interactive Artifacts la tinh nang MOI quan trong nhat session nay
- AskUserQuestion = UI-driven Logic, Wisdom la Partner khong phai bot