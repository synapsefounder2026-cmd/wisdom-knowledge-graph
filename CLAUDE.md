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