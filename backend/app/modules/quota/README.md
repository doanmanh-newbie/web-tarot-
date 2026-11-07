# Module `quota`

Luật giới hạn lượt bốc bài mỗi ngày (mặc định 3, cấu hình bằng `DAILY_READING_LIMIT`, "ngày" tính theo `APP_TIMEZONE` = UTC+7).

Phụ thuộc module khác: không.

## Thành phần

| File | Vai trò |
|---|---|
| `domain/quota_policy.py` | `day_bounds` (mốc 00:00 theo giờ VN), `build_status`, `QuotaConfig`, `QuotaStatus` |
| `domain/exceptions.py` | `DailyQuotaExceeded` (-> HTTP 429) |
| `application/ports/reading_counter.py` | Port "đếm số lượt của user trong khoảng thời gian"; `readings` cài đặt |
| `application/use_cases/get_quota.py` | Tính số lượt đã dùng / còn lại |

## Vì sao không có tầng presentation

Chỉ module `readings` biết cách đếm lượt (bảng `readings`), mà `readings` phụ thuộc `quota` chứ không được ngược lại.
Nên endpoint `GET /me/quota` đặt trong router của `readings`, gọi use case `GetQuota` của module này. Vậy đồ thị phụ thuộc
vẫn một chiều (`readings` -> `quota`), không có vòng.

## Luật nghiệp vụ

Xem bảng BR-01..BR-06 trong `readings/README.md` (lượt tính khi nào, xóa lịch sử có hoàn lượt không, admin có bị giới hạn không).
