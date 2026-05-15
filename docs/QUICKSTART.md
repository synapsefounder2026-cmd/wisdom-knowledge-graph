# Wisdom — Quick Start Guide
> Dành cho người đã setup xong (xem INSTALLATION.md)
> Mục tiêu: Có kết quả đầu tiên trong 15 phút

---

## Trước khi bắt đầu — Khởi động services

Mỗi lần mở máy, chạy 3 lệnh này trong Git Bash:

```bash
# 1. Start Docker containers
docker start wisdom-neo4j wisdom-qdrant

# 2. Activate Python environment
cd ~/wisdom-knowledge-graph
source .venv/Scripts/activate

# 3. Kiểm tra Ollama đang chạy
ollama list
# Nếu không thấy → chạy: ollama serve &
```

Thấy `(.venv)` ở đầu dòng = sẵn sàng ✅

---

## Bước 1 — Ingest video đầu tiên (5 phút)

Chọn 1 YouTube video bạn muốn học → copy link → chạy:

```bash
python wisdom/core/wisdom_whisper.py \
  "https://youtube.com/watch?v=VIDEO_ID" \
  --model base \
  --ingest
```

**Lần đầu:** Download model ~290MB (~2-3 phút)
**Từ lần 2:** Bắt đầu ngay

Thấy output này = thành công:
```
✅ Detected language: en (100%)
✅ Transcript: 15,432 chars
✅ Neo4j: node saved
✅ Qdrant: vector saved
✅ Wiki: wiki/how-i-build-opc_a1b2c3d4.md
```

---

## Bước 2 — Tìm kiếm knowledge (2 phút)

### Search thông thường
```bash
# Hỏi bằng tiếng Việt hoặc tiếng Anh
python wisdom/core/wisdom_query.py "OPC automation"
python wisdom/core/wisdom_query.py "làm thế nào để scale 1 người"
```

### Inverse Search — Dark Matter
Tìm chuỗi suy luận dẫn đến 1 concept:
```bash
python wisdom/core/wisdom_query.py --inverse "AI agent"
python wisdom/core/wisdom_query.py --inverse "trust"
```

---

## Bước 3 — Verify để trở thành Creator (3 phút)

Wisdom yêu cầu bạn **viết lại bằng lời của mình** trước khi knowledge được đánh dấu VERIFIED:

```bash
python wisdom/core/wisdom_verify.py
```

Flow:
```
1. Xem Output Stats (HOARDER/CURATOR/CREATOR)
2. Chọn số để verify node
3. Viết lại 1 insight bằng lời của bạn (min 20 ký tự)
4. Chọn đã dùng để làm gì
5. Node lên VERIFIED ✅
```

**Target:** Output Rate > 30% = CREATOR MODE

---

## Bước 4 — Xem Weekly Report (2 phút)

```bash
python wisdom/core/wisdom_report.py --days 7
```

Report xuất hiện tại: `reports/wisdom_report_YYYYMMDD.md`

Mở file → thấy 6 sections:
1. This Week (stats)
2. Top Insights (AI tổng hợp)
3. Action Items (việc cần làm)
4. By OPC Domain (phân loại)
5. Connections Found (liên kết ẩn)
6. **Output Health Check** (Creator/Curator/Hoarder status)

---

## Shortcuts hay dùng nhất

```bash
# Ingest 1 video
python wisdom/core/wisdom_whisper.py "URL" --ingest

# Ingest cả channel (20 video mới nhất)
python wisdom/core/wisdom_channel_ingest.py "https://youtube.com/@channel" \
  --limit 20 --dry-run    # Preview trước
python wisdom/core/wisdom_channel_ingest.py "https://youtube.com/@channel" \
  --limit 20              # Ingest thật

# Upload file PDF/DOCX/TXT
python wisdom/core/wisdom_upload.py "path/to/file.pdf"

# Search
python wisdom/core/wisdom_query.py "câu hỏi của bạn"
python wisdom/core/wisdom_query.py --inverse "concept"

# Verify nodes
python wisdom/core/wisdom_verify.py
python wisdom/core/wisdom_verify.py --stats

# Weekly report
python wisdom/core/wisdom_report.py

# OPC Score (sau khi có revenue)
python wisdom/core/wisdom_passport.py --score
python wisdom/core/wisdom_passport.py --valuation
```

---

## 7 ngày đầu — Làm theo thứ tự này

### Ngày 1-2: Build Knowledge Base
```bash
# Ingest 5-10 videos về chủ đề bạn đang nghiên cứu
python wisdom/core/wisdom_channel_ingest.py "URL_channel" --limit 10
```

### Ngày 3: Verify + Understand
```bash
python wisdom/core/wisdom_verify.py
# Verify ít nhất 5 nodes
# Viết lại insight bằng lời của bạn
```

### Ngày 4: Nhận Weekly Report đầu tiên
```bash
python wisdom/core/wisdom_report.py --days 7
# Đọc kỹ phần Action Items
# Làm ít nhất 1 action item
```

### Ngày 5-6: Mở rộng nguồn ingest
```bash
# Upload tài liệu PDF/sách
python wisdom/core/wisdom_upload.py "book.pdf"

# Ingest web article (copy text → lưu .txt → upload)
python wisdom/core/wisdom_upload.py "article.txt"
```

### Ngày 7: Đánh giá
```bash
python wisdom/core/wisdom_verify.py --stats
# Output Rate > 30%? → CREATOR MODE ✅
# Output Rate < 10%? → Cần verify thêm nodes
```

---

## Dấu hiệu Wisdom đang hoạt động đúng

```
✅ Mỗi ingest tạo ra 1 wiki page trong wiki/
✅ wisdom_query.py trả về kết quả liên quan
✅ Weekly report có Action Items cụ thể
✅ Output Rate > 30% (CREATOR MODE)
✅ Inverse search tìm ra reasoning chains
```

## Dấu hiệu cần check lại

```
⚠️  Query không ra kết quả → Ingest thêm content
⚠️  Output Rate 0% → Chạy wisdom_verify.py
⚠️  Wiki folder trống → wisdom_wiki.py chưa được gọi
⚠️  Report không có insights → Nodes chưa có opc_applicability
```

---

## Câu hỏi thường gặp

**Q: Ingest bao nhiêu video là đủ?**
A: 20+ videos để Wisdom có đủ context. 50+ để inverse search thật sự có giá trị.

**Q: Model nào tốt nhất cho tiếng Việt?**
A: `--model small` cho tiếng Việt (~970MB, cần RAM 2GB).
   `--model base` cho tiếng Anh (~290MB, nhanh hơn).

**Q: Wisdom có lưu data lên cloud không?**
A: Không. 100% local — Neo4j, Qdrant, Ollama đều chạy trên máy của bạn.

**Q: Mất data khi tắt máy không?**
A: Không mất. Docker containers lưu data persistent.
   Backup thêm: `bash backup_now.sh`

**Q: Dùng Gemini thay Ollama được không?**
A: Được. Thêm `GEMINI_API_KEY` vào `.env` → video > 10 phút tự dùng Gemini.

---

*Wisdom Quick Start v1.0 | 2026-05-15*
