# CLAUDE.md — Wisdom Factory: Living Brain & Operating Rules
> **Doc version:** 2026-05-03 (Tong hop 3 nguon: claude.md + CLAUDE.md Phase 0 + Antigravity Senior Architect)
> **Nguyen tac:** Chi APPEND, khong bao gio REPLACE. Moi buoi lam viec -> append section moi.
> **Bat buoc:** Doc file nay TRUOC KHI bat dau bat ky task nao.

---

## 1. PROJECT CONTEXT

- **Project:** Wisdom Factory — Global Super-Intelligence Ecosystem
- **Phase hien tai:** Phase 2 (Neo4j + Qdrant + Agent Pipeline + Auto Scout)
- **Stack chinh:** Python, Neo4j, Qdrant, Ollama (local), FastAPI, watch-cli
- **Thu muc goc:** `/wisdom/`
- **Nguoi chiu trach nhiem:** Sep Thang (Human in the loop — moi quyet dinh quan trong)

---

## 2. KIEN TRUC TONG QUAN (5 LAYERS — Antigravity Standard)

```
Layer 1: Ingestion      -> wisdom_ingest.py + wisdom_upload.py
Layer 2: Memory/Graph   -> wisdom_graph.py (Neo4j — SOURCE OF TRUTH)
Layer 3: Query/Search   -> wisdom_query.py (Qdrant — SEARCH INDEX)
Layer 4: Cognitive      -> wisdom_agent.py (Devil's Advocate + Validation)
Layer 5: Factory        -> wisdom_blueprint.py
```

### Nguyen tac kien truc da thong nhat (2026-05-03)

**[RULE-A] Neo4j la SOURCE OF TRUTH — Qdrant la SEARCH INDEX**
- Moi write: Neo4j TRUOC -> lay node_id -> write Qdrant voi node_id lam payload
- Moi delete/update: Neo4j first -> propagate sang Qdrant bang node_id
- Khong bao gio write Qdrant truoc Neo4j

**[RULE-B] Moi Neo4j KnowledgeNode PHAI co du 6 fields:**
```python
{
  "id": "uuid",
  "title": "...",
  "content_hash": "md5...",
  "trust_score": 0.85,          # 0.0 - 1.0
  "decay_lambda": 0.003,        # tech=0.003, math~0, news=0.05
  "valid_from": "2026-05-03",
  "valid_until": None,           # None = khong het han
  "epistemic_status": "PENDING", # PENDING|VERIFIED|CONTESTED|SHADOW|DEPRECATED
  "cultural_context": "GLOBAL",  # GLOBAL|REGION_SPECIFIC
  "source_type": "TACIT"         # ACADEMIC|TACIT|SYNTHETIC
}
```

**[RULE-C] Temporal Decay Formula (Antigravity):**
```python
import math
def trust_score(base_score: float, age_days: int, decay_lambda: float) -> float:
    return base_score * math.exp(-decay_lambda * age_days)
# decay_lambda theo domain:
# AI/Tech paper: 0.003 | Math theorem: ~0 | Market news: 0.05
```

**[RULE-D] Adversarial Validation — ASYNC, khong blocking:**
- PENDING -> vao DB ngay, dung duoc cho personal query
- Background job chay Devil's Advocate Agent (wisdom_validator.py)
- Chi VERIFIED moi vao Global Knowledge Pool
- Khong bao gio block ingest pipeline cho validation

**[RULE-E] Tacit Extraction — PHAI explicit opt-in, khong auto-push:**
- Khong tu dong push private knowledge len Global Pool
- Hien popup preview + "Dong gop nhan 50 Wisdom Credit?" [Co] [Khong]
- Chi xu ly sau khi user xac nhan

**[RULE-F] EpistemicConflict — Khong bao gio xoa khi mau thuan:**
```cypher
// Neu 2 nguon mau thuan nhau -> tao Contradiction node
(:KnowledgeNode)-[:CONTRADICTS {confidence_diff: 0.02}]->(:KnowledgeNode)
// Tat ca deu giu, gan nhan [CONTESTED]
// Tra ve cho user: "Ton tai tranh luan hoc thuat ve diem nay"
```

**[RULE-G] Qdrant Collections — Phan vung ro rang:**
```
wisdom_public          -> Knowledge da qua Layer 3 validation (VERIFIED)
wisdom_private_{uid}   -> Du lieu raw chua anonymize (TTL: 30 ngay)
wisdom_shadow          -> Hypothesis nodes cho cho bang chung
```

---

## 3. CHECKLIST TRUOC KHI VIET CODE (BAT BUOC)

- [ ] Doc toan bo ERROR PATTERN REGISTRY (Section 4)
- [ ] Voi moi file xu ly text -> ap dung `strip_emoji()` ngay tu dau
- [ ] Voi moi `open()` -> luon co `encoding='utf-8'`
- [ ] Voi moi DB call -> boc trong `try/except`
- [ ] Khong hardcode API key — dung `os.environ.get()`
- [ ] Subprocess tren Windows -> dung Git Bash exe (xem EP-005)
- [ ] Write DB -> Neo4j TRUOC, Qdrant sau (RULE-A)
- [ ] Moi KnowledgeNode -> du 6 required fields (RULE-B)
- [ ] Sau khi fix loi -> chay: `python wisdom_error_watcher.py --report "ten loi" --file "file.py" --fix "mo ta"`

---

## 4. ERROR PATTERN REGISTRY

> Auto-managed boi `wisdom_error_watcher.py` | Khong chinh sua thu cong.
> Sau khi fix bat ky loi nao -> phai chay watcher de ghi vao day.

---

### [EP-001] EP-001 verified
- **Phát hiện lần đầu:** 2026-05-03
- **Cập nhật lần cuối:** 2026-05-03 13:07
- **Severity:** LOW
- **File phát hiện:** wisdom\core\wisdom_upload.py
- **Mô tả:** Manually verified - no issue
- **Fix đã áp dụng:** Already fixed
- **Áp dụng cho:** Mọi file `*.py`
- **Status:** ✅ Fixed & Documented

```python

```

---
### [EP-002] EP-002 verified
- **Phát hiện lần đầu:** 2026-05-03
- **Cập nhật lần cuối:** 2026-05-03 13:07
- **Severity:** LOW
- **File phát hiện:** wisdom\core\wisdom_upload.py, wisdom\core\wisdom_api.py
- **Mô tả:** Manually verified - no issue
- **Fix đã áp dụng:** Already fixed
- **Áp dụng cho:** Mọi file `*.py`
- **Status:** ✅ Fixed & Documented

```python

```

---
### [EP-003] No Exception Handling in DB Calls
- **Severity:** HIGH
- **Mo ta:** Goi Neo4j/Qdrant khong co try/except -> crash toan bo pipeline
- **Status:** Preventive Rule

```python
try:
    results = client.query_points(
        collection_name=COLLECTION,
        query=embedding,
        limit=top_k,
        with_payload=True
    )
    for r in results.points:
        ...
except Exception as e:
    logger.error(f"Qdrant query failed: {e}")
    results = None
```

---

