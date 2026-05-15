# Wisdom — Error Handling Guide
> Các lỗi thường gặp và cách fix nhanh nhất

---

## Neo4j Errors

### "ServiceUnavailable: Failed to establish connection"
```bash
# Fix: Start Neo4j container
docker start wisdom-neo4j
# Chờ 10 giây rồi thử lại
```

### "AuthError: The client is unauthorized"
```bash
# Fix: Kiểm tra password trong .env
# NEO4J_PASS=password123 (mặc định)
```

### "warn: property key does not exist"
→ Bình thường — Neo4j cảnh báo field mới chưa có trên nodes cũ.
→ Không ảnh hưởng hoạt động. Bỏ qua.

---

## Qdrant Errors

### "Connection refused port 6333"
```bash
docker start wisdom-qdrant
```

### "Embedding size mismatch"
→ Model embedding đã thay đổi.
```bash
# Xóa collection cũ và tạo lại
python -c "
from qdrant_client import QdrantClient
c = QdrantClient('localhost', port=6333)
c.delete_collection('wisdom_knowledge')
print('Collection deleted — sẽ tự tạo lại khi ingest')
"
```

---

## Whisper / Transcription Errors

### "faster-whisper not found"
```bash
pip install faster-whisper --break-system-packages
```

### "yt-dlp not found"
```bash
pip install yt-dlp --break-system-packages
```

### Download chậm / treo ở model download
→ Bình thường lần đầu (~290MB base, ~970MB small).
→ Để máy chạy, không tắt terminal.
→ Sau khi download xong, lần sau nhanh ngay.

### "No transcript found"
```bash
# Thu fallback: youtube_transcript_api
pip install youtube-transcript-api --break-system-packages
# Chạy lại lệnh ingest
```

### Video private / age-restricted
→ Wisdom không thể ingest video private.
→ Chỉ ingest được video public.

---

## TikTok Errors

### "Could not copy Chrome cookie database"
→ Chrome đang mở. Đóng Chrome hoàn toàn → chạy lại.

### "Unable to extract secondary user ID"
→ TikTok block yt-dlp. Giải pháp:
1. Copy link video cụ thể (không phải channel)
2. Dùng công cụ transcript online → copy text → lưu .txt → upload

---

## Ollama Errors

### "connection refused port 11434"
```bash
# Start Ollama
ollama serve &
# Chờ 5 giây rồi thử lại
```

### "model not found"
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### Ollama chậm (>5 phút cho 1 video)
→ Bình thường trên CPU. GPU nhanh hơn 10x.
→ Thêm Gemini API key vào .env để dùng cloud thay Ollama.

---

## Python / Environment Errors

### "ModuleNotFoundError"
```bash
source .venv/Scripts/activate
pip install [module-name] --break-system-packages
```

### "(.venv) không hiện"
```bash
cd ~/wisdom-knowledge-graph
source .venv/Scripts/activate
```

### "python: command not found"
→ Python chưa được thêm vào PATH.
→ Reinstall Python, tick "Add to PATH".

---

## Docker Errors

### "docker: command not found"
→ Docker Desktop chưa mở. Mở Docker Desktop app.

### Container exit ngay sau khi start
```bash
# Xem logs
docker logs wisdom-neo4j
docker logs wisdom-qdrant
# Thường do port conflict
```

### Port conflict (port already in use)
```bash
# Tìm process đang dùng port 7687
netstat -ano | findstr :7687
# Kill process đó hoặc thay port trong .env
```

---

## Git Errors

### "LF will be replaced by CRLF"
→ Bình thường trên Windows. Bỏ qua, không ảnh hưởng.

### Không push được lên GitHub
```bash
git push origin main
# Nếu lỗi authentication → setup GitHub token
```

---

## Lệnh kiểm tra nhanh (chạy khi có vấn đề)

```bash
# Check tất cả services
echo "=== Docker ===" && docker ps
echo "=== Ollama ===" && ollama list
echo "=== Python ===" && python --version
echo "=== Neo4j ===" && python -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j','password123'))
with d.session() as s:
    r = s.run('RETURN 1 AS n').single()
    print('Neo4j OK:', r['n'])
d.close()
"
echo "=== Qdrant ===" && python -c "
from qdrant_client import QdrantClient
c = QdrantClient('localhost', port=6333)
print('Qdrant OK:', c.get_collections())
"
echo "=== Wisdom ===" && python wisdom/core/wisdom_verify.py --stats
```

Tất cả OK → Wisdom sẵn sàng hoạt động ✅

---

*Wisdom Error Handling Guide v1.0 | 2026-05-15*
