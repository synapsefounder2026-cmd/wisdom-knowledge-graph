# CLAUDE.md - Wisdom Project Brain & Rules

Đây là bộ não sống và quy tắc vận hành của dự án Wisdom. Mọi AI agent phải đọc file này trước khi bắt đầu bất kỳ task nào.

## Quy tắc cốt lõi (bắt buộc)

1. **Human in the loop**: Mọi quyết định quan trọng phải có xác nhận từ User (Sếp Thắng) hoặc Grok trước khi thực thi.
2. **SRS-First**: Luôn ưu tiên thiết kế yêu cầu rõ ràng, có cấu trúc trước khi viết code.
3. **Harness Engineering**: Xây dựng môi trường vững chắc, có session memory, validator, approval gate và CLAUDE.md living rules.
4. **Living Knowledge Map**: Mọi kiến thức, quy trình, insight phải được liên kết vào Knowledge Graph khi có thể.
5. **Multi-Model Strategy**:
   - GLM 5.1: Dùng cho task volume cao, chạy dài, phân tích codebase.
   - Claude Opus / Grok: Dùng cho kiến trúc, logic quan trọng, review code, quyết định cuối.
6. **Self-evolving**: Sau mọi correction hoặc bài học mới, phải đề xuất cập nhật file CLAUDE.md này để không lặp lại lỗi.

## Phong cách & Kiến trúc Wisdom
- Local-first + Privacy là ưu tiên hàng đầu.
- Code phải rõ ràng, có comment, dễ maintain và tuân thủ Solar System Architecture.
- Sử dụng GitNexus + Grapuco để hiểu codebase trước khi sửa đổi lớn.
- Tất cả output phải có chất lượng production, có test và security check khi cần.

## Quy trình làm việc bắt buộc cho mọi agent
- Bước 1: Đọc WISDOM_PROJECT_SUMMARY_v2026.md
- Bước 2: Đọc CLAUDE.md này
- Bước 3: Sử dụng Spec Agent nếu có yêu cầu nghiệp vụ
- Bước 4: Kiểm tra blast radius trước khi sửa code quan trọng
- Bước 5: Sau khi hoàn thành hoặc sửa lỗi → đề xuất cập nhật CLAUDE.md nếu cần

Cập nhật file này liên tục khi có bài học mới từ dự án.
## Bài học & Kinh nghiệm (2026-05-01)

### [BÀI HỌC 1] Gemini API free tier bị block tại Việt Nam
- Triệu chứng: Lỗi `limit: 0` trên tất cả keys dù chưa dùng
- Nguyên nhân: Google hạn chế free tier Gemini tại Việt Nam
- Giải pháp: Dùng **Ollama local** thay thế — đúng triết lý Local-first
- Lưu ý: Không mất thời gian thử VPN, đổi project, đổi model khi gặp `limit: 0`
- Model đang dùng: `gemma3:4b` chạy tốt trên 16GB RAM

### [BÀI HỌC 2] watch-cli — Knowledge Ingestion Agent
- Repo: github.com/sonpiaz/watch-cli
- Vai trò trong Wisdom: "Mắt và tai" — thu thập knowledge từ video
- Tích hợp: URL video → watch-cli → Ollama phân tích → Neo4j/Qdrant
- Phù hợp với: Open Source Intelligence Layer (Pillar 2)
- Ưu tiên: Tích hợp trong Phase 1

### [NGUYÊN TắC MỚI] Wisdom Value Flywheel
- Mọi tính năng phải phục vụ ít nhất 1 tầng:
- Học tập → Kinh nghiệm → Kiếm tiền → Cống hiến → Phát triển
- Nếu không trả lời được → không build
## Bài học & Quyết định (2026-05-01)

### [BÀI HỌC 1] Gemini API free tier bị block tại Việt Nam
- Triệu chứng: limit: 0 dù chưa dùng
- Giải pháp: Dùng Ollama local — đúng Local-first
- Model: gemma3:4b, RAM 16GB chạy tốt
- Không mất thời gian thử VPN hay đổi project

### [BÀI HỌC 2] watch-cli
- Repo: github.com/sonpiaz/watch-cli
- Vai trò: Knowledge Ingestion Agent
Bài học & Kinh nghiệm (2026-05-02) — Phase 0 Complete
[STACK CONFIRMED] Models đang dùng

llama3.1:8b — reasoning, coding, Q&A phức tạp (mạnh hơn gemma3:4b)
gemma3:4b — task nhẹ, volume cao
nomic-embed-text — embedding cho Qdrant vector search
Tất cả chạy local qua Ollama tại http://localhost:11434

[INFRASTRUCTURE] Docker services đã chạy ổn định

Neo4j 5.26.0: bolt://localhost:7687, browser http://localhost:7474

Auth: neo4j/password123


Qdrant 1.17.1: http://localhost:6333

Collection: wisdom_knowledge, vector size: 768, distance: COSINE