### [EP-004] No Exception Handling in DB calls
- **Phát hiện lần đầu:** 2026-05-03 08:44
- **Cập nhật lần cuối:** 2026-05-03 13:02
- **Severity:** HIGH
- **File phát hiện:** wisdom\core\wisdom_ingest.py, wisdom\core\wisdom_query.py, wisdom\core\wisdom_upload.py, wisdom_query.py, wisdom_upload.py
- **Mô tả:** Gọi Neo4j/Qdrant không có try/except gây crash toàn bộ pipeline
- **Fix đã áp dụng:** Bọc tất cả DB calls trong try/except với fallback
- **Áp dụng cho:** Mọi file `*.py`
- **Status:** ✅ Fixed & Documented

```python
try:
    result = collection.query(...)
except Exception as e:
    logger.error(f'DB query failed: {e}')
    result = []
```

---
### [EP-005] Subprocess tren Windows — Git Bash Required
- **Severity:** HIGH
- **Mo ta:** subprocess.run(["command"]) va shell=True deu FAIL tren Windows
- **Root cause:** Windows khong biet Git Bash PATH; shell=True dung cmd.exe
- **Status:** Fixed & Documented

```python
# SAI - ca 2 cach deu fail tren Windows
subprocess.run(["watch", url])
subprocess.run(f"watch {url}", shell=True)

# DUNG - luon dung duong dan tuyet doi den bash.exe
BASH_EXE = "C:/Program Files/Git/bin/bash.exe"
subprocess.run([BASH_EXE, "-c", f"watch {url}"])
subprocess.run([BASH_EXE, "-c", f"python '{script_path}' '{arg}'"])

# Ap dung cho: watch-cli, transcribe, va moi Git Bash command tu Python
```

---

### [EP-006] Qdrant Client API Thay Doi (v1.16+)
- **Severity:** HIGH
- **Mo ta:** client.search() deprecated -> dung client.query_points()
- **Status:** Fixed & Documented

```python
# SAI (deprecated)
results = client.search(
    collection_name=COLLECTION,
    query_vector=embedding,
    limit=5
)

# DUNG (v1.16+)
results = client.query_points(
    collection_name=COLLECTION,
    query=embedding,          # khong phai query_vector
    limit=top_k,
    with_payload=True
)
for r in results.points:     # .points (khong phai list truc tiep)
    print(r.payload)
```

---

### [EP-007] Facebook Video Can Cookies
- **Severity:** MEDIUM
- **Mo ta:** FB video thuong login-walled -> watch-cli khong download duoc anonymous
- **Status:** Known Issue — Workaround documented

```bash
# Workaround: Export cookies tu Chrome
# Extension: "Get cookies.txt LOCALLY"
watch <FB_URL> --cookies ~/cookies.txt

# TODO: Build auto-cookie helper cho FB ingestion pipeline
```

---

### [EP-008] Scanned PDF — OCR Pipeline 2 Buoc
- **Severity:** MEDIUM
- **Mo ta:** PyPDF2 chi doc text-based PDF. Scanned PDF tra ve empty string.
- **Status:** Fixed & Documented

```python
import pytesseract
from pdf2image import convert_from_path

# Thiet lap duong dan tuyet doi tren Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin"

def extract_pdf_text(path: str) -> str:
    # Buoc 1: Thu text-based truoc
    try:
        import PyPDF2
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = " ".join(page.extract_text() or "" for page in reader.pages)
        if len(text.strip()) > 100:
            return text
    except Exception:
        pass

    # Buoc 2: Fallback OCR cho scanned PDF
    images = convert_from_path(path, poppler_path=POPPLER_PATH)
    return "\n".join(pytesseract.image_to_string(img) for img in images)
```

---

### [EP-009] Windows Subprocess Output — Carriage Return Strip
- **Severity:** MEDIUM
- **Mo ta:** Python tren Windows output \r\n thay vi \n -> timestamps va gia tri bi loi neu khong strip
- **Status:** Fixed & Documented

```python
# Trong Python:
result = subprocess.run([BASH_EXE, "-c", cmd], capture_output=True, text=True)
output = result.stdout.replace('\r\n', '\n').replace('\r', '')

# Trong Bash script:
ts="${ts%%$'\r'*}"   # Strip carriage return tu Python output
```

---

### [EP-010] wisdom_api.py — Cac Loi Khi Test Server
- **Severity:** HIGH
- **File:** wisdom_api.py
- **Mo ta:** Cac loi thuong gap khi chay wisdom_api.py lan dau
- **Status:** Documented — Apply khi gap

```python
# LOI 1: Import error khi chua cai beautifulsoup4/requests
# Fix: pip install beautifulsoup4 requests

# LOI 2: Port 8000 conflict
# Fix: doi PORT = 8001 hoac kill process dang dung port
import socket
def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

# LOI 3: Subprocess timeout khi ingest video qua dai
# Fix: tang timeout hoac chay ingest rieng
result = subprocess.run([...], timeout=600)  # 10 phut thay vi 300

# LOI 4: encoding='utf-8' thieu trong subprocess capture
result = subprocess.run([...], capture_output=True, text=True, encoding='utf-8')

# LOI 5: CORS error khi bookmarklet goi API
# Da fix trong wisdom_api.py: Access-Control-Allow-Origin: *
```

---

## 5. TOOLS & QUICK COMMANDS

```bash
# Scan project tim loi moi
python wisdom_error_watcher.py --scan

# Bao cao loi vua fix
python wisdom_error_watcher.py --report "ten loi" --file "file.py" --fix "mo ta fix"

# Chay background watcher (dev session)
python wisdom_error_watcher.py --watch

# Kiem tra Docker services
docker-compose ps
docker-compose up -d

# Kiem tra Ollama models
ollama list

# Test Qdrant
curl http://localhost:6333/collections

# Test Neo4j
curl http://localhost:7474
```

---

## 6. INFRASTRUCTURE — TRANG THAI DA XAC NHAN

### Models (Ollama local)
- `llama3.1:8b` — reasoning, coding, Q&A phuc tap
- `gemma3:4b` — task nhe, volume cao
- `nomic-embed-text` — embedding cho Qdrant (vector size: 768)
- Endpoint: `http://localhost:11434`

### Docker Services
- **Neo4j 5.26.0:** bolt://localhost:7687 | browser: http://localhost:7474
  - Auth: neo4j / password123
  - Volume: neo4j_data
- **Qdrant 1.17.1:** http://localhost:6333
  - Collection mac dinh: wisdom_knowledge (768 dims, COSINE)
  - Volume: qdrant_data

### Files Hien Tai
```
wisdom/core/wisdom_ingest.py   -> Ingest tu URL (YT/FB/TikTok)
wisdom/core/wisdom_upload.py   -> Upload file (PDF/Word/Audio/Video/Image)
wisdom/core/wisdom_query.py    -> Search + Answer (Vector + Graph + LLM)
wisdom/core/wisdom_api.py      -> API server nhan URL tu bookmarklet (port 8000)
wisdom_error_watcher.py        -> Auto-scan loi + ghi vao CLAUDE.md
```

---

## 7. DECISION LOG

