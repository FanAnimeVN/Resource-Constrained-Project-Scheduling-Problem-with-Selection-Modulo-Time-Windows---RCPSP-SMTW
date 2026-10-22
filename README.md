# Hệ thống lập lộ trình học tập cá nhân hóa (RCPSP-SMTW)

Hệ thống gợi ý **lộ trình đăng ký tín chỉ tối ưu** qua nhiều học kỳ, **giải thích** từng đề xuất và
**tư vấn chọn chuyên ngành** cho sinh viên. Dữ liệu mẫu mô phỏng chương trình Cử nhân Công nghệ thông tin
138 tín chỉ (từ khóa 2020) của Khoa CNTT, Trường ĐH Khoa học Tự nhiên – ĐHQG-HCM.

Về mặt toán học, đây là một biến thể của bài toán **lập lịch dự án có giới hạn nguồn lực, có chọn lựa và
cửa sổ thời gian theo chu kỳ** (*Resource-Constrained Project Scheduling Problem with Selection & Modulo-Time
Windows*):
- học phần là công việc;
- tín chỉ mỗi kỳ là nguồn lực bị giới hạn;
- kỳ mở môn (HK1/HK2/Hè, năm chẵn/lẻ) là cửa sổ thời gian lặp theo chu kỳ;
- môn tự chọn là phần "chọn lựa".

> ⚠️ Dữ liệu trong `data/hcmus_cntt_k2020` là **dữ liệu mẫu**, dựng từ thông tin công khai. Mọi bản ghi chưa
> xác minh đều có `"source": "sample"`. Trước khi dùng thật, cần đối chiếu với CTĐT và quy chế chính thức
> (QĐ 1175/QĐ-KHTN), rồi nạp lại qua `cplan import-csv`.

## Hệ thống làm được gì

| Chức năng | Mô tả |
|---|---|
| **Lộ trình tối ưu** | Chọn môn và xếp kỳ cùng lúc bằng OR-Tools CP-SAT. Lộ trình thỏa đủ 11 ràng buộc cứng HC-01..HC-11 (tín chỉ, tiên quyết/học trước/song hành, loại trừ, tải kỳ, kỳ mở môn, hạn đào tạo) và các điều kiện riêng của từng môn (tích lũy tối thiểu, học ở kỳ cuối, GPA). |
| **5 phương án** | *Tốt nghiệp sớm* · *Cân bằng tải* · *An toàn (đệm học lại)* · *Theo định hướng* · *Đề xuất cho bạn* (dung hòa theo trọng số do sinh viên chọn). Kèm bảng so sánh chỉ số và bảo đảm các phương án khác nhau. |
| **Giải trình** | Mỗi môn có 4 phần: vì sao chọn, vì sao xếp ở kỳ đó (thử dời môn sớm hơn để xem luật nào bị vi phạm), chuỗi phụ thuộc, và rủi ro (nếu rớt thì học lại kịp không). |
| **Khi không có lời giải** | Không bao giờ trả lộ trình sai quy chế. Thay vào đó trả: chẩn đoán nhanh (ví dụ "chuỗi tiên quyết dài hơn số kỳ còn lại"), **tập luật xung đột tối thiểu (MUS)** và gợi ý tháo gỡ (gia hạn, bật học hè…). |
| **Tư vấn chuyên ngành** | Chấm điểm minh bạch theo 4 thành phần: học lực ở môn nền tảng, sở thích, mục tiêu nghề nghiệp, và tiến độ tốt nghiệp nếu chọn chuyên ngành đó (do bộ tối ưu chạy thử). Kèm độ tin cậy và độ ổn định của thứ hạng. |
| **Đăng ký kỳ tới** | Danh sách môn nên đăng ký, các môn có thể thay thế kèm lý do, và cảnh báo môn mỗi năm chỉ mở một lần. |
| **Mô phỏng rớt môn** | "Nếu rớt môn X thì tốt nghiệp chậm bao nhiêu kỳ?" |
| **Tích hợp cho nhà trường** | Có REST API kèm OpenAPI, import CSV từ Phòng Đào tạo, và bộ kiểm tra dữ liệu (phát hiện chu trình bằng Tarjan, kiểm tra tham chiếu, kiểm tra khối có đủ tín chỉ…). Mọi quy chế nằm trong file dữ liệu, không viết cứng trong code. |

## Chạy thử nhanh

Yêu cầu: Python ≥ 3.11, Node ≥ 20. Có `uv` thì cài nhanh hơn, nhưng không bắt buộc.

```bash
make setup          # tạo backend/.venv, cài OR-Tools, FastAPI…; npm ci cho frontend
make test           # 49 test backend (unit, property, BDD AC-01..AC-07, API) + vitest
make serve          # build giao diện rồi mở http://localhost:8000 (API + web cùng cổng)
```

Chạy ở chế độ phát triển (2 terminal): `make dev-api` và `make dev-web`, sau đó mở http://localhost:5173.

Dùng dòng lệnh:

