# Wisdom Project Summary v2026

**Tầm nhìn:**  
Xây dựng một "Bản đồ Tri thức" sống, tự tiến hóa, kết hợp Second Brain cá nhân và cộng đồng tri thức Việt Nam. Wisdom không chỉ lưu trữ kiến thức mà còn giúp người dùng hiểu sâu, kết nối ý tưởng, và biến tri thức thành hành động (học tập + kiếm tiền).

**Nguyên tắc cốt lõi:**
- Local-first + Privacy (dữ liệu nằm trên máy người dùng)
- Human in the loop (người dùng luôn có quyền quyết định cuối cùng)
- Self-evolving (hệ thống tự học, tự sửa lỗi, tự bổ sung kiến thức)
- Harness Engineering (môi trường vững chắc cho AI agent)
- SRS-First (thiết kế yêu cầu rõ ràng trước khi code)

**Kiến trúc chính:**
- Knowledge Graph (Neo4j) + Vector Database (Qdrant)
- Per-User Vectorization (mỗi người dùng có không gian vector riêng)
- Living Knowledge Map (nodes, edges, colorful + bling visualization)
- Paperclip-style AI Operating System (orchestration, event-driven, budget control)
- Personalized TutorBot System
- Enterprise Agent Builder (local + cloud burst)
- AI Tri Kỷ & Digital Companions
- Intelligent Growth Engine + Amazon Flywheel model

**Ngách Kiếm Tiền & Hệ Sinh Thái Wisdom (Note 1 + Note 2 + Note 3 – 14/04/2026)**

Wisdom xây dựng một **Hệ sinh thái đặc quyền (Special Ecosystem)** theo mô hình **Solar System Architecture**, với 3 trụ cột kiếm tiền chính:

**1. Solar System Ecosystem & Authority-Based Affiliate (Note 3 – Ưu tiên triển khai sớm)**  
Wisdom đóng vai **Mặt trời** (trung tâm điều khiển, lưu trữ tri thức, Dashboard chính).  
Các nền tảng bên ngoài (YouTube, Midjourney, Sora, ElevenLabs, Canva…) là **Vệ tinh**.  
Thay vì làm video affiliate truyền thống, Wisdom tận dụng **vẻ đẹp tri thức, tâm hồn và hình ảnh cá nhân** của Sếp để tạo sức hút.  
User có thể “Clone” dự án mẫu / Template chất lượng cao của Sếp → tự động nhận link affiliate tinh tế qua **Recommended Stack**.  
Affiliate không phải quảng cáo thô, mà là “Cấu hình đề xuất” mà Sếp thực sự dùng và tin tưởng.  
Lợi ích: Tăng retention Subscription mạnh mẽ, xây dựng thương hiệu bền vững theo nguyên tắc “Hữu xạ tự nhiên hương”.

**2. Open Source Intelligence Layer (Note 1 – Hỗ trợ user non-tech)**  
Giúp người không biết code vẫn dễ dàng tiếp cận và tận dụng repo open source.  
Wisdom sử dụng AI để giải thích repo, hướng dẫn cài đặt, customize và đánh giá mức độ phù hợp.  
User có thể bắt đầu từ những việc nhỏ (tạo trang web tĩnh, tool đơn giản) và dần tích hợp vào Wisdom Graph.  
Đây là nền tảng để user non-tech tự tin tham gia sâu hơn vào hệ sinh thái.

**3. Agentic Economy & Wisdom Credit System (Note 2 – Nguồn thu dài hạn, triển khai Phase 2+)**  
Xây dựng **Sàn giao dịch lao động lai** (Agent Marketplace): User có thể niêm yết và cho thuê Skill/Agent đã huấn luyện.  
Giới thiệu **Wisdom Credit** (100 Credit = 1 USD) làm tiền tệ nội bộ ổn định.  
Cơ chế cốt lõi: Escrow + Sandbox + Validator Agent + Proof of Value.  
Phí sàn tự động **18%** cho Sếp trên mọi giao dịch Agent.  
Bảo mật chiều sâu: Data Sharding, Micro-Wallets, Honey Pots, Economic Disincentive, Master Switch (Freeze Wallet, Tax Adjuster…).  
Hướng phát triển sau: Resource Pooling (Wisdom Hub API) theo phased approach an toàn, bắt đầu từ đàm phán Enterprise Plan với các tool hot nhất.

**Chiến lược triển khai tổng thể:**
- **Giai đoạn 1–2 (ưu tiên)**: Tập trung mạnh Note 3 (Solar System) + Note 1 (Open Source Adapter) để xây dựng branding, retention và thu nhập thụ động từ affiliate.
- **Giai đoạn 2–3**: Triển khai Note 2 (Agent Marketplace + Wisdom Credit) khi đã có lượng user trả phí ổn định và hệ thống bảo mật đủ mạnh.
- Toàn bộ mô hình hướng đến việc biến Wisdom thành **Ecosystem Owner**, nơi user không chỉ dùng tool mà còn sống và kiếm tiền trong hệ sinh thái do Sếp kiến tạo.