| Date | Decision | Reason |
|------|----------|--------|
| Phase 0 | Ollama local thay Gemini | Gemini free tier bi block tai VN |
| Phase 0 | gemma3:4b + llama3.1:8b | 16GB RAM, chay tot local |
| Phase 1 | FastAPI + Python cho Web UI | Nhe, khong can Node.js, phu hop Local-first |
| Phase 2 | Neo4j la source of truth | Qdrant chi la search index, tranh data lech nhau |
| Phase 2 | Qdrant query_points() | client.search() deprecated tu v1.16 |
| Phase 2 | Adversarial Validation async | Khong block ingest pipeline, UX tot hon |
| Phase 2 | Tacit Extraction phai opt-in | Phap ly + tin tuong user, tranh auto-push |
| Phase 2 | EpistemicConflict node | Khong xoa khi mau thuan, giu ca 2 nguon + [CONTESTED] |

---

## 8. ROADMAP PHASE 2 (Da thong nhat 2026-05-03)

### Sprint 1 — Fix Foundation (Tuan 1)
- [ ] Them `node_id` lam cau noi Neo4j <-> Qdrant (fix data drift)
- [ ] Them 6 required fields vao Neo4j schema (RULE-B)
- [ ] Them `status: PENDING|VERIFIED` workflow
- [ ] Migration script cho data cu
- [ ] EpistemicConflict node type + CONTRADICTS relationship

### Sprint 2 — Auto Scout Pipeline (Tuan 2)
- [ ] `wisdom_scout.py` — background job theo schedule
- [ ] Nguon uu tien: YouTube channels, RSS feeds, GitHub repos
- [ ] Route vao wisdom_ingest.py (khong viet lai pipeline)
- [ ] `credibility_score` dua tren domain + engagement

### Sprint 3 — Devil's Advocate Agent (Tuan 3)
- [ ] `wisdom_validator.py` — doc queue PENDING nodes (async)
- [ ] Cross-check fact bang llama3.1:8b local
- [ ] Conflict detection voi knowledge da co trong Neo4j
- [ ] Promote PENDING -> VERIFIED hoac flag human review

---

## 9. BAI HOC & LICH SU (Append-only)

### [2026-05-01] Phase 0 Complete
- Stack confirmed: Ollama + Neo4j + Qdrant + watch-cli + 3 pipelines
- Gemini free tier bi block tai VN -> chuyen sang Ollama local
- watch-cli can patch nhieu buoc tren Windows (xem EP-005, EP-009)

### [2026-05-02] Phase 1 — Upload + API
- wisdom_upload.py: ho tro PDF/Word/Audio/Video/Image/EPUB
- Scanned PDF can OCR 2 buoc (xem EP-008)
- wisdom_api.py: API server nhan URL tu bookmarklet

### [2026-05-03] Thong nhat Architecture voi Antigravity
- Neo4j = source of truth (RULE-A)
- 6 required fields tren moi KnowledgeNode (RULE-B)
- Temporal Decay Formula theo domain (RULE-C)
- Adversarial Validation phai async (RULE-D)
- Tacit Extraction phai explicit opt-in (RULE-E)
- EpistemicConflict: giu ca 2 nguon + [CONTESTED] (RULE-F)
- Qdrant 3 collections phan vung ro rang (RULE-G)

---

*CLAUDE.md — Tong hop 3 nguon: claude.md + CLAUDE.md Phase 0 + Antigravity Senior Architect*
*Chi APPEND, khong bao gio REPLACE | Doc truoc khi code*
## Bài học & Kinh nghiệm (2026-05-03 — Buổi tối)

### [BÀI HỌC 11] Emoji Encoding — Lỗi lặp lại do thiếu propagation
- **Files bị ảnh hưởng:** `wisdom_ingest.py` → `wisdom_query.py`
- **Root cause:** Fix lỗi ở 1 file nhưng không apply sang file cùng loại
- **Fix:** Dùng `strip_emoji()` ở MỌI file nhận `text: str` từ bên ngoài

```python
import re
def strip_emoji(text: str) -> str:
    emoji_pattern = re.compile('[' 
        u'\U0001F600-\U0001F64F'
        u'\U0001F300-\U0001F5FF'
        u'\U0001F680-\U0001F6FF'
        u'\U0001F1E0-\U0001F1FF'
        u'\U00002600-\U000027BF'
        u'\U0001F900-\U0001F9FF'
        ']+', flags=re.UNICODE)
    return emoji_pattern.sub('', text)
```

- **Checklist propagate bắt buộc sau mỗi fix:**
  - [ ] wisdom_ingest.py
  - [ ] wisdom_query.py
  - [ ] wisdom_upload.py
  - [ ] wisdom_agent.py (Phase 2)
  - [ ] wisdom_blueprint.py (Phase 2)

### [NGUYÊN TẮC MỚI] Log lỗi ngay — không để mất
- Sau mỗi buổi làm việc → append bài học vào CLAUDE.md **trước khi đóng máy**
- Conversation Claude.ai đôi khi bị ghi thiếu → không phụ thuộc vào việc tìm lại chat
- Thói quen: fix xong → ghi luôn → không cần nhớ


## 🔴 ERROR PATTERN REGISTRY (Auto-generated)

> ⚠️ Section này được tự động quản lý bởi wisdom_error_watcher.py
> Không chỉnh sửa thủ công.

### [EP-001] EP-001 verified
- **Phát hiện lần đầu:** 2026-05-03
- **Cập nhật lần cuối:** 2026-05-03 13:07
- **Severity:** LOW
- **File phát hiện:** wisdom\core\wisdom_upload.py
- **Mô tả:** Manually verified - no issue
- **Fix đã áp dụng:** Already fixed
- **Áp dụng cho:** Mọi file `*.py`
- **Status:** ✅ Fixed & Documented

```python

```

---
---

## 10. BUSINESS STRATEGY (Thong nhat 2026-05-03)

### Nguyen tac chon tinh nang build
> Moi tinh nang phai tra loi duoc: "Tao ra dong tien o giai doan nao?"
> Neu khong tra loi duoc -> khong build.

---

### NHOM A — Lam ngay (Phase 1-2, co the tao cash flow trong 6 thang)

**A1. Affiliate System**
- User refer nguoi moi dang ky -> nhan % subscription phi
- Wisdom khong can tu marketing, users tu di tim khach hang
- Chi phi acquisition gan bang 0
- Uu tien: CAO NHAT

**A2. Blueprint Marketplace**
- Users dong goi automation workflow thanh Blueprint
- Ban tren Wisdom Store
- Owner thu 18% commission moi giao dich
- Uu tien: CAO

**A3. Business Storefront (co ban)**
- Moi user co 1 trang storefront ca nhan
- Link den san pham/khoa hoc/dich vu ben ngoai
- Wisdom lam trung gian tin cay, tang conversion
- Uu tien: CAO

**A4. Learning Path Monetization** <- [MOI - chua co trong tai lieu Antigravity]
- Wisdom tu generate lo trinh hoc sieu ca nhan hoa dua tren knowledge graph
- Dua tren diem mu kien thuc cua tung user
- De ban nhat cho beachhead market MMO/Affiliate
- Ly do: MMO community luon san sang tra tien de hoc kiem tien nhanh hon
- Uu tien: CAO

---

### NHOM B — Lam sau khi co 500+ users (Phase 2-3)

**B1. App Store voi AI Review**
- Users tao Cognitive Apps (Blueprint + Mental Model + Tool)
- AI tu dong kiem duyet chat luong truoc khi len Store
- Owner thu 15-30% "App Store Tax" moi giao dich
- Network effect: nhieu Developer -> nhieu App -> nhieu User -> vong lap

