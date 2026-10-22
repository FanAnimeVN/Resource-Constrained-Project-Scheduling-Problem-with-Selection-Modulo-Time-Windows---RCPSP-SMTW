# Kịch bản demo (khoảng 5 phút)

Chuẩn bị: `make setup && make serve`, sau đó mở http://localhost:8000.

1. **Tân sinh viên (sv01).**
   - Thao tác: chọn *Nguyễn Minh An*, bấm **Lập lộ trình**.
   - Hệ thống tự gợi ý chuyên ngành *Khoa học máy tính*, vì sinh viên thích AI và dữ liệu.
   - Có 5 tab phương án. Nên so sánh:
     - *Tốt nghiệp sớm*: 6 kỳ, 24 TC/kỳ;
     - *Cân bằng tải*: 8 kỳ, 17–18 TC/kỳ.
2. **Giải trình.**
   - Thao tác: bấm vào thẻ *Cấu trúc dữ liệu và giải thuật*.
   - Ngăn giải trình cho biết:
     - môn là bắt buộc của khối Cơ sở ngành;
     - không học sớm hơn được vì môn học trước (Kỹ thuật lập trình) xếp ở HK2 2026–2027, trong khi môn này
       chỉ mở HK1;
     - mở khóa những môn nào;
     - điểm rủi ro.
   - Bấm **Mô phỏng: nếu rớt môn này?** để xem tốt nghiệp chậm bao nhiêu kỳ.
3. **So sánh.**
   - Trang *So sánh phương án* có bảng chỉ số (ô tô đậm là giá trị tốt nhất), biểu đồ tải theo kỳ và ma trận
     khoảng cách. Đây là minh chứng cho AC-07.
4. **Tư vấn chuyên ngành (sv02).**
   - Thao tác: chọn *Trần Thu Bình*, vào trang *Tư vấn chuyên ngành*, bấm **Phân tích**.
   - *Công nghệ phần mềm* đứng đầu nhờ điểm Kỹ thuật lập trình cao, sở thích phần mềm/web và mục tiêu backend.
   - Thử đổi định hướng: kéo "Mạng & hạ tầng" và "An toàn thông tin" lên 5, hạ "Kỹ nghệ phần mềm" và
     "Web & di động" xuống 1, chỉ giữ mục tiêu nghề "Kỹ sư mạng", rồi phân tích lại. *Mạng máy tính và
     Viễn thông* sẽ lên đầu.
5. **Đăng ký kỳ tới.**
   - Trang này cho danh sách gợi ý cho HK2 2026–2027, bộ đếm tín chỉ so với giới hạn, các môn thay thế và cảnh
     báo môn mỗi năm chỉ mở một lần.
6. **Sinh viên nợ môn (sv03).**
   - Sinh viên đang bị cảnh báo học tập nên tải bị giới hạn 10–14 TC.
   - GPA dưới 7.0 nên không được làm khóa luận. Hệ thống tự chọn *Thực tập + Đồ án tốt nghiệp* thay thế.
7. **Vô nghiệm (sv04).**
   - Hệ thống không đưa ra lộ trình sai. Thay vào đó nó cho:
     - chẩn đoán *"Chuỗi tiên quyết … cần tối thiểu 5 học kỳ, nhưng chỉ còn 2 học kỳ"*;
     - tập luật xung đột tối thiểu;
     - gợi ý gia hạn. Đây là minh chứng cho AC-05.
8. **Đổi quy chế không sửa code (AC-06).**
   - Ở trang hồ sơ, đổi *Bộ quy chế* sang "10–22 TC" rồi lập lộ trình lại: mọi kỳ đều ≤ 22 TC.
   - Hoặc sửa trực tiếp file `data/hcmus_cntt_k2020/regulations/default.json`.
9. **Dữ liệu CTĐT.**
   - Trang này có cây khối kiến thức, báo cáo kiểm tra dữ liệu và đồ thị tiên quyết.
   - Bấm *Cơ sở trí tuệ nhân tạo* để tô sáng cả chuỗi điều kiện phía trước nó.
