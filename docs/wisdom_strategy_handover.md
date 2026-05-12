# wisdom_strategy_handover.md
> Tong hop TOAN BO chien luoc Wisdom — co filter va danh gia trang thai.
> Doc SAU CLAUDE.md, TRUOC khi bat dau code.
> Status: VALIDATED | PHASE 2-3 | CAN REVIEW | FROZEN
> Last updated: 2026-05-11 | P-042

---

## 1. DINH VI ✅ VALIDATED
Wisdom = He dieu hanh OPC. KHONG PHAI chatbot. LA OS cho 1 nguoi van hanh bang AI.
Formula: 1 Founder + AI Labor Force + N Partners
Soul: Explicit (99%) AI xu ly. Tacit (1%) = Moat that su cua Sep.
Quote: "Co the thue ngoai suy nghi. Khong the thue ngoai thau hieu."

## 2. KIEN TRUC ✅ VALIDATED
4-Layer: INBOX -> RAW -> WIKI -> OUTBOX
Stack: Neo4j + Qdrant + Ollama + FastAPI | Windows 11, Git Bash
P-004 Bridge (done): Neo4j elementId() -> Qdrant neo4j_node_id payload
Dual-Format: Markdown = Source of Truth | HTML = Presentation layer

## 3. RULES ✅ VALIDATED
RULE-A: Write Neo4j TRUOC -> lay node_id -> write Qdrant
RULE-B: 7 fields bat buoc: trust_score, decay_lambda, valid_from, valid_until, epistemic_status, cultural_context, source_type
RULE-C: trust_score(t) = base * exp(-lambda * age_days)
RULE-D: Validation ASYNC — khong block ingest
RULE-E: Tacit knowledge = explicit opt-in
RULE-F: Mau thuan -> tao CONTRADICTS node, khong xoa
RULE-G: Qdrant: wisdom_public | wisdom_private_{uid} | wisdom_shadow
RULE-H: Obsidian bridge chi lam SAU P-007 stable

## 4. MULTI-AGENT RESEARCH ENGINE 🔵 PHASE 2
Feynman pattern: Researcher | Reviewer | Writer | Verifier
Heavy tasks -> RunPod/Modal
Trigger: Sau 10 buyers va P-007 API stable

## 5. MARKDOWN SKILL FILES 🔵 PHASE 2
Moi agent = 1 Markdown Skill File (self-documenting, Git-synced)
Template: templates/WISDOM_SKILL_TEMPLATE.md da co san

## 6. WISDOM CANVAS 🔵 PHASE 3
Infinite board — human + AI tren Shared State
Output: Research Map, Verification Dashboard, Knowledge Graph view
Dependencies: P-007 stable + P-017 Artifacts Engine

## 7. MONETIZATION ✅ VALIDATED
Hom nay: P-056 Gumroad $49 Early Bird (cho PayPal 3 ngay)
Sau buyer #1: Collect feedback, iterate SPEC.md, Blueprint #2
Phase 2 (10 buyers): Marketplace (P-009), KDP 8-Agent (P-027, da co 13 orders)
Phase 3 (50+ users): SaaS $29-299/thang, RevShare 0.5-2.5%, Exit Commission 5-10%

## 8. COUNCIL SYSTEM ✅ VALIDATED (P-020)
Buffett: Circle of Competence, Margin of Safety
Jobs: User value, Simplicity
Munger: Inversion, Second-order effects
Flow: UNVERIFIED -> PENDING -> VERIFIED -> CONTRADICTED
ARIS Pattern: Generator viet -> Reviewer phan bien -> iterate den 9/10

## 9. CONTEXT COMPRESSION ✅ VALIDATED (P-041)
Caveman Protocol: Fragment, bo filler, giam 65-75% tokens (internal only)
AgentMemory 🔵 PHASE 2: RAG-based, tiet kiem 95% token, sau P-007
Spec-kit: Blueprint = machine-readable SPEC.md, khong chi text

## 10. MULTI-TENANT ARCHITECTURE 🔵 PHASE 2-3
Moi node: tenant_id + project_id
Query: WHERE n.tenant_id = 'user_x' OR n.tenant_id = 'GLOBAL'
Hybrid: Web Dashboard (non-tech) + MCP Server (pro users)
Data Flywheel: Private node -> strip PII -> promote GLOBAL
Trigger: 50+ users