**B2. B2B API Licensing**
- Ban API truy cap cap doanh nghiep vao Tacit Knowledge tong hop
- Target: quy dau tu, tap doan cong nghe, R&D teams
- Tiem nang: hang trieu USD/nam
- Dieu kien: phai co du luong data da verify truoc

**B3. Mental Model Marketplace**
- Users niem yet "Mo hinh tu duy" len Store
- DIEU KIEN QUAN TRONG: phai co performance tracking truoc
- Neu khong verify chat luong -> refund -> mat uy tin platform
- Chi mo sau khi co rating system hoan chinh

---

### NHOM C — Khong lam voi (Rui ro cao / Qua som)

**C1. DePIN GPU Sharing**
- Can critical mass hang nghin nodes moi co y nghia
- User base ban dau qua nho -> overhead khong can thiet
- Xem xet lai Phase 3+

**C2. Tokenomics / ICO / IDO**
- Phap ly Viet Nam hien tai: vung xam, rui ro cao
- Co the block toan bo du an neu lam sai thoi diem
- Chi xem xet khi co legal framework ro rang
- De cuoi cung trong roadmap

---

### Pricing da chot (2026-05-01)
- Founding: $99/year (100 nguoi dau)
- Standard: $199/year
- MMO Pro: $499/year (teams)
- Enterprise: $999+/year

### Beachhead Market
- Vietnam first -> SEA -> Global
- MMO/Affiliate community: san sang tra tien de hoc kiem tien nhanh hon
- Da ngon ngu tu kien truc dau tien

### Muc tieu quy mo
- Phase 1: 50 Founding Members
- Phase 2: 500 Standard users
- Phase 3: 2,000+ global users

---

### So sanh mo hinh (da thong nhat)
| Mo hinh | Kha thi som | Rui ro | Uu tien |
|---------|-------------|--------|---------|
| Affiliate System | Yes | Thap | Phase 1 |
| Blueprint Marketplace | Yes | Thap | Phase 1 |
| Business Storefront | Yes | Thap | Phase 1 |
| Learning Path | Yes | Thap | Phase 1 |
| App Store Tax | Trung binh | Trung binh | Phase 2 |
| B2B API | Kho | Trung binh | Phase 2-3 |
| Mental Model Rent | Kho | Cao | Phase 2-3 |
| DePIN GPU | Rat kho | Cao | Phase 3+ |
| Tokenomics | Rat kho | Rat cao | Cuoi cung |
---

## 11. OPEN SOURCE INTELLIGENCE & ENHANCEMENT (Thong nhat 2026-05-03)

### Triet ly cot loi
"Dung tren vai nguoi khong lo" — hoc tu tinh hoa open source,
build phien ban tot hon, dep hon, hieu qua hon.
Day chinh xac la the manh cua Wisdom.

Vi du thuc te:
- Apple khong phat minh smartphone -> lam tot hon
- Google khong phat minh search -> lam tot hon
- Wisdom khong phat minh RAG -> lam tot hon cho thi truong VN/SEA

### wisdom_code_scout.py — Module moi (Phase 2, Layer 3)

Luong hoat dong:
- GitHub / HuggingFace / ProductHunt / Reddit
- [Repo Scanner] — filter: stars > 100, license: MIT/Apache/BSD
- [AST Parser] — extract: functions, classes, design patterns
- [Ollama llama3.1:8b] — phan tich: bai toan, thuat toan, diem yeu, co hoi cai tien
- [Enhancement Generator] — de xuat phien ban tot hon
- [Neo4j] — KnowledgeNode {source_type: "open_source_intel"}
- [Qdrant] — searchable by: functionality, pattern, use_case

### RULE — License Filter (BAT BUOC)
- Chi ingest: MIT / Apache 2.0 / BSD / CC
- Khong ingest: GPL, AGPL, proprietary, no-license
- Check license TRUOC khi ingest bat ky repo nao

### 3 buoc chuan khi xu ly open source repo
1. HOC — hieu thuat toan, design pattern, logic kinh doanh
2. PHAN TICH — tim diem yeu, han che, co hoi cai tien
3. BUILD BETTER — Wisdom tao phien ban moi: nhanh hon, dep hon, phu hop VN/SEA

### Khong lam
- Khong copy code nguyen xi vao Wisdom
- Khong claim ownership y tuong lay tu repo nguoi khac
- Khong ingest repo khong ro license

### Ung dung thuc te
- Scan GitHub hang tuan -> cap nhat best practices moi nhat
- Phat hien tools AI moi tren HuggingFace -> analyze ngay
- Reddit/ProductHunt -> bat xu huong som nhat thi truong
- Output -> Blueprint Store: "Phien ban Wisdom cua tool X"
### Tools & Links da research (2026-05-03)

TIER 1 — Public Scraping:
- Name: facebook-scraper
- GitHub: github.com/kevinzg/facebook-scraper
- Stars: 2647 | License: MIT | Language: Python
- Install: pip install facebook-scraper
- Dung cho: public pages, groups, posts, comments
- Note: pass cookies="cookies.txt" cho noi dung can login

- Name: facebook-page-scraper  
- GitHub: github.com/SSujitX/facebook-pages-scraper
- Stars: 300+ | License: MIT | Language: Python
- Install: pip install facebook-page-scraper
- Dung cho: page info, followers, engagement stats
- Note: khong can webdriver, khong can API key

- Name: facebook-graphql-scraper
- GitHub: github.com/FaustRen/facebook-graphql-scraper
- Stars: dang tang | Language: Python + Selenium
- Dung cho: posts theo khoang thoi gian, reaction count
- Note: dung GraphQL API cua FB, on dinh hon HTML scraping

TIER 2 — Saved/Liked Behavior:
- Name: fb-scraping-tools
- GitHub: github.com/hubertlacote/fb-scraping-tools
- Dung cho: lay tat ca posts user da liked, pages user follow
- Note: can cookies, doi ngon ngu FB sang English (UK) truoc

TIER 3 — Chrome Extension (tu build):
- Wisdom bookmarklet hien co: wisdom_bookmarklet.html
- Nang cap len full Chrome Extension de capture real-time behavior
- Tham khao: github.com/The-Web-Scraping-Playbook/awesome-facebook-scrapers
  (danh sach curated tat ca FB scrapers, update thuong xuyen)

TIKTOK:
- Tuong tu FB Tier 1, dung: github.com/davidteather/TikTok-Api
- Hoac tich hop vao watch-cli hien co (da ho tro TikTok URL)
### [EP-012] IndentationError khi paste code nhieu phan vao VS Code
- Severity: MEDIUM
- Trieu chung: def function bi indent sai, nam trong block khac
- Root cause: Paste tung phan rieng le -> indent bi lech
- Fix: python -c "content.replace(wrong_indent, correct_indent)"
- Phong ngua: Paste code 1 lan duy nhat, khong chia nhieu phan
- Status: Fixed & Documented
### [TRANG THAI] wisdom_payment.py — DONE & TESTED (2026-05-03)
- WisdomLedger connected Neo4j thanh cong
- create_user: tao user + auto generate affiliate_code
- add_credit: cong credit vao vi
- process_affiliate_commission: $199 x 20% = $39.8 chinh xac
- request_payout: check minimum $50 dung
- get_user_summary: tra ve day du balance/earned/spent/withdrawn
- Test passed 100% khi Docker (Neo4j + Qdrant) dang chay
- NOTE: Phai chay docker-compose up -d truoc khi test
### [EP-013] lxml_html_clean missing (2026-05-03)
- Trieu chung: ImportError khi import facebook_scraper
- Fix: pip install lxml_html_clean
- Ap dung: moi lan cai facebook-scraper tren moi truong moi