Cả hai dùng named volumes: neo4j_data, qdrant_data
Khởi động: docker-compose up -d trong thư mục project

[BÀI HỌC 3] watch-cli trên Windows/Git Bash — Các patch bắt buộc
Khi chạy watch-cli trên Windows với Git Bash, cần patch các file sau:
1. /c/Users/LENOVO/.local/bin/extract-frames

Thêm -update 1 vào ffmpeg command (single image output)
Dùng cygpath -m để convert Unix path → Windows path cho ffmpeg/ffprobe
Strip \r (carriage return) từ Python output: ts="${ts%%$'\r'*}"
Python trên Windows output \r\n thay vì \n → timestamps bị lỗi nếu không strip

2. /c/Users/LENOVO/.local/lib/env.sh

Copy từ ~/.watch-cli/lib/env.sh (file gốc có đầy đủ functions)
Không dùng file từ ~/.config/watch-cli/env vì thiếu functions

3. /c/Users/LENOVO/.config/watch-cli/env

Xóa dòng KYMA_API_KEY= trống — nếu để trống sẽ override GROQ mode
Dùng Groq API (free tier) thay Kyma: set GROQ_API_KEY=gsk_...
Thêm vào cuối file, không uncomment dòng # GROQ_API_KEY= có sẵn

4. ~/.bashrc
bashexport PATH="/c/Users/LENOVO/.local/bin:$PATH"
export TMPDIR="/tmp"
alias python3="python"
[BÀI HỌC 4] Python subprocess trên Windows

subprocess.run(["watch", url]) → FAIL vì Windows không biết Git Bash PATH
subprocess.run(f"watch {url}", shell=True) → FAIL vì shell=True dùng cmd.exe
✅ ĐÚNG: subprocess.run(["C:/Program Files/Git/bin/bash.exe", "-c", f"watch {url}"])
Áp dụng cho mọi Git Bash command gọi từ Python script trên Windows

[BÀI HỌC 5] Qdrant Client API thay đổi (v1.16+)

client.search() → đã bị deprecated, dùng client.query_points()
Parameter: query_vector= → đổi thành query=
Kết quả: trả về object, access qua .points (không phải list trực tiếp)
Ví dụ đúng:

pythonresults = client.query_points(
    collection_name=COLLECTION,
    query=embedding,
    limit=top_k,
    with_payload=True
)
for r in results.points:
    ...
[BÀI HỌC 6] API Key Security

KHÔNG BAO GIỜ paste API key thật vào chat
Nếu lỡ paste → xóa key ngay lập tức trên console của provider
Groq: https://console.groq.com → API Keys → Delete & Create new

[BÀI HỌC 7] Facebook video cần cookies

FB video thường login-walled → watch-cli không download được anonymous
Giải pháp: Export cookies từ Chrome bằng extension "Get cookies.txt LOCALLY"
Chạy: watch <FB_URL> --cookies ~/cookies.txt
TODO: Build auto-cookie helper cho FB ingestion pipeline

[PIPELINE HOÀN CHỈNH] Wisdom Knowledge Ingestion v1.0
URL (YT/FB/TikTok)
  → watch-cli (download + transcript via Groq Whisper)
  → Ollama llama3.1:8b (phân tích → title, concepts, tags, flywheel)
  → Neo4j (Video node + Concept nodes + Tag nodes + relationships)
  → Qdrant (vector embedding via nomic-embed-text)
[PIPELINE HOÀN CHỈNH] Wisdom Query v1.0
User question
  → nomic-embed-text (embed query)
  → Qdrant vector search (top-k similar)
  → Neo4j graph search (concept matching)
  → Ollama llama3.1:8b (generate answer từ context)
  → Bilingual answer (VI/EN tùy câu hỏi)
[FILES MỚI] Phase 0 Output

wisdom/core/wisdom_ingest.py — Knowledge Ingestion Pipeline
wisdom/core/wisdom_query.py — Knowledge Query Pipeline

[TRẠNG THÁI] Phase 0 — HOÀN THÀNH ✅
Tất cả infrastructure đã chạy ổn định:

Ollama + 3 models (llama3.1:8b, gemma3:4b, nomic-embed-text)
Docker + Neo4j + Qdrant
watch-cli (patched cho Windows)
Ingest pipeline + Query pipeline
Đã test với video thật: "AI Second Brain for Maximizing Productivity"

[NEXT] Phase 1 — Gợi ý ưu tiên

Build simple web UI (dashboard Knowledge Graph)
Tích hợp FB cookie helper
Batch ingestion (nhiều video cùng lúc)
Kết nối Wisdom với Solar System Ecosystem (affiliate layer)
## Bài học & Kinh nghiệm (2026-05-02 — Buổi chiều)

### [BÀI HỌC 8] Manual Upload Pipeline — wisdom_upload.py