**Công nghệ stack (Phase 0):**  
- Ollama (local models)  
- GitNexus (code intelligence)  
- Docker + Docker Compose  
- VS Code + Claude Code / Antigravity (vibe coding)

**Files hiện tại:**  
- WISDOM_PROJECT_SUMMARY_v2026.md ← File này  
- WISDOM_CO_BUILDER_v2.0.md  
- WISDOM_SKILL_TEMPLATE.md  
- README.md

**Trạng thái hiện tại:** Phase 0 - Local Setup (Đang thực hiện)
## Wisdom Value Flywheel (Chốt 2026-05-01)

Mọi tính năng trong Wisdom phải phục vụ ít nhất một tầng 
trong vòng flywheel sau:

Học tập → Kinh nghiệm → Kiếm tiền → Cống hiến 
→ Phát triển bản thân & Cộng đồng → (lặp lại ở tầng cao hơn)

**Nguyên tắc thiết kế:** Nếu một tính năng không trả lời được 
câu hỏi "Tính năng này giúp user tiến lên tầng nào trong 
flywheel?" → không build.

**Giá trị đích thực Wisdom hướng đến:**
- Học tập hiệu quả hơn nhờ AI + Knowledge Graph
- Tích lũy kinh nghiệm thành tài sản số cá nhân
- Kiếm tiền đủ để tồn tại và khẳng định giá trị
- Cống hiến lại cho cộng đồng tri thức Việt Nam
- Phát triển bản thân và cộng đồng bền vững
## Target Market & Pricing (Chốt 2026-05-01)

### Beachhead Market: MMO/Affiliate Community
- Việt Nam first → SEA → Global
- Đa ngôn ngữ từ kiến trúc đầu tiên

### Pricing (Year only, no monthly)
- Founding: $99/year (100 người đầu)
- Standard: $199/year
- MMO Pro: $499/year (teams)
- Enterprise: $999+/year

### Quy mô mục tiêu
- Phase 1: 50 Founding Members
- Phase 2: 500 Standard users
- Phase 3: 2,000+ global users
---

## Input Intelligence Architecture (Chốt 2026-05-02)

Wisdom tiếp nhận knowledge từ MỌI nguồn đầu vào có thể — manual, URL, auto-crawl, real-time.
Dù input từ nguồn nào, đều qua chung một Universal Processing Pipeline.

---

### TIER 1: Manual Input (User chủ động cung cấp)

**Documents & Text:**
- PDF (sách, research papers, reports)
- Word (.docx), Excel (.xlsx), PowerPoint (.pptx)
- Markdown, Notion export, Plain text (.txt)
- EPUB, MOBI (ebooks)
- Scanned documents + Handwritten notes (OCR)

**Audio:**
- MP3, WAV, M4A upload
- Podcast episodes, Voice memos
- Meeting recordings (Zoom, Teams, Google Meet)
- Audio books

**Video:**
- MP4, MOV upload trực tiếp
- Screen recordings, Webinar recordings
- Online course videos

**Images:**
- Screenshots (code, UI, diagrams)
- Infographics, Whiteboard photos
- Mind maps, Charts & graphs
- OCR text extraction từ images

**Structured Data:**
- CSV, JSON, XML
- Database exports, Spreadsheets
- API responses

---

### TIER 2: URL & Social Input (User paste link)

**Video Platforms:**
- YouTube (public + unlisted), Facebook Video
- TikTok, Instagram Reels, LinkedIn Videos
- Vimeo, Bilibili, Rumble

**Content Platforms:**
- Blog posts, articles, Medium, Substack
- Wikipedia, News articles, Landing pages

**Social & Community:**
- Facebook posts/groups, Twitter/X threads
- Reddit threads, LinkedIn posts, Quora answers
- Discord (export), Telegram channels

**Knowledge & Code:**
- GitHub repos (README + code), GitLab, Bitbucket
- Stack Overflow threads, Documentation sites
- Notion pages (public), Google Docs (shared)

**Audio Platforms:**
- Spotify podcasts, Apple Podcasts
- SoundCloud, Anchor.fm

---

### TIER 3: Auto-Ingestion (Wisdom tự động theo dõi)

**Curated Author Tracking:**
- Chỉ track tác giả đã được vetting + approved
- Vetting criteria: credibility score, topic alignment, content quality
- Auto-ingest new content trong 24h sau khi publish
- Nguồn: YouTube channels, Facebook pages, TikTok, Newsletters, RSS, Substack, GitHub accounts