### [NOTE] wisdom_fb_ingest.py — cho cookies
- File da build xong, syntax OK
- FB block anonymous tu 2023 -> can cookies.txt
- Khi co cookies: python wisdom_fb_ingest.py --page "vnexpress.net" --limit 20 --cookies cookies.txt
- Cai extension: "Get cookies.txt LOCALLY" tren Chrome Web Store
## 13. EROCA 4-LAYER ARCHITECTURE (Thong nhat 2026-05-03)

### 4 Tang du lieu
INBOX -> RAW -> WIKI -> OUTBOX

TANG 1 — INBOX (Triage Engine)
- epistemic_status: UNVERIFIED (mac dinh khi moi vao)
- Auto-Deduplication: hash URL/content truoc khi insert
  content_hash = SHA-256(url + content[:500])
  Neu hash da ton tai -> merge vao node cu, khong tao moi
- Bouncer Agent (async, khong blocking):
  - Rule-based tagging ngay lap tuc: domain, keyword
  - Ollama llama3.1:8b chay sau 5 phut: niche, urgency, emotion
  - Tags: niche(MMO/Tech/Business), urgency(high/med/low)

TANG 2 — RAW (Immutable Ledger)
- Khong bao gio sua node RAW sau khi tao
- Bat buoc: sha256_checksum + ingested_timestamp
- Vector hoa ngay lap tuc vao Qdrant (collection: wisdom_raw)
- Cho phep Semantic Search tren raw data chua tinh luyen
- Schema:
  sha256_checksum: str   <- SHA-256(full_content)
  ingested_at: ISO       <- timestamp chinh xac
  source_url: str        <- nguon goc bat bien
  raw_content: str       <- noi dung goc, khong chinh sua

TANG 3 — WIKI (Digested Forge)
- Chi len WIKI khi: ripeness_score >= 0.7
  + Da qua Devil's Advocate Agent (Red-Teaming)
  + epistemic_status: VERIFIED
- Node types: Concept | Rule | Case_Study | Framework | Insight
- Dynamic Decay:
  MMO tactics (FB/TT algo) -> decay_lambda = 0.05 (outdated nhanh)
  Core principles -> decay_lambda = 0.001 (ben vung)
  Khi trust_score < 0.4 -> tu dong flag OUTDATED -> trigger scout

TANG 4 — OUTBOX (Storefront / Blueprint Factory)
- Dieu kien tao Blueprint:
  minimum: 3 Verified_Rule + 1 Case_Study + 1 Framework
- Blueprint JSON structure:
  {id, title, description, wiki_nodes[], price,
   target_audience, value_flywheel, created_at}
- Phase 1: tao Blueprint JSON
- Phase 2: auto-generate UI (chua build)
- Ket noi truc tiep voi wisdom_payment.py (da co)

### Diem nghen can chu y
1. RAW -> WIKI: can ripeness_score ro rang, khong de subjective
2. WIKI -> OUTBOX: can minimum node condition, khong de Blueprint rong

### Files can update
- wisdom_ingest.py: them SHA-256 + dedup check
- wisdom_upload.py: them SHA-256 + dedup check
- wisdom_fb_ingest.py: them SHA-256 + dedup check
- wisdom_blueprint.py: tao moi cho OUTBOX layer
## 14. WISDOM CONSTITUTION (Hien phap Kien truc Loi)
Last updated: 2026-05-03
Nguon: EROCA + GBrain + Khang's AI OS + Antigravity

### 3 Triet ly van hanh bat bien
1. Tu choi Collector's Fallacy: Wisdom la Digestion Engine, khong phai kho bai
2. AI Interrogation: Chi chay khi RAW->WIKI, khong phai luc capture
   (Capture First = Friction 0, Interrogation = truoc khi VERIFY)
3. Data Gravity > AI Models: Neo4j/Qdrant la SSOT
   LLM chi la engine — co the doi bat cu luc nao

### 4-Layer Forge — Neo4j Schema chot
INBOX: InboxItem {epistemic_status: UNVERIFIED, sha256, urgency, niche}
RAW:   RawSource {content_hash SHA-256, immutable, qdrant_vector_id}
WIKI:  Concept|Rule|CaseStudy {trust_score, decay_lambda, red_team_score,
       ripeness_score >= 0.7 de len WIKI}
OUTBOX: Blueprint {min 3 Verified_Rule + 1 CaseStudy, price, status}

### Relationships
(InboxItem)-[:PROMOTED_TO]->(RawSource)
(RawSource)-[:DISTILLED_TO]->(Concept|Rule|CaseStudy)
(Rule)-[:SUPPORTS|CONTRADICTS]->(Rule)
(Rule)-[:COMPILED_INTO]->(Blueprint)
(Blueprint)-[:DERIVED_FROM]->(RawSource)

### 2 Vu khi sat thu can build (tu Khang's AI OS)
1. Self-Improving Loop:
   - Detect hanh vi lap lai >= 3 lan
   - Auto popup: "Dong goi thanh Blueprint?"
   - Nguon Blueprint tu dong cho Wisdom Store
   - File: wisdom_behavior_tracker.py (chua build)

2. Automation CRON Strip:
   - 07:00 Auto-Scout GitHub trending
   - 20:00 Dynamic Decay cleanup
   - Every 30min Heartbeat check
   - File: wisdom_cron.py (chua build)

### Dieu chinh so voi de xuat goc
- AI Interrogation: chi o buoc RAW->WIKI (khong phai luc capture)
- Zero-Config UI: Phase 2 (sau khi Blueprint JSON xong)
- Glassmorphism UI: Phase 2
## 15. UI/UX & INTERACTION CONSTITUTION (Thong nhat 2026-05-05)
> Tong hop tu: Master Proposal (Antigravity) + Nature-Centric Vision (Sep Thang) + Claude Ecosystem Analysis

### Visual Soul — Nature-Centric Design Language
- Triet ly: Thien nhien + Cong nghe = Tin cay (khong giong bat ky AI tool nao hien tai)
- KHONG dung anh literal (rung/bien/vu tru) -> dung organic motion graphics
- Mau sac chinh: Deep forest green + warm amber + cream
- Khong dung dark blue/purple generic nhu ChatGPT, Notion AI
- Motion: Nodes breathing animation, fluid particles lay cam hung thien nhien
- Typography: Serif (wisdom/quote content) + Sans-serif (data/UI)
- Am thanh (Phase 3): Tieng chuong nhe khi node duoc VERIFIED

### Interaction Layer — Minimalist UI Rules
- Buttons CHI xuat hien khi can thiet — khong "o nhiem" khong gian nghe thuat
- Context Boards: Glassmorphism (blur backdrop, mo ao nhu kinh)
- Trang thai:
  Default  -> Background organic + Graph nodes floating
  Hover    -> Context board fade in
  Action   -> Minimal buttons appear
  Done     -> Fade out hoan toan
- Nguyen tac: UI khong tranh gianh su chu y voi content