```bash
backend/.venv/bin/cplan validate hcmus_cntt_k2020             # kiểm tra dữ liệu CTĐT
backend/.venv/bin/cplan plan --student sv02 --strategy BALANCED
backend/.venv/bin/cplan plan --student sv04                   # ví dụ vô nghiệm → báo cáo xung đột
backend/.venv/bin/cplan advise --student sv02                 # tư vấn chuyên ngành
```

Tài liệu API (Swagger) có tại http://localhost:8000/docs.

Docker: `docker compose up --build` dựng một image phục vụ cả API lẫn giao diện tại cổng 8000. Dockerfile
**chưa được build thử** trong môi trường phát triển hiện tại vì không có Docker daemon.

## Deploy công khai lên Vercel

Repo đã có sẵn `vercel.json`, `api/index.py` và `requirements.txt`:
- giao diện build từ `frontend/` và được phục vụ dạng tĩnh;
- mọi đường dẫn `/api/*` chạy FastAPI + OR-Tools trong một hàm Python serverless (tối đa 60 giây, 2 GB RAM).

Các bước:
1. Vào https://vercel.com/new, chọn **Import** repo GitHub này. Không cần đổi cấu hình: Vercel tự đọc `vercel.json`.
2. Bấm **Deploy**. Bản build từ nhánh `main` là bản *Production* với đường dẫn công khai `*.vercel.app`.
3. Bản build từ nhánh khác là *Preview*. Mặc định Vercel bật *Deployment Protection* cho Preview, nên người ngoài
   phải đăng nhập mới xem được. Muốn chia sẻ công khai, hãy merge vào `main`, hoặc tắt mục này trong
   Settings → Deployment Protection.

Hoặc dùng CLI: `npm i -g vercel && vercel --prod`.

## Kiến trúc

```
data/  (JSON: danh mục môn, phụ thuộc, lịch mở, cây khối, quy chế, SV mẫu)
  │
  ▼
validation/ ── kiểm tra dữ liệu DV-01..DV-14 (chu trình, tham chiếu, khối…)
analysis/   ── lịch học kỳ · trạng thái SV · ES/LS theo chu kỳ mở môn · rủi ro · chẩn đoán nhanh PC-xx
solver/     ── mô hình CP-SAT tích hợp (optimize | explain) · chiến lược lexicographic · đa dạng · MUS
verify/     ── bộ kiểm chứng độc lập: mọi phương án phải qua trước khi trả về
explain/    ── giải trình từng môn, thông điệp tiếng Việt
advisor/    ── tư vấn chuyên ngành · gợi ý kỳ tới · mô phỏng rớt môn
api/        ── FastAPI (REST + phục vụ giao diện đã build)
frontend/   ── React + TypeScript + Tailwind (giao diện tiếng Việt)
```

Thư mục `docs/` gồm:
- [`docs/model.md`](docs/model.md): mô hình toán và cách đối chiếu HC/SC với code, giải thích bằng ví dụ;
- [`docs/data-format.md`](docs/data-format.md): định dạng dữ liệu và cách tích hợp;
- [`docs/decisions.md`](docs/decisions.md): các quyết định nghiệp vụ (trả lời 6 câu hỏi của đặc tả);
- [`docs/demo.md`](docs/demo.md): kịch bản demo;
- [`docs/spec.md`](docs/spec.md): đặc tả gốc;
- [`docs/MVP_PLAN.md`](docs/MVP_PLAN.md): kế hoạch MVP.

## Kiểm thử

| Loại | Nội dung |
|---|---|
| Unit | validator, lịch học kỳ, ES/LS, từng ràng buộc HC trên dataset nhỏ, verifier, chẩn đoán nhanh, import CSV, tư vấn |
| Property (hypothesis) | Trên các bài toán ngẫu nhiên: solver kết luận khả thi ⇔ duyệt vét cạn tìm thấy lời giải; mọi lời giải của solver qua được verifier; MUS là tối thiểu |
| Nghiệm thu (pytest-bdd) | `backend/tests/acceptance/features/ac0*.feature`: giữ nguyên văn Given/When/Then AC-01..AC-07 của đặc tả |
| API | mọi endpoint với 5 sinh viên mẫu |
| E2E | `make e2e`: Playwright lập lộ trình, mở giải trình, chạy tư vấn và xem báo cáo xung đột |

## Giới hạn hiện tại và hướng phát triển

**Chưa có trong phiên bản này:**
- xếp thời khóa biểu tuần (chọn lớp học phần không trùng giờ);
- trợ lý hội thoại dùng LLM;
- cơ sở dữ liệu, đăng nhập SSO và phân quyền;
- đồng bộ tự động với hệ thống đào tạo;
- dự báo rớt môn bằng học máy từ dữ liệu lịch sử;
- dashboard cho khoa (dự báo nhu cầu mở lớp từ lộ trình của sinh viên).

**Tiên quyết** hiện chỉ hỗ trợ dạng "A và B"; trường hợp "A hoặc B" xử lý qua bảng môn tương đương.

**Thời gian chạy:** mỗi yêu cầu lập lộ trình (5 phương án) mất khoảng 1–8 giây trên 4 CPU. Có thể chỉnh bằng
biến môi trường `CPLAN_STAGE_TIME_LIMIT` (giới hạn giây cho mỗi stage) và `CPLAN_WORKERS` (số luồng).
