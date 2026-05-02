# SRS Tuần 1 — Personal Second Brain

## Mục tiêu
User ghi chú → Ollama extract insights 
→ Neo4j lưu → Qdrant vector hóa → Search được

## User Stories
1. Sếp gõ/paste ghi chú vào Wisdom
2. Wisdom tự động extract: chủ đề, keywords, insights
3. Lưu vào Neo4j Knowledge Graph
4. Vector hóa vào Qdrant
5. Sếp search → Wisdom trả về kết quả liên quan

## Tech Stack
- Input: CLI đơn giản (terminal)
- AI: Ollama gemma3:4b
- Graph: Neo4j (đang chạy)
- Vector: Qdrant (đang chạy)

## Definition of Done
- Ghi chú 5 notes thật
- Search ra đúng kết quả
- Response dưới 10 giây