### AskUserQuestion — UI-driven Logic (QUAN TRONG)
Wisdom KHONG chi tra loi. Wisdom la Partner co quyen "chat van".
Backend tra ve JSON schema, Frontend tu render UI:

{
  "type": "conflict_resolution | cadence_assignment | promote_confirm | context_needed",
  "message": "Kien thuc nay mau thuan voi Rule X, Sep muon:",
  "options": [
    {"label": "Giu ca hai [CONTESTED]", "value": "keep_both",  "color": "amber"},
    {"label": "Ghi de Rule cu",         "value": "override",   "color": "red"},
    {"label": "Bo qua lan nay",         "value": "skip",       "color": "gray"}
  ],
  "slider": null,
  "multi_choice": false
}

Cac truong hop kich hoat AskUserQuestion:
- Node chuan bi thang cap RAW -> WIKI (ripeness check)
- Conflict detected giua 2 nodes (EpistemicConflict)
- Cadence chua duoc phan loai ro rang
- Trust score qua thap can human review
UI cam giac: User dang dieu hanh empire, khong phai dung chatbot

### Interactive Artifacts Engine (MOI — P-017)
Wisdom KHONG chi tra ve text thuan. Output phai tuong tac duoc.
Output types:
- Chart     -> bar/line/pie chart tu Neo4j data
- Table     -> sortable, filterable knowledge table
- Dashboard -> blueprint performance, decay report
- Mini-tool -> spaced repetition card, conflict resolver

Backend JSON response format:
{
  "type": "artifact",
  "artifact_type": "chart | table | dashboard | card",
  "data": {...},
  "config": {"title": "...", "x_axis": "...", "color_scheme": "nature"}
}

Vi du use cases:
- "Show knowledge decay report" -> bar chart decay by domain
- "Blueprint sales this week"   -> revenue dashboard
- "Conflict map"                -> interactive graph
- "Review due today"            -> spaced repetition cards

### Blueprints as Skills (Cap nhat tu Claude Ecosystem)
Hoc tu infographic Claude: Skills = "Day Claude cac quy trinh lap lai"
Wisdom's Blueprints = SOP cao cap co the thuc thi lap lai
- Khong chi ban data, ban "cach van hanh" (operational knowledge)
- Moi Blueprint co: steps[], triggers[], expected_output, success_metrics
- AI Agent co the chay Blueprint tu dong (Phase 2)
- Storefront = App Store cho cognitive workflows

### Extended Thinking = Adversarial Validation (Da co)
- Claude's Extended Thinking: internal reasoning truoc khi tra loi
- Wisdom's Devil's Advocate: llama3.1:8b phan bien node truoc khi VERIFY
- Da implement trong wisdom_validator.py — khong can them gi
- Nguyen tac: Chi VERIFIED khi pass red-team score >= 0.6

### Tech Stack Roadmap (Confirmed)
Phase 1 (hien tai): FastAPI + HTML thuan — functional, co data
Phase 2 (10+ users): React + TailwindCSS + D3.js graph 2D
Phase 3 (co revenue): React Three Fiber + WebGL Fluid + Blink-Synapse + Bloom effects

### Global Instructions cho moi AI Agent trong Wisdom
1. Doc CLAUDE.md truoc khi bat dau bat ky task nao
2. Tuan thu Wisdom Constitution tuyet doi
3. AskUserQuestion thay vi tu y quyet dinh khi chua ro boi canh
4. Output phai co artifact khi data cho phep visualize
5. Human-in-the-loop: Moi quyet dinh quan trong phai cho Sep xac nhan
## 16. UNDERSTAND-ANYTHING INTEGRATION (Thong nhat 2026-05-05)
> Repo: github.com/Lum1104/Understand-Anything | License: MIT
> Hoc de build better, khong copy nguyen xi

### 4 Thu Can Hoc Truc Tiep

**1. Knowledge Graph JSON Export**
- Pattern: Luu graph vao wisdom-graph-export.json
- Commit 1 lan, dung lai khong can chay lai pipeline
- Apply cho Wisdom: snapshot toan bo Neo4j graph de share + backup

**2. Dark Luxury Theme (Adapt cho Nature-Centric)**
- Understand-Anything: #0a0a0a (black) + #d4a574 (amber) + DM Serif Display
- Wisdom adapt: #0a1a0f (deep forest) + #d4a574 (amber) + Cream
- Graph-first layout: 75% graph + 360px right sidebar
- Rat gan voi Nature-Centric palette da chot

**3. 5-Agent Pipeline Pattern (Tiet kiem token)**
- Agents write intermediate results to DISK, khong return ve context
- => Tiet kiem token cuc nhieu khi scan large codebase/knowledge base
- Apply cho wisdom_scout.py:
  Scanner Agent    -> quet nguon, luu disk
  Analyzer Agent   -> phan tich content, luu disk
  Mapper Agent     -> xay dung graph relationships, luu disk
  Tour Builder     -> tao guided tour, luu disk
  Reviewer Agent   -> quality check, merge vao Neo4j

**4. Domain View -> Knowledge Flow Map**
- Understand-Anything: map code -> business domains/flows/steps
- Wisdom adapt: map knowledge nodes -> MMO earning journey
  Vi du: INBOX(raw tips) -> RAW(verified) -> WIKI(strategies) -> OUTBOX(blueprint)
  User nhin vao thay ngay "tri thuc cua toi dang o dau trong hanh trinh kiem tien"

### Impact Analysis (Tu DERIVED_FROM relationship)
- Khi sua 1 Rule trong WIKI -> Wisdom canh bao Blueprint nao bi anh huong
- Da co san: DERIVED_FROM relationship trong Neo4j schema
- Can build: impact_check() function trong wisdom_validator.py
- Logic:
  MATCH (r:Rule)<-[:DERIVED_FROM*]-(b:Blueprint)
  WHERE r.id = $rule_id
  RETURN b.title, b.id

### Guided Tours cho Blueprint (P-019)
- Khi user mua Blueprint -> auto-generate tour qua knowledge nodes
- Thu tu: theo ripeness_score + logical dependency
- Format: [{step, node_id, explanation, action}]
- Inspired by: tour-builder agent cua Understand-Anything
## 17. COUNCIL LOGIC — PERSONA AGENT SYSTEM (Thong nhat 2026-05-05)
> Inspired by: AI Advisory Board concept
> Antigravity phan tich: "Framework Filter + Quality Control, khong phai tai sinh vi nhan"

### Triet ly Cot loi
- KHONG phai: "Steve Jobs nghi gi?"
- LA: "Dua tren 10 nguyen tac thiet ke Apple, soi loi giao dien nay"
- Gia tri o FRICTION: Buoc user giai trinh tu duy cua chinh minh
- AI dong vai "Bao cat" de user tu lam ro quyet dinh
- RAG co trich dan: Phai cite nguon cu the, khong hallucinate

### 3 Personas Co Ban
buffett -> Circle of Competence, Margin of Safety, Long-term thinking
  Cau hoi mau: "Bien do an toan o dau?", "Day co nam trong vong tron nang luc khong?"

jobs    -> User value, Simplicity, "Would I use this?"
  Cau hoi mau: "User se cam nhan gi?", "Co the don gian hoa them khong?"