## 11. ACTION-ORIENTED MCP 🔵 PHASE 2
GOOD: "Scan 50 Blueprints, bulk update trust_score"
GOOD: "Trigger Ingestor scrape latest 10 posts"
GOOD: "Generate study roadmap from node Y"
Lien ket: P-007 FastAPI -> MCP wrapper

## 12. INGEST SOURCES — Legal ✅ VALIDATED
DUOC PHEP: YouTube (CC), Coursera Audit, MIT OCW, arXiv, PubMed, GitHub MIT/Apache
BI CAM: Sci-Hub, Glassdoor, LeetCode, Udemy downloader, Voice clone khong consent

## 13. WISDOM LENS 🔵 PHASE 2 (P-043)
Chrome Extension thay the P-001 FB cookies
1-click capture -> POST /api/clip -> INBOX node
ToS disclaimer bat buoc
Trigger: Sau P-007 /api/clip ready

## 14. DOCUMENT PROCESSING 🔵 PHASE 2
P-044 Firecrawl MCP: Evaluate TRUOC khi build P-023
P-023 wisdom_cleaner.py: trafilatura/readability-lxml (neu P-044 khong du)
P-030 Docling: PDF/DOCX/PPTX/XLSX/WAV/MP3, MCP Server support (primary)
P-031 OpenDataLoader: PDF table accuracy 0.928 (optional)

## 15. KNOWLEDGE CADENCE SYSTEM 🔵 PHASE 2 (P-011)
Fields: review_cadence, last_reviewed, next_review, review_count, retention_score
Tech news -> daily (0.05) | Frameworks -> weekly (0.01) | Principles -> monthly (0.003)
SM-2 Spaced Repetition: De = gian ra, Kho = rut ngan

## 16. FAANG 196 ⚠️ CAN REVIEW
196 LeetCode patterns distilled tu 3500+ boi Senior SWE FAANG
Can Council check: feasibility, legal, commercial viability
Content Flywheel chua validate: 196 nodes -> 196 videos MMO Faceless
Legal: Chi ingest nguon open (arXiv, MIT OCW, GitHub MIT/Apache)

## 17. B2B AFFILIATE ENGINE ⚠️ CAN REVIEW (P-058)
Target: Kyma API, AI proxies, commission 10-20% recurring
Social Graph Flywheel: KOL adopt Blueprint -> link spread virally
Warning: Affiliate links phai minh bach voi user (FTC guidelines)
Status: Phase 3, validate market truoc

## 18. BLACK BOX STRATEGY ✅ VALIDATED
Marketing: Show results va story (FOMO), KHONG sell How-To
Product: User mua Access (rent Engine, khong thay Source Code)
Implementation: Heavily sandboxed, no prompt injection

## 19. SCHOOL OF FISH ✅ VALIDATED
Multiple niche projects nho ($30K-50K/thang moi) vs 1 monolith
20/80 Rule: 20% human + 80% agentic
Niche Moat: Hard niches -> scare off competitors

## 20. SELF-IMPROVING LOOP ✅ VALIDATED
Fix bug -> update CLAUDE.md ngay. KHONG tao RULES.md rieng.
Complex tasks -> delegate subagents
Never mark done khong co proof

## 21. FEEDING THE GRAPH ✅ VALIDATED
Knowledge Graph = Asset chinh (nhu Pixel trong E-commerce)
Feed high-quality data TRUOC Execution phase
Data Quality + Volume -> Mature Brain -> high-ticket consultancy

## 22. CODE-DRIVEN AI ✅ VALIDATED
Open-source only: Python, R, n8n, Ollama
KHONG dung commercial GUI (SPSS, etc.)
Blueprints: Jupyter, RStudio, open-source CLI

## 23. LOCAL INTELLIGENCE & SECURITY ⚠️ CAN REVIEW
Gutenberg AI: Ollama + OpenCV, scan physical docs -> Knowledge Graph
Evaluate vs Tesseract hien tai trong wisdom_upload.py
PATCH NGAY: Ollama -> v0.17.1+ (CVE-2026-7482, severity 9.1)

## 24. LONG-TERM MEMORY 🔵 PHASE 2
Claude-Mem (SQLite + ChromaDB): Project timelines + observations
AI Legal: 14 skills (contract review, NDA, risk scoring) -> /legal commands
Shopee Autopilot ⚠️: Validate Sep co shop khong truoc khi build

