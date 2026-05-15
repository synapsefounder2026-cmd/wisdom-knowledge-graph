# Wisdom — Installation Guide
> Windows 11 | Git Bash | Python 3.10+
> Thời gian setup: 20-30 phút lần đầu

---

## Yêu cầu hệ thống

| Item | Minimum | Recommended |
|------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| RAM | 8GB | 16GB |
| Storage | 10GB free | 20GB free |
| Python | 3.10+ | 3.11+ |
| Internet | Cần khi setup | - |

---

## Bước 1 — Cài đặt Prerequisites

### 1.1 Git + Git Bash
Tải tại: https://git-scm.com/download/win
→ Cài với tất cả options mặc định
→ Kiểm tra: mở Git Bash, gõ `git --version`

### 1.2 Python 3.11
Tải tại: https://www.python.org/downloads/
→ **QUAN TRỌNG:** Tick "Add Python to PATH" khi cài
→ Kiểm tra trong Git Bash:
```bash
python --version
# Phải ra: Python 3.11.x
```

### 1.3 Docker Desktop
Tải tại: https://www.docker.com/products/docker-desktop/
→ Cài xong → Mở Docker Desktop → chờ icon Docker ở taskbar chuyển xanh
→ Kiểm tra:
```bash
docker --version
# Phải ra: Docker version 24.x.x
```

### 1.4 Node.js 20+ (cho FreeLLMAPI — optional)
Tải tại: https://nodejs.org/en/download
→ Chọn LTS version
→ Kiểm tra: `node --version`

---

## Bước 2 — Clone Wisdom repo

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/wisdom-knowledge-graph.git
cd wisdom-knowledge-graph
```

---

## Bước 3 — Tạo môi trường Python

```bash
python -m venv .venv
source .venv/Scripts/activate
# Thấy (.venv) ở đầu dòng là OK

pip install -r requirements.txt --break-system-packages
```

Nếu chưa có requirements.txt, cài thủ công:
```bash
pip install neo4j qdrant-client requests python-dotenv \
            faster-whisper yt-dlp fastmcp \
            PyPDF2 python-docx python-pptx openpyxl \
            --break-system-packages
```

---

## Bước 4 — Khởi động Neo4j + Qdrant (Docker)

```bash
# Khởi động containers
docker run -d \
  --name wisdom-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:latest

docker run -d \
  --name wisdom-qdrant \
  -p 6333:6333 -p 6334:6334 \
  qdrant/qdrant:latest

# Kiểm tra đang chạy
docker ps
# Phải thấy cả wisdom-neo4j và wisdom-qdrant
```

Kiểm tra Neo4j browser:
→ Mở Chrome → vào http://localhost:7474
→ Login: neo4j / password123
→ Thấy giao diện graph là OK ✅

---

## Bước 5 — Cài đặt Ollama (Local AI)

Tải tại: https://ollama.com/download
→ Cài xong → mở terminal mới → chạy:

```bash
# Pull models cần thiết (lần đầu ~5GB, cần internet)
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Kiểm tra
ollama list
# Phải thấy cả 2 models
```

---

## Bước 6 — Tạo file .env

```bash
cd ~/wisdom-knowledge-graph
cp .env.example .env
```

Nếu không có .env.example, tạo mới:
```bash
cat > .env << 'ENVEOF'
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=password123

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Ollama
OLLAMA_BASE=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
EMBED_MODEL=nomic-embed-text

# Optional — Gemini (free tại aistudio.google.com)
GEMINI_API_KEY=your_key_here

# Optional — Groq (free tại console.groq.com)
GROQ_API_KEY=your_key_here

# Paths
WISDOM_WIKI_DIR=wiki
WISDOM_REPORT_DIR=reports
WISDOM_PASSPORT_DIR=passport
ENVEOF
echo ".env created"
```

---

## Bước 7 — Test toàn bộ pipeline

```bash
cd ~/wisdom-knowledge-graph
source .venv/Scripts/activate

# Test 1: Ingest 1 video
python wisdom/core/wisdom_whisper.py \
  "https://www.youtube.com/watch?v=TeJAjXSteQc" \
  --model base

# Thành công nếu thấy:
# "Detected language: en"
# "Transcript: X,XXX chars"

# Test 2: Query
python wisdom/core/wisdom_query.py "OPC business"

# Test 3: Inverse search
python wisdom/core/wisdom_query.py --inverse "AI"

# Test 4: Weekly report
python wisdom/core/wisdom_report.py --days 7
```

---

## Xử lý lỗi thường gặp

### Lỗi: "docker: command not found"
→ Docker Desktop chưa mở. Mở Docker Desktop → chờ icon xanh → thử lại.

### Lỗi: "Connection refused port 7687"
```bash
docker start wisdom-neo4j
docker start wisdom-qdrant
```

### Lỗi: "No module named 'neo4j'"
```bash
source .venv/Scripts/activate
pip install neo4j --break-system-packages
```

### Lỗi: "ollama: command not found"
→ Ollama chưa cài hoặc chưa start.
```bash
# Start Ollama service
ollama serve &
```

### Lỗi: "Could not copy Chrome cookie database" (TikTok)
→ Đóng Chrome hoàn toàn trước khi chạy lệnh TikTok.

### Lỗi: LF/CRLF warning khi git commit
→ Bình thường trên Windows, bỏ qua.

### Whisper download chậm (~970MB model small)
→ Bình thường lần đầu. Sau khi download xong sẽ cache, lần sau nhanh.

---

## Cấu trúc thư mục sau khi setup

```
wisdom-knowledge-graph/
├── .env                    ← Config (KHÔNG commit)
├── .venv/                  ← Python environment
├── wiki/                   ← Wiki pages (.md)
├── reports/                ← Weekly reports
├── passport/               ← OPC Digital Passports
├── wisdom/core/
│   ├── wisdom_ingest.py    ← YouTube ingest
│   ├── wisdom_whisper.py   ← Local transcription
│   ├── wisdom_query.py     ← Search + Inverse search
│   ├── wisdom_wiki.py      ← Wiki page writer
│   ├── wisdom_upload.py    ← File upload
│   ├── wisdom_report.py    ← Weekly report
│   ├── wisdom_verify.py    ← Creator verification
│   ├── wisdom_channel_ingest.py ← Channel/playlist
│   ├── wisdom_mcp.py       ← MCP server
│   └── wisdom_passport.py  ← OPC Digital Asset
└── CLAUDE.md               ← Project context
```

---

## Kiểm tra cuối — Checklist trước khi dùng

```
□ docker ps → thấy wisdom-neo4j + wisdom-qdrant
□ http://localhost:7474 → Neo4j browser mở được
□ ollama list → thấy llama3.1:8b + nomic-embed-text
□ (.venv) hiện ở đầu dòng Git Bash
□ python wisdom/core/wisdom_query.py "test" → không báo lỗi
```

Tất cả 5 ✅ → Wisdom sẵn sàng!

---

*Wisdom Installation Guide v1.0 | 2026-05-15*
*Hỗ trợ: [contact]*