munger  -> Inversion, Mental models, Second-order effects
  Cau hoi mau: "Neu lam nguoc lai thi sao?", "He qua thu cap la gi?"

### Council Interrogation Flow
Knowledge Node chuan bi len WIKI
        ↓
[Council Interrogation Layer — wisdom_validator.py]
        ↓
Moi Persona dat 1-2 cau hoi dua tren framework cua ho
        ↓
[AskUserQuestion UI — Council Board]
3 persona cards, user tra loi tung cai
        ↓
Node duoc VERIFY voi council_score tong hop
        ↓
INTERROGATED_BY relationship luu vao Neo4j

### Neo4j Schema
(:PersonaAgent {
  id, name,
  framework: [str],
  source_books: [str],
  question_templates: [str]
})

(:KnowledgeNode)-[:INTERROGATED_BY {
  score: float,
  questions_asked: [str],
  user_response: str,
  timestamp: datetime
}]->(:PersonaAgent)

### Lo trinh Build
Step 1 (Ngay): council_check() trong wisdom_validator.py
  -> Chi la system prompt thay doi
  -> 3 personas: buffett, jobs, munger
  -> Khong can data moi

Step 2 (Tuan toi): Nap PDF sach vao Qdrant
  -> Collection: wisdom_personas (rieng biet)
  -> Khi Persona tra loi -> RAG tu collection nay
  -> Bat buoc cite nguon: "Theo trang X cua sach Y..."

Step 3 (Phase 2): Council Board UI
  -> 3 persona cards voi cau hoi rieng
  -> User tra loi tung card
  -> Glassmorphism design
  ## 18. TEMPORAL WISDOM AXIS (Thong nhat 2026-05-05)
> Giai quyet bai toan Cut-off date: Wisdom song cung nhip thi truong

### Mo hinh Du lieu "3 Thi"

QUA KHU (The Reservoir):
- Node types: WIKI — Concept, Rule, Framework, Mental Model
- Vi du: Munger mental models, Buffett frameworks, Lich su case study
- decay_lambda = 0.001 (gan nhu vinh vien)
- Xu ly: La "neo" de ra quyet dinh, it thay doi

HIEN TAI (The Stream):
- Node types: INBOX/RAW — Trend, News, Algorithm update
- Vi du: TikTok trend hom nay, FB algorithm moi, gia crypto
- decay_lambda = 0.05 (7-30 ngay het han)
- valid_until = ingested_at + domain_ttl
- Xu ly: PHAI trigger Live-Search truoc khi tra loi
- KHONG dung cached knowledge cho cac query HIEN TAI

TUONG LAI (The Vision):
- Node types: OUTBOX — Blueprint, Scenario, Prediction
- Vi du: "Neu TT algorithm thay doi, Blueprint nay bi anh huong gi?"
- Xu ly: Munger Inversion + Impact Analysis
- DERIVED_FROM chain de trace back nguon goc du lieu

### Freshness Guard — Wisdom Freshness Module
(Da co 80% trong schema hien tai, can bo sung Live-Search)

Da co:
- decay_lambda field tren moi node
- valid_until field tren moi node
- epistemic_status: DEPRECATED khi het han
- wisdom_decay.py chay hang ngay

Can them:
- Live-Search trigger khi query node co status STALE/HIEN_TAI
- Domain TTL config:
  trend_tiktok:    7 ngay
  trend_facebook:  7 ngay
  market_price:    1 ngay
  government_policy: 30 ngay
  framework:       vinh vien

### Conflict Detection: Qua khu vs Hien tai
Khi Persona Qua khu (Buffett: "Mua va giu") mau thuan voi
node Hien tai (Thi truong dang sup do):
-> EpistemicConflict node tu dong tao ra
-> AskUserQuestion: "Nguyen tac Qua khu dang mau thuan voi Thuc tai,
   Sep muon xu ly the nao?"
-> Options: [Giu nguyen tac] [Adapt cho tinh huong] [Danh dau CONTESTED]

### 2 Personas Moi (Bo sung vao Council Logic)

Persona 4: Street Smart (Thi truong thuc te)
- Khong co trong sach — build tu community knowledge
- Source: FB groups MMO VN, TikTok creator community, affiliate forums
- Framework: "Cai nay co 'mui' lua dao khong?", "Thuật toan vua thay doi gi?"
- Emerge tu: Wisdom users data (khi du data tu community)
- decay_lambda: 0.05 (cap nhat lien tuc)

Persona 5: The Intuition (Truc giac chi huy)
- Day la ban sao tu duy cua chinh Sep Thang
- Build tu: Lich su decision cua Sep trong Wisdom
- Capture: Tacit Knowledge Extraction (WISDOM CONSTITUTION Layer 4)
- Cau hoi mau: "Dua tren kinh nghiem xuong mau cua Sep o VN,
  Sep thay cai nay co 'mui' rui ro khong?"
- Unique moat: Khong AI tool nao co — chi Wisdom moi co

### Ghi chu Cong cu
- GitNexus: PENDING — van de tuong thich Windows, cho thong bao moi
- Understand-Anything: Dung thay the chinh de mapping tri thuc + code
  Pattern hoc: 5-agent pipeline, domain view, impact analysis
  ## APPEND VÀO CLAUDE.md — Session 2026-05-06

---

## 19. OBSIDIAN INTEGRATION STRATEGY (Thong nhat 2026-05-06)
> Inspired by: kepano/obsidian-skills (MIT License)
> Nguon: CEO Obsidian chia se repo bien ghi chu thanh he tri thuc AI-ready
> Antigravity concept: "Dual Brain" — Wisdom (AI Engine) + Obsidian (Local UI)

### Phan tich So sanh: Obsidian Skills vs Wisdom

| Obsidian Skills | Wisdom tuong duong | Ket luan |
|-----------------|-------------------|----------|
| Wikilinks, tags, properties | Neo4j relationships, labels | Wisdom MANH HON — co semantic meaning |
| Bases — dashboard/DB view | Web UI Dashboard (P-007) | Tuong duong |
| JSON Canvas — mindmap | Knowledge Graph visualization | Obsidian truc quan hon |
| Obsidian CLI — doc/tao note | wisdom_query.py + wisdom_upload.py | Tuong duong |
| Defuddle — clean web -> MD | Chua co — day la GAP | Can build P-023 |

### 3 Diem Wisdom MANH HON Obsidian Skills
1. Graph relationships co semantic meaning — SUPPORTS, CONTRADICTS, DERIVED_FROM
   Obsidian chi biet "lien ket", Wisdom biet "tai sao lien ket"
2. Temporal Decay (decay_lambda + valid_until) — Obsidian khong co
   Tri thuc Wisdom tu biet khi nao minh lot thoi
3. Council Logic (Persona Agents) — Obsidian khong co
   Knowledge phai qua interrogation truoc khi VERIFY

### 3 Thu Hoc Tu Obsidian Skills (Ap dung ngay)
1. Defuddle pattern -> wisdom_cleaner.py (P-023)
   - Clean HTML truoc khi ingest: bo ads, nav, footer
   - Extract: title, author, date, main content
   - Stack: trafilatura hoac readability-lxml

2. Mermaid output -> P-024
   - Query relationships -> tra ve Mermaid diagram
   - Render trong Web UI bang mermaid.js CDN, khong can D3.js
   - De build nhat trong interactive artifacts