**Personal Behavior Signals (opt-in):**
- Browser bookmarks sync
- YouTube watch history, Facebook saved posts
- Twitter/X bookmarks, Pocket/Instapaper saves
- Kindle highlights, Notion/Obsidian vault sync
- Chrome/Edge history (opt-in, anonymized)

---

### TIER 4: Real-time & Live Input (Phase 3)
- Live streams (YouTube Live, FB Live)
- Spaces/Clubhouse audio
- Real-time news feeds
- API webhooks từ external tools
- Email inbox (opt-in, filter by rules)
- Calendar events & meeting notes
- Slack/Teams workspace (opt-in)

---

### TIER 5: Device & Sensor Input (Phase 3+)
- Mobile camera (scan document, whiteboard)
- Mobile microphone (voice note → ingest)
- Wearable data (focus time, productivity patterns)
- Screen capture agent (what user reads on screen)

---

### Universal Processing Pipeline

Dù input từ nguồn nào, đều qua chung pipeline:

```
Any Input Source
      ↓
[Format Detector] → identify file type
      ↓
[Extractor] → text / audio / video → raw content
      ↓
[Quality Filter] → duplicate, spam, illegal, sensitive
      ↓
[AI Analyzer] → Ollama / Claude
      → title, summary, concepts, tags
      → language, flywheel layer
      → source credibility score
      ↓
[Privacy Classifier]
      → Personal only / Contribute to Pool / Public
      ↓
[Neo4j Knowledge Graph] + [Qdrant Vector DB]
      ↓
Personal Space + Knowledge Bank
```

---

### Verified Solution Pool (Chốt 2026-05-02)

Mỗi solution trong Pool phải:
- Được verify thực tế (đã chạy được, có context: OS, version, hardware)
- Gắn tag đầy đủ để match đúng user context
- Ranked by: số lần dùng thành công + thời gian tiết kiệm được
- Owner nhận Wisdom Credit khi người khác dùng solution của mình
- Không expose raw content nếu owner không muốn — chỉ inject kết quả vào context

---

### Pre-flight System Check (Chốt 2026-05-02)

Trước khi user bắt đầu làm việc với Wisdom, hệ thống tự động scan:

**Hardware Check:**
- RAM available (Ollama cần tối thiểu 8GB)
- Disk space (models + Docker volumes)
- GPU/CPU capability
- Working directory — suggest move từ C: sang D: nếu cần

**Software Check:**
- Python version, pip packages installed
- Docker running + healthy
- Ollama installed + models pulled
- Git Bash / WSL setup
- Port conflicts (7474, 7687, 6333, 11434)

**Environment Check:**
- PATH variables đúng chưa
- TMPDIR, MSYS settings (Windows)
- API keys configured

**Output:**
- Readiness Score
- Auto-fix issues nếu có thể
- Guide từng bước nếu cần manual fix
- Match user với Solution Pool phù hợp cấu hình máy

---

### Privacy Architecture — 3-Layer Model

**Layer 1 — Personal (chỉ user thấy):**
- Behavior data, personal notes
- Sensitive searches, private bookmarks

**Layer 2 — Anonymized Pool (contribute vào bank):**
- Patterns được anonymize hoàn toàn
- Không trace về individual
- User opt-in, nhận Credit khi contribute

**Layer 3 — Public Knowledge Bank:**
- Verified solutions
- Curated author content
- Community-approved insights

**Content Filter tự động:**
- Loại bỏ: hate speech, illegal, adult, misinformation
- Flag: sensitive topics → human review
- Comply: GDPR, platform ToS, Vietnamese law

---

### Auto-Quality Control

Trước khi vào Knowledge Bank:
- Duplicate detection
- Freshness check (outdated?)
- Conflict check (mâu thuẫn knowledge cũ?)
- Source credibility score
- AI fact-check với external sources

Sau khi vào Bank:
- Decay score theo thời gian (tech content cũ nhanh)
- Community feedback loop
- Auto-archive nếu outdated

---

### Input Source Priority Matrix

| Nguồn | Độ phong phú | Ưu tiên |
|---|---|---|
| Manual upload (doc/pdf/video/audio) | ⭐⭐⭐ | Phase 1 |
| YouTube URL | ⭐⭐⭐⭐ | Phase 1 |
| Website/Blog URL | ⭐⭐⭐ | Phase 1 |
| FB/TikTok (cookies) | ⭐⭐⭐⭐ | Phase 1 |
| GitHub repos | ⭐⭐⭐ | Phase 1 |
| Auto author tracking | ⭐⭐⭐⭐⭐ | Phase 2 |
| Browser history sync | ⭐⭐⭐⭐ | Phase 2 |
| Email/Newsletter | ⭐⭐⭐ | Phase 2 |
| Live streams | ⭐⭐⭐⭐ | Phase 3 |
| Device/Sensor | ⭐⭐⭐⭐⭐ | Phase 3+ |