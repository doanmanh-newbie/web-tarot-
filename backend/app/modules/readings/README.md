# Module `readings`

Module lõi: bốc bài, nhờ AI diễn giải, lưu và quản lý lịch sử.

Phụ thuộc module khác: `quota`, `cards`, `spreads` (và `auth` ở tầng presentation để biết người đang đăng nhập).

## Endpoint (đều cần đăng nhập)

| Method | Path | Mô tả |
|---|---|---|
| POST | `/readings` | Bốc bài: `{spread_id, question}` -> 201 + reading (kèm lời diễn giải) |
| POST | `/readings/{id}/interpret` | Giải lại khi lần trước AI lỗi (không bốc lại, không tốn lượt) |
| GET | `/readings?limit=20&offset=0` | Lịch sử của tôi, mới nhất trước |
| GET | `/readings/{id}` | Chi tiết một lần bốc |
| DELETE | `/readings/{id}` | Xóa khỏi lịch sử (204) |
| GET | `/me/quota` | Số lượt đã dùng / còn lại hôm nay |

## Luồng bốc bài

```
POST /readings
  1. Kiểm tra câu hỏi (1..300 ký tự) và kiểu trải bài        <- lỗi ở đây KHÔNG mất lượt
  2. Server bốc ngẫu nhiên (module secrets), mỗi lá 50% ngược
  3. Lưu reading + kiểm tra quota trong MỘT bước nguyên tử   <- hết lượt: 429
  4. Gọi AI (đã có bài trong DB rồi)                          <- lỗi: reading.ai_status = "failed"
  5. Trả 201 + reading
```

## Luật nghiệp vụ (đưa vào tài liệu yêu cầu)

| Mã | Luật |
|---|---|
| BR-01 | Mỗi người dùng được bốc tối đa `DAILY_READING_LIMIT` (mặc định 3) lần mỗi ngày. "Ngày" tính theo UTC+7, đổi lúc 00:00 giờ Việt Nam. |
| BR-02 | Lượt được tính khi bài đã được bốc và lưu. Nếu AI lỗi thì bài vẫn được giữ, lượt vẫn tính (người dùng đã rút bài), và người dùng bấm "Giải lại" không tốn thêm lượt, không bốc lại. |
| BR-03 | Xóa lịch sử không hoàn lại lượt (xóa mềm, vẫn tính vào quota), để không thể "bốc rồi xóa" nhằm lách giới hạn. |
| BR-04 | Tài khoản admin không bị giới hạn lượt. |
| BR-05 | Câu hỏi bắt buộc, 1 đến 300 ký tự (sau khi bỏ khoảng trắng thừa). Câu hỏi/kiểu trải bài không hợp lệ thì không mất lượt. |
| BR-06 | Chỉ chủ sở hữu được xem, giải lại và xóa reading. Người khác nhận 404 (không phải 403) để không lộ reading có tồn tại. |
| BR-07 | Reading đã có diễn giải thì "Giải lại" trả luôn kết quả cũ, không gọi AI lần nữa (tiết kiệm quota Gemini). |

## Quyết định thiết kế (đưa vào báo cáo)

| Vấn đề | Cách xử lý |
|---|---|
| Bốc bài ở đâu | Server, bằng `secrets.SystemRandom` (nguồn ngẫu nhiên của hệ điều hành). Client không gửi lá bài lên nên không thể gian lận |
| Chống bấm đồng thời để lách giới hạn | Kiểm tra quota + lưu reading cùng một transaction, khóa theo user bằng `pg_advisory_xact_lock`. Đã đo trên PostgreSQL 16 thật: 12 request cùng lúc, limit 3: có khóa luôn đúng 3 lượt, bỏ khóa thì cả 12 lọt qua |
| AI lỗi / chậm | Timeout (`GEMINI_TIMEOUT_SECONDS`, mặc định 20s); mọi lỗi (mạng, hết quota, bị chặn nội dung, trả rỗng) đổi thành `InterpretationFailed`; bài vẫn lưu, `ai_status="failed"`, có nút "Giải lại" |
| AI bịa ý nghĩa | Prompt chứa "Ý nghĩa gốc" của từng lá (lấy từ DB, đúng chiều xuôi/ngược) và yêu cầu chỉ dựa vào đó. Đây là grounding bằng dữ liệu có cấu trúc, tương tự RAG nhưng truy xuất theo khóa chính |
| Prompt injection | Câu hỏi bọc trong `<cau_hoi>` và được coi là dữ liệu; bỏ ký tự `<` `>` nên không tự đóng thẻ; giới hạn 300 ký tự; AI không có công cụ nào để lạm dụng. Là giảm thiểu rủi ro, không phải bảo đảm tuyệt đối |
| Nội dung nhạy cảm | System prompt cấm lời khuyên y tế/pháp lý/tài chính, cấm khẳng định chắc chắn về bệnh tật/cái chết, hướng người dùng tới chuyên gia khi câu hỏi liên quan sức khỏe/tự hại; mỗi kết quả kèm `disclaimer` "chỉ mang tính giải trí" |
| Không có API key | App vẫn chạy: bài vẫn bốc và lưu, `ai_status="failed"` kèm thông báo; `AI_PROVIDER=offline` cho diễn giải mẫu không cần mạng |
| Lộ thông tin | Không ghi câu hỏi của người dùng và API key vào log |
| Truy vấn | Lịch sử lấy lá bài và kiểu trải theo lô (không N+1) |

## Hạn chế đã biết (ghi vào báo cáo)

- Gọi Gemini chạy đồng bộ trong request (tối đa ~20s giữ một worker). Đủ cho đồ án; muốn mở rộng thì chuyển sang hàng đợi/async.
- Hai lần bấm "Giải lại" cùng lúc trên một reading có thể gọi AI hai lần (không ảnh hưởng quota của người dùng, chỉ tốn thêm một lượt gọi Gemini).
- Reading xóa mềm vẫn nằm trong DB (cần cho quota). Nếu cần xóa hẳn theo yêu cầu quyền riêng tư thì thêm job dọn dẹp sau khi qua ngày.
- Chặn nội dung nhạy cảm dựa vào prompt và bộ lọc an toàn của Gemini, chưa có bước kiểm duyệt riêng ở phía server.
- Tên model Gemini đổi/ngừng nhanh; nếu model bị gỡ, API trả lỗi và mọi lần diễn giải sẽ ở trạng thái "failed" cho tới khi đổi `GEMINI_MODEL`.
