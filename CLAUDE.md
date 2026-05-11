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