## 25. CONTENT FACTORY ⚠️ CAN REVIEW
TradingAgents + Dexter: Analyst -> Trader -> Portfolio Manager (Phase 3)
Pixelle-Video: Script -> TTS -> Video (Phase 3, sau buyer #1)
DocuSeal 🔵: Open-source digital signature, OPC contracts (Phase 2)

## 26. SMOLAGENTS 🧊 FROZEN (P-057)
CodeAgent: viet va execute Python snippets
FROZEN: Implement sau 10 buyers
Evaluate: So sanh voi Ollama + LangChain hien tai

## 27. NEURAL SWARM — Ruflo ⚠️ CAN REVIEW
48k stars, agents learn tu successful tasks
Status: Phase 3, validate architecture truoc khi commit

## 28. DEEPSEEK V4 ⚠️ CAN REVIEW
1M token context, 1/10 cost so voi Claude 3.5
Decision chot: Local-only cho tacit knowledge
Cloud API: Chi research public repos, KHONG cho data Sep

## 29. PROJECT AEGIS 🧊 FROZEN (P-059)
Goal: Autonomous C-UAS (Counter-Drone) defense system
Hardware: PLFM Radar 10.5GHz + PCB Motors (Carl Bugeja)
Software: Micro-Doppler AI + Biomimetic (Hawk/Dragonfly pursuit)
Swarm: Decentralized bee-colony logic cho interceptor drones
Spec: docs/PROJECT_AEGIS_BLUEPRINT.md
TRIGGER UNLOCK: Sau 10 Gumroad sales. KHONG dong code truoc do.

## 30. OPC MACRO VISION 🔵 PHASE 3
1 Million Sovereign OPCs
BUILD: Knowledge Graph, Agent Orchestration, CLAUDE.md
BUY: Stripe Atlas, LLM APIs
PARTNER: Digital Residency (Estonia/Palau), Tax APIs
Revenue: SaaS + RevShare + Exit Commission + Compute Arbitrage

## 31. SPATIAL UI 🔵 PHASE 3
MediaPipe: Webcam 60FPS -> gesture control Knowledge Graph
DeepTutor: TutorBot rieng moi OPC user
Curriculum: MIT 6.S191 (Intro to Deep Learning)
Trigger: Sau P-007 stable

## 32. COST ARBITRAGE ⚠️ CAN REVIEW
NVIDIA NIM API: 5,000 free credits, chi cho isolated research
KHONG dung cho production data
Fullstack Persona (Mina/Alexander): 28 skills, AI Avatar, Voice Cloning

## 33. INFRASTRUCTURE ✅ VALIDATED
Phase 1: Laptop + OneDrive | $0 | Dang lam
Phase 2: Hetzner CX32 4vCPU 8GB | $14/thang | Khi P-007 xong
Phase 3: Hetzner CX52 + RunPod GPU | $50-80 + bien phi | 50+ users
Backup: bash backup_now.sh hang toi 21:00 (P-039 done)
VPS Security: ufw deny 7474/6333 | Neo4j/Qdrant localhost only | Fail2ban

## 34. LEGAL & IP ✅ VALIDATED
DeepSeek Local-only | KHONG Sci-Hub | KHONG Glassdoor/LeetCode
KHONG Arkon (PolyForm) | KHONG Warp code (AGPL)
50 curated skills > 10,000 noise
Ollama patch v0.17.1+ (CVE-2026-7482)
Voice clone: explicit consent bat buoc
Affiliate links: minh bach voi user (FTC)

## 35. PHAN CONG HE THONG ✅ VALIDATED
Sep: Quyet dinh cuoi, tacit knowledge, dinh huong
Antigravity: Expansion, vision, repo research, inspire
Claude: Stability, hop le, security, phan bien, code

## SCOPE CREEP WARNING ✅ VALIDATED
FROZEN: Aegis (P-059), smolagents (P-057), TradingAgents, Pixelle-Video,
        Spatial UI, Neural Swarm (Ruflo), DeepSeek cloud, AI Glasses
Signal: 1 buoi sang mo 5+ tasks moi -> DUNG LAI, doc file nay

## LINKS NHANH
CLAUDE.md | PENDING.md | docs/wisdom_node_schema.md
docs/WISDOM_VOICE.md | docs/WISDOM_ARCHITECTURE.md
docs/PROJECT_AEGIS_BLUEPRINT.md
wisdom/core/: wisdom_ingest.py | wisdom_upload.py | wisdom_fb_ingest.py
wisdom/core/: wisdom_decay.py | wisdom_dedup.py | wisdom_migrate_p003.py

---
*P-042 | 2026-05-11 | Filter tu CLAUDE_STRATEGY_HANDOVER.md 35 sections*
