# WISDOM_RESOURCE_CATALOG.md
> Catalog TOAN BO nguon luc da thu thap — Sep + Anti da qua buoc 1.
> Claude catalog day du: o dau, dung vao viec gi, trigger khi nao.
> Nguyen tac: KHONG BO SOT. Biet ro vi tri va thoi diem thuc hien.
> Last updated: 2026-05-12 | P-062

---

## NGUYEN TAC CATALOG

```
Da co = Tai san. Chua dung = Chua den luc. Khong phai rac.
Moi item deu co: Vi tri | Use case cu the | Trigger | Priority
```

---

## WING A — PRODUCTION
> `D:\Wisdom_Factory\Production\`

### FreeMoCap — Markerless 3D Motion Capture
- **Vi tri:** `D:\Wisdom_Factory\Production\freemocap\`
- **La gi:** Capture chuyen dong 3D bang webcam, khong can marker vat ly
- **Dung vao Wisdom:** Tao Avatar Agent co chuyen dong thuc (Mina/Alexander personas)
- **Use case cu the:**
  - Marketing videos cho Blueprint Marketplace (P-009)
  - Animated agent personas thay cho static icons
  - Tutorial videos co AI presenter
- **Wisdom Blueprint potential:** "AI Avatar Production Blueprint" — high-value product
- **Trigger:** Sau khi co 10 buyers + P-009 Marketplace live
- **Priority:** 🔵 PHASE 2-3
- **Lien ket:** P-022 Persona 4&5, Pixelle-Video

---

## WING B — DEFENSE (Project Aegis)
> `D:\Wisdom_Factory\Defense\`
> Toan bo Wing B: FROZEN cho den 10 Gumroad sales

### SigDigger — Radio/Signal Intelligence
- **Vi tri:** `D:\Wisdom_Factory\Defense\SigDigger\`
- **La gi:** Scan va giai ma tin hieu vo tuyen (RF)
- **Dung vao Aegis:** Detect drone signals (RF fingerprinting) truoc khi radar bat
- **Use case cu the:**
  - Passive RF detection: nhan dien drone bang tin hieu dieu khien
  - Spectrum analysis: map tan so hoat dong cua muc tieu
  - COMINT layer cho Common Operational Picture
- **Trigger:** 10 Gumroad sales → Aegis Phase 2 unlock
- **Priority:** 🧊 FROZEN (P-059)

### Map3D — Photorealistic 3D City Modeling
- **Vi tri:** `D:\Wisdom_Factory\Defense\map3d\`
- **La gi:** Dung mo hinh 3D thanh pho tu anh/LiDAR
- **Dung vao Aegis:** "Sa ban so" cho chi huy tac chien dia khong gian
- **Use case cu the:**
  - Import OpenStreetMap → render 3D terrain
  - Overlay Radar PLFM data len ban do 3D
  - Trajectory prediction cho intercept drone
- **Trigger:** Aegis Phase 2 unlock
- **Priority:** 🧊 FROZEN (P-059)

### RuView — WiFi DensePose
- **Vi tri:** `D:\Wisdom_Factory\Defense\RuView\`
- **La gi:** Nhin xuyen tuong bang song WiFi (human pose estimation)
- **Dung vao Aegis:** Phat hien nguoi trong toa nha khong can camera
- **Use case cu the:**
  - Indoor threat detection (complement Acoustic layer)
  - Perimeter monitoring khong lo mo qua wall
- **NOTE:** Privacy implications nghiem trong — chi dung trong controlled military/security context
- **Trigger:** Aegis Phase 2 unlock
- **Priority:** 🧊 FROZEN (P-059)

### HermesPy — Radar Signal Processing
- **Vi tri:** `D:\Wisdom_Factory\Defense\Aegis_DeepTech\HermesPy\`
- **La gi:** Python framework cho radar signal processing va simulation
- **Dung vao Aegis:** Simulate PLFM radar waveforms truoc khi build hardware
- **Use case cu the:**
  - Verify LFM chirp parameters (10.5GHz)
  - Test Micro-Doppler classification algorithm
  - LPI waveform design (Low Probability of Intercept)
- **Trigger:** Aegis Phase 2 unlock
- **Priority:** 🧊 FROZEN (P-059)

### Graf-PSL-LPI — LPI Radar Waveforms
- **Vi tri:** `D:\Wisdom_Factory\Defense\Aegis_DeepTech\Graf-PSL-LPI\`
- **La gi:** LPI radar waveform library (Polyphase-coded spread spectrum)
- **Dung vao Aegis:** Radar tang hinh — quet ma khong bi phat hien
- **Use case cu the:**
  - Replace basic LFM chirp bang PSL waveform
  - Giam kha nang bi intercept 40-60dB
- **Trigger:** Aegis Phase 2 unlock
- **Priority:** 🧊 FROZEN (P-059)

### Batear — Acoustic Localization
- **Vi tri:** `D:\Wisdom_Factory\Defense\Aegis_DeepTech\Batear\`
- **La gi:** Acoustic localization system (inspired by bat echolocation)
- **Dung vao Aegis:** Passive acoustic detection — Hibernation trigger
- **Use case cu the:**
  - Tram Aegis ngu dong
  - Microphone array phat hien drone sound signature (80-400Hz)
  - Wake-up trigger → activate radar + VIO
  - Giam tieu thu dien 95% khi khong co muc tieu
- **Trigger:** Aegis Phase 2 unlock
- **Priority:** 🧊 FROZEN (P-059)

### RPG SVO Pro — Visual-Inertial Odometry
- **Vi tri:** `D:\Wisdom_Factory\Defense\Aegis_DeepTech\RPG_SVO_Pro\`
- **La gi:** Visual odometry — drone tu dinh vi bang camera, khong can GPS
- **Dung vao Aegis:** GPS-denied navigation cho interceptor drone
- **Use case cu the:**
  - Moi truong GPS bi pha song → switch sang VIO mode
  - Fuse camera landmarks + IMU data → position estimate
  - Constant Bearing Pursuit khong GPS
- **NOTE:** VRAM intensive → chi activate khi GPS mat (fallback mode)
- **Trigger:** Aegis Phase 2 unlock
- **Priority:** 🧊 FROZEN (P-059)

### GeoAI — Satellite Tactical Vision
- **Vi tri:** `C:\Synapse\Research\20260512_Coffee_Morning\GeoAI\` → chuyen D: Phase 2
- **La gi:** Satellite imagery AI analysis
- **Dung vao Aegis:** Common Operational Picture (COP) — ket hop satellite + Radar
- **Use case cu the:**
  - Overlay satellite imagery len Map3D
  - Change detection: phat hien hoat dong bat thuong tu ve tinh
  - Fuse voi PLFM Radar data → unified intelligence picture
- **Trigger:** Aegis Phase 2 unlock
- **Priority:** 🧊 FROZEN (P-059)

---

## WING C — INTELLIGENCE
> `D:\Wisdom_Factory\Intelligence\`

### Gmail Backup (.eml) — Email Intelligence
- **Vi tri:** `D:\Wisdom_Factory\Intelligence\gmail_backup\`
- **La gi:** Auto-dump email ve .eml format hang ngay
- **Dung vao Wisdom:** Agent doc email → tao INBOX nodes tu dong
- **Use case cu the:**
  - KDP sales notifications → update Blueprint performance data
  - Business emails → extract decisions, action items
  - Newsletters → ingest vao knowledge graph (opt-in)
  - Sep doc Dashboard thay vi check email tung cai
- **Implementation plan:**
  1. Gmail API OAuth setup (15 phut)
  2. wisdom_email_ingest.py: doc .eml → extract text → wisdom_cleaner.py
  3. Filter by label/sender (Sep opt-in RULE-E)
  4. Tao INBOX nodes voi source_type = 'EMAIL'
  5. Them vao wisdom_cron.py --morning job
- **Trigger:** Sau Gumroad co buyer dau tien
- **Priority:** 🔵 PHASE 2 (P-060)
- **Lien ket:** wisdom_cron.py, wisdom_cleaner.py, P-013 Meeting Intelligence

---

## LEGACY RESEARCH
> `C:\Synapse\Research\20260512_Coffee_Morning\`
> Chuyen sang D: trong Phase 2

### Graphify — Code Knowledge Graph
- **La gi:** AST parser 25 ngon ngu → Knowledge Graph tu source code
- **Dung vao Wisdom:** P-010 wisdom_code_scout.py — auto-extract knowledge tu repos
- **Use case cu the:**
  - Parse GitHub repos → tao Concept/Rule nodes tu code patterns
  - 71.5x token savings khi dung graph thay vi raw files
  - Auto-rebuild graph sau moi commit
- **Trigger:** P-010 wisdom_code_scout.py, sau Phase 1
- **Priority:** 🔵 PHASE 2 (P-010-REF)

### InsForge — BaaS for Agents
- **La gi:** Backend-as-a-Service cho agents tu quan ly resources qua MCP
- **Dung vao Wisdom:** Agent self-provisioning khi scale len 120+ agents
- **Use case cu the:**
  - Agent tao database table rieng khong can Sep config thu cong
  - MCP-native resource allocation
  - Event-driven architecture cho agent coordination
- **Risk:** Concurrent write conflicts → can Event Queue (Redis/RabbitMQ)
- **Giai phap isolation:** Tenant-based namespace + write queue per agent
- **Trigger:** 50+ users, multi-tenant architecture (P-010)
- **Priority:** 🔵 PHASE 3

### CADAM — CAD/Design Automation
- **La gi:** Computer-Aided Design automation
- **Dung vao Aegis:** PCB Motor design automation (Carl Bugeja blueprint)
- **Use case cu the:**
  - Auto-generate PCB layouts tu specs
  - Validate drone frame structural integrity
- **Trigger:** Aegis Phase 2 unlock
- **Priority:** 🧊 FROZEN (P-059)

### Anthropic Financial Services Skills
- **La gi:** agent.yaml + SKILL.md standard tu Anthropic financial-services repo
- **Dung vao Wisdom:** Chuan hoa tat ca 120 agents theo format nay
- **Use case cu the:**
  - Moi agent = 1 SKILL.md (self-documenting, Git-synced)
  - Tao agent moi trong < 5 phut theo template
  - Prompt bloat giam 60%+ qua structured format
- **Implementation:**
  ```yaml
  # agent.yaml template
  name: wisdom_researcher
  version: 1.0
  skill_file: SKILL.md
  tools: [neo4j_query, qdrant_search, web_search]
  context_limit: 8000
  caveman_mode: true  # internal comms
  ```
- **Trigger:** Lam ngay vao templates/WISDOM_SKILL_TEMPLATE.md
- **Priority:** ✅ VALIDATED — lam ngay (1 session)

### Docmost — Self-hosted Knowledge Hub
- **La gi:** Open-source Notion/Confluence thay the
- **Dung vao Wisdom:** Team knowledge base, Blueprint documentation
- **Use case cu the:**
  - Agents tu dong viet Blueprint vao Docmost
  - RAG tu Docmost Markdown
  - Sep doc final output o day thay vi raw Neo4j
- **NOTE:** Hien tai Git + Markdown = du tot. Docmost them gia tri khi co team.
- **Trigger:** Sau 10 buyers, khi can cong tac nhom
- **Priority:** 🔵 PHASE 2 (P-061)

### OpenHuman — Human Behavior Dataset
- **La gi:** Open dataset ve hanh vi con nguoi
- **Dung vao Wisdom:** Training data cho Persona 5 (The Intuition) — P-022
- **Use case cu the:**
  - Pattern matching: Sep hanh dong nhu the nao trong tinh huong X?
  - Tacit knowledge extraction tu behavioral patterns
- **Trigger:** P-022 Persona 5, Phase 3
- **Priority:** 🔵 PHASE 3

---

## SUMMARY TABLE

| Resource | Wing | Vi tri | Use case chinh | Trigger | Priority |
|---|---|---|---|---|---|
| FreeMoCap | Production | D:\...\Production\ | AI Avatar cho personas | 10 buyers | 🔵 P2-3 |
| SigDigger | Defense | D:\...\Defense\ | RF drone detection | Aegis unlock | 🧊 FROZEN |
| Map3D | Defense | D:\...\Defense\ | 3D tactical map | Aegis unlock | 🧊 FROZEN |
| RuView | Defense | D:\...\Defense\ | WiFi through-wall | Aegis unlock | 🧊 FROZEN |
| HermesPy | Defense | D:\...\Defense\ | Radar simulation | Aegis unlock | 🧊 FROZEN |
| Graf-PSL-LPI | Defense | D:\...\Defense\ | LPI stealth radar | Aegis unlock | 🧊 FROZEN |
| Batear | Defense | D:\...\Defense\ | Acoustic wake trigger | Aegis unlock | 🧊 FROZEN |
| RPG SVO Pro | Defense | D:\...\Defense\ | GPS-denied nav | Aegis unlock | 🧊 FROZEN |
| GeoAI | Defense | C:\Synapse\ → D: | Satellite + Radar COP | Aegis unlock | 🧊 FROZEN |
| Gmail .eml | Intelligence | D:\...\Intelligence\ | Email → INBOX nodes | 1st buyer | 🔵 PHASE 2 |
| Graphify | Legacy | C:\Synapse\ → D: | Code → Knowledge Graph | P-010 | 🔵 PHASE 2 |
| InsForge | Legacy | C:\Synapse\ → D: | Agent self-provisioning | 50+ users | 🔵 PHASE 3 |
| CADAM | Legacy | C:\Synapse\ → D: | PCB design automation | Aegis unlock | 🧊 FROZEN |
| Anthropic Skills | Legacy | C:\Synapse\ → D: | Agent SKILL.md standard | Ngay bay gio | ✅ VALIDATED |
| Docmost | Legacy | C:\Synapse\ → D: | Team knowledge hub | 10 buyers | 🔵 PHASE 2 |
| OpenHuman | Legacy | C:\Synapse\ → D: | Persona 5 training | Phase 3 | 🔵 PHASE 3 |

---

## AEGIS COMPLETE STACK (khi unlock)

Khi trigger 10 Gumroad sales → Aegis Phase 2:

```
SENSOR LAYER:
  Batear (Acoustic) → passive detection, wake trigger
  SigDigger (RF) → drone signal fingerprinting
  PLFM Radar (Hardware) → active tracking
  GeoAI (Satellite) → strategic overview

PROCESSING LAYER:
  HermesPy → radar signal processing
  Graf-PSL-LPI → LPI stealth waveforms
  RPG SVO Pro → GPS-denied navigation (fallback)
  RuView → indoor threat detection

VISUALIZATION LAYER:
  Map3D → 3D tactical map
  CADAM → PCB motor design

PRODUCTION SUPPORT:
  FreeMoCap → AI Avatar cho briefing/reporting
```

---

## ACTION ITEMS NGAY HOM NAY

1. **Anthropic SKILL.md** → update `templates/WISDOM_SKILL_TEMPLATE.md` (30 phut)
2. **wisdom_cron.py** → test + setup Windows Task Scheduler
3. **Luu file nay** vao `docs/WISDOM_RESOURCE_CATALOG.md`
4. **Tao folder structure tren o D:** khi co thoi gian:
   ```
   D:\Wisdom_Factory\
   ├── Production\  (FreeMoCap)
   ├── Defense\     (Aegis stack)
   └── Intelligence\ (Gmail backup)
   ```

---

*P-062 | 2026-05-12 | Catalog tu CLAUDE_STRATEGIC_HANDOVER_20260512.md*
*Nguyen tac: Khong bo sot. Biet ro vi tri va thoi diem.*
