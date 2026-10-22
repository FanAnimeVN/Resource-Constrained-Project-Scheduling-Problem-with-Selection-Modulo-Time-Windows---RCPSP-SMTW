# Quyết định nghiệp vụ (trả lời 6 câu hỏi ở Mục 5 của đặc tả)

Mọi giá trị dưới đây nằm trong **file dữ liệu**, không viết cứng trong code. Muốn đổi luật chỉ cần sửa JSON
(đây chính là yêu cầu AC-06).

| # | Câu hỏi | Mặc định cho MVP | Cấu hình ở |
|---|---|---|---|
| 1 | Ngưỡng TC mỗi kỳ | Kỳ chính 14–24 TC. Kỳ cuối được miễn mức sàn. Kỳ hè 0–8 TC, chỉ xếp khi sinh viên bật "Học hè". SV bị cảnh báo học tập: 10–14 TC (giá trị mẫu). Hồ sơ `hcmus_clc_2025.json` dùng 10–22 TC (theo thông báo ĐKHP 2025–2026 của CT CLC). | `data/<ds>/regulations/*.json` |
| 2 | 138 TC là "đúng bằng" hay "tối thiểu" | **Tối thiểu (≥ 138)**: tài liệu Khoa ghi "SV có thể tích lũy nhiều hơn 138TC". Mục tiêu phụ: giảm tối đa TC dư. Vẫn hỗ trợ `credit_rule: "exact"`. | `curriculum.json` |
| 3 | Học trước vs tiên quyết | **Tiên quyết**: phải ĐẠT A (điểm ≥ `min_grade` nếu có) ở kỳ trước. **Học trước**: chỉ cần đã HỌC A ở kỳ trước, kể cả khi rớt. **Song hành**: học A trước hoặc cùng kỳ với B. (Theo TT 08/2021/TT-BGDĐT.) | `dependencies.json` |
| 4 | Môn tương đương | Nhóm tương đương hai chiều (đổi mã) + thay thế một chiều. Đạt môn tương đương = đạt môn gốc (thỏa tiên quyết, được tính vào khối). Tự sinh loại trừ giữa các môn tương đương. | `equivalences.json` |
| 5 | Thời gian đào tạo | Chuẩn 8 kỳ chính; tối đa 12 kỳ chính (6 năm). **Cần đối chiếu QĐ 1175/QĐ-KHTN.** | `regulations/*.json` |
| 6 | "Khác biệt có ý nghĩa" | Mỗi phương án tối ưu một mục tiêu khác nhau; ma trận (môn, kỳ) của hai phương án chiến lược khác nhau ít nhất 1 môn (no-good cut chỉ thêm khi trùng). Khoảng cách = số môn khác kỳ + khác biệt tập môn tự chọn + chênh kỳ tốt nghiệp. | engine |

## Quyết định bổ sung

- Mức sàn áp chặt cho mọi kỳ chính giữa lộ trình (không bỏ trống kỳ). Cờ `allow_empty_main_terms` (mặc định `false`).
- GDTC, GDQP, chuẩn ngoại ngữ không tính vào 138 TC → hiển thị dạng checklist điều kiện tốt nghiệp.
- Môn đang học (IN_PROGRESS) mặc định được giả định là sẽ đạt (`assume_in_progress_pass`).
- Tiên quyết chỉ hỗ trợ dạng "A và B"; trường hợp "A hoặc B" xử lý qua bảng tương đương.

## Những con số cần Phòng Đào tạo xác nhận

Dữ liệu mẫu được dựng từ thông tin công khai (xem `docs/MVP_PLAN.md`, mục 13) vì không truy cập trực tiếp được
trang của trường. Các bản ghi chưa xác minh có `"source": "sample"`. Cần xác nhận: ngưỡng TC/kỳ, thời gian tối đa,
danh sách môn chuyên ngành, lịch mở môn, điều kiện làm khóa luận.