**File mới:** `wisdom/core/wisdom_upload.py`

**Supported formats:**
- Documents: PDF, DOCX, PPTX, XLSX, TXT, MD
- Audio: MP3, WAV, M4A, OGG, FLAC (transcribe via Groq)
- Video: MP4, MOV, AVI (extract audio → transcribe)
- Images: JPG, PNG, BMP (OCR via Tesseract)
- Ebook: EPUB

**Dependencies cần cài:**
```bash
pip install pypdf2 python-docx python-pptx openpyxl pillow pytesseract ebooklib pdf2image
```

**Tools cần cài trên Windows:**
- Tesseract OCR v5.5.0: https://github.com/UB-Mannheim/tesseract/wiki
  - PATH: `/c/Program Files/Tesseract-OCR`
  - Thêm vào ~/.bashrc: `export PATH="/c/Program Files/Tesseract-OCR:$PATH"`
- Poppler v25.12.0: https://github.com/oschwartz10612/poppler-windows/releases
  - Giải nén vào `C:/poppler/`
  - PATH: `/c/poppler/poppler-25.12.0/Library/bin`
  - Thêm vào ~/.bashrc: `export PATH="/c/poppler/poppler-25.12.0/Library/bin:$PATH"`

### [BÀI HỌC 9] Scanned PDF cần OCR pipeline 2 bước
- PyPDF2 chỉ đọc được text-based PDF
- Scanned PDF (ảnh chụp) → PyPDF2 trả về empty string
- Giải pháp: thử text-based trước → nếu fail → fallback OCR
- OCR pipeline: `pdf2image (poppler)` → convert PDF → images → `pytesseract` → text
- Poppler path phải pass explicit: `convert_from_path(path, poppler_path=r"C:\poppler\...")`
- Tesseract path phải set explicit trong Python:
  `pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"`

### [BÀI HỌC 10] Python subprocess Windows — gọi Git Bash commands
- `subprocess.run(["command"])` → FAIL (Windows không biết Git Bash PATH)
- `subprocess.run("command", shell=True)` → FAIL (dùng cmd.exe)
- ✅ ĐÚNG: `subprocess.run(["C:/Program Files/Git/bin/bash.exe", "-c", "command"])`
- Áp dụng cho: watch, transcribe, và mọi Git Bash command từ Python

### [KIẾN TRÚC MỚI] Wisdom Input Intelligence — 5 Tiers
Đã chốt và document trong WISDOM_PROJECT_SUMMARY_v2026.md:
- Tier 1: Manual upload (PDF, Word, Audio, Video, Image, EPUB)
- Tier 2: URL & Social (YT, FB, TikTok, GitHub, Blog...)
- Tier 3: Auto-ingestion (Curated authors + Personal behavior)
- Tier 4: Real-time & Live (Phase 3)
- Tier 5: Device & Sensor (Phase 3+)

### [KIẾN TRÚC MỚI] Verified Solution Pool
- Knowledge tinh khiết, verified thực tế
- Gắn context: OS, version, hardware
- Owner nhận Wisdom Credit khi solution được dùng
- Privacy: không expose raw content nếu owner không muốn

### [KIẾN TRÚC MỚI] Pre-flight System Check
- Scan hardware, software, environment trước khi làm việc
- Auto-fix issues nếu có thể
- Readiness Score → match với Solution Pool phù hợp
- Kinh nghiệm từ Antigravity: scan → detect → fix → relocate working dir

### [KIẾN TRÚC MỚI] Multi-Project trên nền Wisdom
- Mỗi project có: CLAUDE.md riêng, .env riêng, Qdrant collection riêng
- Dùng chung: Ollama, Neo4j, Qdrant (1 Docker stack — tiết kiệm RAM)
- Tách biệt bằng namespace: collection name, Neo4j labels
- Wisdom = Platform Layer cho mọi project

### [NGUYÊN TẮC] CLAUDE.md chỉ được APPEND, không bao giờ REPLACE
- Lý do: giữ lịch sử, tính kế thừa, không mất bài học cũ
- Mỗi buổi làm việc → append section mới với date
- Không overwrite nội dung cũ dù có update

### [TRẠNG THÁI] Files hoàn chỉnh sau 2026-05-02
- `wisdom/core/wisdom_ingest.py` — Ingest từ URL (YT/FB/TikTok)
- `wisdom/core/wisdom_upload.py` — Upload file (PDF/Word/Audio/Video/Image)
- `wisdom/core/wisdom_query.py` — Search + Answer (Vector + Graph + LLM)

### [NEXT] Phase 1 — Ưu tiên tiếp theo
1. Web UI Dashboard (xem Knowledge Graph, search từ browser)
2. FB cookie helper (auto-ingest FB video)
3. Batch ingestion (nhiều URL/file cùng lúc)
4. New Project Starter Kit (template clone-and-run)
5. Kết nối Solar System Ecosystem (affiliate layer)