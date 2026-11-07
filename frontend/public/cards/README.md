# Ảnh lá bài

Backend trả `image_url` dạng `/cards/<slug>.jpg`, ví dụ `/cards/the-fool.jpg`, `/cards/ace-of-wands.jpg`.
Đặt đủ 78 file với đúng tên slug trong thư mục này (danh sách slug nằm trong `backend/scripts/data/cards.json`).

## Bản quyền (quan trọng)

- Bộ Rider-Waite-Smith xuất bản năm 1909 hiện thuộc phạm vi công cộng ở nhiều nước (kể cả Việt Nam),
  nhưng **các bản vẽ lại, tô màu lại, hoặc deck hiện đại thì thường còn bản quyền**.
- Nên tải bản quét gốc từ nguồn có ghi rõ giấy phép (ví dụ Wikimedia Commons, trang file có ghi
  "Public domain") và ghi nguồn vào báo cáo. Kiểm tra từng bản trước khi dùng.
- Trong thời gian chưa có ảnh, frontend nên hiển thị mặt bài tạm (tên lá) khi ảnh lỗi để không vỡ giao diện.