3. Properties schema chuan hoa -> wisdom_node_schema.md (P-026)
   - Define ro tat ca fields, enum values, default decay_lambda
   - Doc truoc khi tao bat ky node nao

### Dual Brain Architecture (Phase 3)
```
[WISDOM — AI Engine]          [OBSIDIAN — Local UI]
Neo4j (Graph DB)    <------>  .md files + WikiLinks
Qdrant (Vector DB)  <------>  Obsidian Bases (Dashboard)
Council Logic       <------>  Canvas (Blueprint drag-drop)
Web UI (online)     <------>  Vault (offline-first)
```

Bridge: wisdom_obsidian_bridge.py (P-025)
- Export VERIFIED node -> .md co Properties + WikiLinks
- Watch vault -> ingest file moi vao Wisdom INBOX
- Canvas export: Blueprint -> JSON Canvas

### [RULE-H] Thu Tu Trien Khai — Obsidian Integration
```
Phase 2 (hien tai):
  1. P-023 wisdom_cleaner.py    — Defuddle, lam ngay
  2. P-024 Mermaid output       — Interactive, lam sau P-007
  3. P-026 node_schema.md       — Reference doc, lam ngay

Phase 3 (sau khi P-007 Web UI stable):
  4. P-025 wisdom_obsidian_bridge.py — Sync 2 chieu
```

CANH BAO: Khong lam P-025 truoc khi P-007 on dinh.
Ly do: Sync complexity — Neo4j + Obsidian lech nhau se rat kho debug.

### Obsidian Node Export Format (Chuan)
```markdown
---
id: {uuid}
title: {title}
trust_score: {0.0-1.0}
epistemic_status: PENDING|VERIFIED|CONTESTED|SHADOW|DEPRECATED
valid_from: {ISO date}
valid_until: {ISO date | null}
decay_lambda: {float}
review_cadence: daily|weekly|monthly|archive
cultural_context: GLOBAL|REGION_SPECIFIC
source_type: ACADEMIC|TACIT|SYNTHETIC
tags: [{domain}, {content_type}]
related: [[{linked_node_title_1}]], [[{linked_node_title_2}]]
---

{content}
```

### Ghi chu Chien luoc
- Obsidian = "Tai san so vat ly" — user so huu file that, khong bi lock-in
- Wisdom = "Nguoi quan kho thong minh" — khai thac va lam giau tri thuc
- Offline scenario: Obsidian chay khong can internet, Wisdom sync lai khi co mang
- Unique moat: Khong tool nao khac co Neo4j graph + Temporal decay + Council + Obsidian bridge
## APPEND VÀO CLAUDE.md — Session 2026-05-06

---

## 19. OBSIDIAN INTEGRATION STRATEGY (Thong nhat 2026-05-06)
> Inspired by: kepano/obsidian-skills (MIT License)
> Nguon: CEO Obsidian chia se repo bien ghi chu thanh he tri thuc AI-ready
> Antigravity concept: "Dual Brain" — Wisdom (AI Engine) + Obsidian (Local UI)

### Phan tich So sanh: Obsidian Skills vs Wisdom

| Obsidian Skills | Wisdom tuong duong | Ket luan |
|-----------------|-------------------|----------|
| Wikilinks, tags, properties | Neo4j relationships, labels | Wisdom MANH HON — co semantic meaning |
| Bases — dashboard/DB view | Web UI Dashboard (P-007) | Tuong duong |
| JSON Canvas — mindmap | Knowledge Graph visualization | Obsidian truc quan hon |
| Obsidian CLI — doc/tao note | wisdom_query.py + wisdom_upload.py | Tuong duong |
| Defuddle — clean web -> MD | Chua co — day la GAP | Can build P-023 |

### 3 Diem Wisdom MANH HON Obsidian Skills
1. Graph relationships co semantic meaning — SUPPORTS, CONTRADICTS, DERIVED_FROM
   Obsidian chi biet "lien ket", Wisdom biet "tai sao lien ket"
2. Temporal Decay (decay_lambda + valid_until) — Obsidian khong co
   Tri thuc Wisdom tu biet khi nao minh lot thoi
3. Council Logic (Persona Agents) — Obsidian khong co
   Knowledge phai qua interrogation truoc khi VERIFY

### 3 Thu Hoc Tu Obsidian Skills (Ap dung ngay)
1. Defuddle pattern -> wisdom_cleaner.py (P-023)
   - Clean HTML truoc khi ingest: bo ads, nav, footer
   - Extract: title, author, date, main content
   - Stack: trafilatura hoac readability-lxml

2. Mermaid output -> P-024
   - Query relationships -> tra ve Mermaid diagram
   - Render trong Web UI bang mermaid.js CDN, khong can D3.js
   - De build nhat trong interactive artifacts

3. Properties schema chuan hoa -> wisdom_node_schema.md (P-026)
   - Define ro tat ca fields, enum values, default decay_lambda
   - Doc truoc khi tao bat ky node nao

### Dual Brain Architecture (Phase 3)
```
[WISDOM — AI Engine]          [OBSIDIAN — Local UI]
Neo4j (Graph DB)    <------>  .md files + WikiLinks
Qdrant (Vector DB)  <------>  Obsidian Bases (Dashboard)
Council Logic       <------>  Canvas (Blueprint drag-drop)
Web UI (online)     <------>  Vault (offline-first)
```

Bridge: wisdom_obsidian_bridge.py (P-025)
- Export VERIFIED node -> .md co Properties + WikiLinks
- Watch vault -> ingest file moi vao Wisdom INBOX
- Canvas export: Blueprint -> JSON Canvas

### [RULE-H] Thu Tu Trien Khai — Obsidian Integration
```
Phase 2 (hien tai):
  1. P-023 wisdom_cleaner.py    — Defuddle, lam ngay
  2. P-024 Mermaid output       — Interactive, lam sau P-007
  3. P-026 node_schema.md       — Reference doc, lam ngay

Phase 3 (sau khi P-007 Web UI stable):
  4. P-025 wisdom_obsidian_bridge.py — Sync 2 chieu
```

CANH BAO: Khong lam P-025 truoc khi P-007 on dinh.
Ly do: Sync complexity — Neo4j + Obsidian lech nhau se rat kho debug.

### Obsidian Node Export Format (Chuan)
```markdown
---
id: {uuid}
title: {title}
trust_score: {0.0-1.0}
epistemic_status: PENDING|VERIFIED|CONTESTED|SHADOW|DEPRECATED
valid_from: {ISO date}
valid_until: {ISO date | null}
decay_lambda: {float}
review_cadence: daily|weekly|monthly|archive
cultural_context: GLOBAL|REGION_SPECIFIC
source_type: ACADEMIC|TACIT|SYNTHETIC
tags: [{domain}, {content_type}]
related: [[{linked_node_title_1}]], [[{linked_node_title_2}]]
---

{content}
```

### Ghi chu Chien luoc
- Obsidian = "Tai san so vat ly" — user so huu file that, khong bi lock-in
- Wisdom = "Nguoi quan kho thong minh" — khai thac va lam giau tri thuc
- Offline scenario: Obsidian chay khong can internet, Wisdom sync lai khi co mang
- Unique moat: Khong tool nao khac co Neo4j graph + Temporal decay + Council + Obsidian bridge