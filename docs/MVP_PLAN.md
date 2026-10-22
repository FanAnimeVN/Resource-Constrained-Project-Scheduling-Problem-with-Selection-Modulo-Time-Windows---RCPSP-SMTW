# Kế hoạch MVP: Hệ thống lập lộ trình học tập cá nhân hóa (RCPSP-SMTW), Khoa CNTT, ĐH KHTN ĐHQG-HCM

> **Trạng thái: đã thực thi đủ các mốc M0–M10.** Cách chạy và kết quả: xem `README.md`; các điểm khác so với kế hoạch: xem `docs/model.md` (mục 4).
> Nhánh làm việc: `claude/quirky-davinci-q3kngj`. Xong mỗi mốc thì commit rồi push. Chưa tạo PR khi bạn chưa yêu cầu.

---

## 1. Bối cảnh

- Repo hiện chỉ có `README.md` từ commit khởi tạo, nên dự án làm từ đầu.
- Đầu vào là bản đặc tả `ProjectTDTT.md` (file upload: `/root/.claude/uploads/424d88b1-e113-55c0-8ac2-745f6d9ec33f/6f189dfa-ProjectTDTT.md`, các mục 1–7). Bản đặc tả mô tả bài toán RCPSP-SMTW: vừa chọn học phần vừa xếp chúng vào các học kỳ, chịu giới hạn tín chỉ, đồ thị tiên quyết và lịch mở môn theo chu kỳ. Nó gồm các ràng buộc HC-01..HC-11, 4 chiến lược tối ưu, yêu cầu trả MUS khi vô nghiệm, tiêu chí nghiệm thu AC-01..AC-07 và kiến trúc 4 lớp.
- Mục tiêu cuối cùng là một hệ thống tích hợp cho nhà trường, làm được 3 việc: (1) gợi ý môn học và lộ trình đăng ký tín chỉ tối ưu qua nhiều học kỳ; (2) tư vấn chọn chuyên ngành theo từng sinh viên; (3) giải thích được mọi đề xuất, và không bao giờ trả về một lộ trình sai quy chế.
- **Những điều bạn đã chốt:** dùng FastAPI + React; để chức năng xếp thời khóa biểu tuần sang sau MVP; chưa tích hợp trợ lý AI, thay vào đó là phần giải trình tự động có cấu trúc; dữ liệu mẫu mô phỏng CTĐT CNTT 138 TC (từ K2020) của Khoa CNTT HCMUS.
- **Môi trường (đã kiểm tra):**
  - Có Python 3.13 và `uv`. Wheel `ortools 9.15` bản cp313 tải được từ PyPI.
  - Có Node 22 và npm 10.
  - Chromium cho Playwright (build 1194) có sẵn ở `/opt/pw-browsers`. Máy có 4 CPU.
  - Mọi trang `*.hcmus.edu.vn` bị network policy chặn (lỗi 403). Vì vậy dữ liệu mẫu được dựng từ các thông tin công khai đã tra được (mục 13), và mọi số liệu chưa xác minh được gắn `"source": "sample"`.

## 2. Phạm vi MVP

**Trong phạm vi MVP:**
1. **Lớp dữ liệu cấu hình:** 1 CTĐT (CNTT K2020+, 6 chuyên ngành) gồm danh mục môn, quan hệ phụ thuộc, lịch mở môn, cây khối kiến thức, quy chế và bảng môn tương đương. Lưu bằng JSON, import được từ CSV. Kèm một bộ kiểm tra dữ liệu.
2. **Engine lập lộ trình bằng CP-SAT:** chọn môn và xếp kỳ cùng lúc. Lộ trình phải thỏa:
   - các ràng buộc HC-01..HC-11;
   - điều kiện riêng của từng môn: số TC tích lũy tối thiểu, bắt buộc học ở kỳ cuối, GPA tối thiểu;
   - tùy chọn cá nhân: bật học hè, trần tín chỉ riêng, ghim hoặc loại môn, kỳ muốn tốt nghiệp, chuyên ngành.
3. **5 phương án:** `FAST_TRACK`, `BALANCED`, `RISK_AVERSE`, `SPECIALIZATION_FOCUS` và `PERSONALIZED` (cá nhân hóa theo trọng số sinh viên tự đặt). Kèm bảng so sánh chỉ số, và các phương án bảo đảm khác nhau.
4. **Giải trình:** giải thích cho từng môn trong lộ trình. Khi vô nghiệm thì trả báo cáo gồm chẩn đoán nhanh, MUS và gợi ý nới lỏng.
5. **Tư vấn chuyên ngành cá nhân hóa:** dựa trên học lực, sở thích, mục tiêu nghề nghiệp và tác động đến tiến độ (do solver tính).
6. **Gợi ý đăng ký kỳ tới:** danh sách môn nên đăng ký kèm môn thay thế, và chức năng mô phỏng "nếu rớt môn X".
7. **REST API** (có OpenAPI) và **Web UI tiếng Việt** viết bằng React.
8. **Kiểm thử:** unit, property-based, BDD cho AC-01..AC-07, API và e2e smoke. Có CI trên GitHub Actions; Docker Compose là tùy chọn.

**Ngoài phạm vi (để lộ trình phát triển sau, nhưng thiết kế sẵn điểm mở rộng):**
- xếp thời khóa biểu tuần và chọn lớp học phần;
- trợ lý hội thoại dùng LLM;
- cơ sở dữ liệu, đăng nhập SSO và phân quyền;
- đồng bộ tự động với hệ thống đào tạo (SIS);
- dự báo rớt môn bằng ML từ dữ liệu lịch sử;
- dashboard cho khoa (dự báo nhu cầu mở lớp, tổng hợp từ lộ trình của sinh viên);
- hỗ trợ nhiều CTĐT, nhiều khoa;
- tiên quyết dạng "A hoặc B". MVP chỉ hỗ trợ dạng "A và B", cộng với bảng môn tương đương.

## 3. Trả lời 6 câu hỏi nghiệp vụ ở Mục 5 của đặc tả

Mọi giá trị dưới đây đều nằm trong file dữ liệu, không viết cứng trong code.

| # | Câu hỏi | Mặc định cho MVP | Cấu hình ở |
|---|---|---|---|
| 1 | Ngưỡng TC mỗi kỳ | Kỳ chính 14–24 TC (khớp AC-03). Kỳ cuối được miễn mức sàn. Kỳ hè 0–8 TC, chỉ xếp khi sinh viên bật "Học hè". Có `load_rules` theo học lực: sinh viên bị cảnh báo học tập đăng ký trong khoảng 10–14 TC (giá trị mẫu). Kèm thêm hồ sơ quy chế `hcmus_clc_2025.json` (10–22 TC, lấy theo thông báo ĐKHP năm 2025–2026) để demo việc đổi quy chế. | `regulations/*.json` |
| 2 | 138 TC là "đúng bằng" hay "tối thiểu" | **Tối thiểu (≥ 138).** Tài liệu của Khoa ghi "SV có thể tích lũy nhiều hơn 138TC". Mục tiêu phụ là giảm tối đa số TC dư. Vẫn hỗ trợ chế độ `credit_rule: "exact"`. | `curriculum.json` |
| 3 | Học trước khác tiên quyết thế nào | **Tiên quyết:** phải ĐẠT A, và đạt điểm ≥ `min_grade` nếu có quy định. **Học trước:** chỉ cần đã HỌC A ở kỳ trước, kể cả khi rớt. **Song hành:** học A trước hoặc cùng kỳ với B. (Theo định nghĩa trong TT 08/2021/TT-BGDĐT.) | `dependencies.json` |
| 4 | Môn tương đương | Có hai loại: nhóm tương đương hai chiều (trường hợp đổi mã môn) và môn thay thế một chiều. Đạt môn tương đương thì coi như đạt môn gốc: thỏa tiên quyết và được tính vào khối. Hệ thống tự sinh ràng buộc loại trừ giữa các môn tương đương với nhau. | `equivalences.json` |
| 5 | Thời gian đào tạo | Chuẩn là 8 kỳ chính. Tối đa mặc định 12 kỳ chính (6 năm). **Con số này cần đối chiếu với QĐ 1175/QĐ-KHTN.** | `regulations/*.json` |
| 6 | Thế nào là "khác biệt có ý nghĩa" | Mỗi phương án tối ưu một mục tiêu khác nhau. Ma trận phân bổ (môn, kỳ) của hai phương án phải khác nhau ít nhất 1 môn; ràng buộc cắt (no-good cut) chỉ thêm vào khi hai phương án bị trùng. Báo cáo khoảng cách theo 3 thước đo: số môn khác kỳ, khác biệt tập môn tự chọn, chênh kỳ tốt nghiệp. | cấu hình engine |

Ngoài 6 câu trên, có thêm hai quyết định:
- Mức sàn W_min áp chặt cho mọi kỳ chính nằm giữa lộ trình, tức không được bỏ trống kỳ. Cờ `allow_empty_main_terms` mặc định là `false`.
- GDTC, GDQP và ngoại ngữ không tính vào 138 TC. Các môn này hiển thị dưới dạng checklist điều kiện tốt nghiệp và không đưa vào bài toán tối ưu.

## 4. Đề xuất cải tiến so với đặc tả (sẽ làm luôn)

1. **Dùng một mô hình CP-SAT duy nhất cho cả chọn môn lẫn xếp kỳ**, thay cho cách làm 2 giai đoạn (Knapsack rồi CP-SAT) của đặc tả.
   - Lý do: làm 2 giai đoạn thì giai đoạn 1 có thể chọn bộ môn tự chọn mà giai đoạn 2 không xếp được, vì vướng lịch mở môn hoặc tiên quyết.
   - Quy mô khoảng 100 môn × tối đa 20 kỳ, sau khi cắt tỉa còn khoảng 1–2 nghìn biến boolean, CP-SAT giải trong vài giây.
2. **Tính cửa sổ thời gian theo chu kỳ mở môn (ES/LS).** Lan truyền kỳ sớm nhất (ES) và muộn nhất (LS) cho từng môn, có xét HK1/HK2/Hè và năm chẵn/lẻ. Kết quả dùng để cắt bớt biến, và để phát hiện vô nghiệm ngay lập tức với thông điệp dễ hiểu (AC-05).
3. **Tối ưu theo thứ tự ưu tiên (lexicographic) cho từng chiến lược**, nên không phải dò trọng số. Riêng phương án cá nhân hóa dùng Compromise Programming:
   - lấy 4 phương án chiến lược làm bảng payoff, từ đó có điểm lý tưởng và điểm tệ nhất của từng mục tiêu;
   - chuẩn hóa các mục tiêu theo hai điểm đó;
   - tối thiểu hóa tổng có trọng số, với trọng số do sinh viên chọn.
4. **Định nghĩa rủi ro bằng "đệm học lại".** Môn nút cổ chai được ưu tiên xếp vào kỳ sao cho nếu rớt thì vẫn còn lượt mở kế tiếp trước hạn muộn nhất (LS) của môn đó. Cách này cụ thể và dễ giải thích hơn câu "xếp càng sớm càng tốt".
5. **Tìm MUS theo nhóm luật nghiệp vụ.**
   - Mỗi nhóm ràng buộc gắn với một assumption literal.
   - Lấy lõi xung đột (core) từ CP-SAT, sau đó lọc bằng deletion filter để ra tập tối thiểu.
   - Kết quả là tập xung đột tối thiểu được diễn đạt bằng ngôn ngữ quy chế, kèm gợi ý nới lỏng (bật học hè, gia hạn, tăng trần tín chỉ…).
6. **Bộ kiểm chứng độc lập (verifier)** viết bằng Python thuần.
   - Mọi phương án đều phải qua verifier trước khi trả về.
   - Verifier cũng là chuẩn đối chiếu (oracle) cho property-based test.
   - Nhờ đó cam kết "không trả phương án sai quy chế" vẫn giữ được ngay cả khi mô hình có lỗi.
7. **Giải thích "vì sao không học sớm hơn" bằng phép thử phản thực tế.** Thử dời môn sang một kỳ sớm hơn, để verifier chỉ ra luật nào bị vi phạm. Nếu không luật nào bị vi phạm thì nói rõ môn bị dời là do chiến lược tối ưu.
8. **Tư vấn chuyên ngành gắn với solver.** Mỗi chuyên ngành được chạy thử "what-if" để biết kỳ tốt nghiệp sớm nhất và số TC đã học được tận dụng. Điểm số minh bạch, có kèm độ tin cậy và độ ổn định của thứ hạng.
9. **Mô phỏng rớt môn.** Lập lại lộ trình với giả định sinh viên rớt một môn, để thấy rõ giá trị của phương án An toàn.

## 5. Kiến trúc và cấu trúc thư mục

```
docs/      MVP_PLAN.md (bản này), spec.md (đặc tả gốc mục 1–7), decisions.md, model.md, data-format.md, demo.md
data/hcmus_cntt_k2020/
  courses.json  dependencies.json  offerings.json  curriculum.json  equivalences.json  advisor.json
  regulations/{default.json, hcmus_clc_2025.json}
  students/{sv01_nam1_moi, sv02_nam2, sv03_nam3_no_mon, sv04_sap_het_han, sv05_chuyen_ma}.json
backend/   pyproject.toml   (package `curriculum_planner`, CLI `cplan`)
  src/curriculum_planner/
    domain/models.py            Pydantic v2: Course, Dependency(+Type), Offering, KnowledgeBlock(+SelectionRule),
                                Curriculum, Specialization, Regulation(+LoadRule), Equivalence, AcademicRecord(+Status),
                                StudentProfile, Preferences, Term(+TermKind), Plan, ScheduledCourse, Explanation,
                                Issue, InfeasibilityReport, ValidationReport
    data/loader.py              thư mục dataset → `Dataset` (cache theo (dataset, regulation))
    data/csv_import.py          CSV → JSON
    validation/validator.py     DV-01..DV-14 (Tarjan SCC)
    analysis/calendar.py        dãy học kỳ HK1/HK2/Hè, hạn chót, nhãn tiếng Việt
    analysis/student_state.py   chuẩn hóa hồ sơ (PASSED/EXEMPTED/IN_PROGRESS/FAILED, áp tương đương, GPA, TC theo khối)
    analysis/graph.py           ES/LS theo chu kỳ mở môn, chuỗi găng, điểm rủi ro, safe(c,t)
    analysis/prechecks.py       PC-01..PC-06
    solver/model_builder.py     dựng CP-SAT, mode `optimize` | `explain`
    solver/strategies.py        mỗi chiến lược = danh sách stage tối ưu theo thứ tự ưu tiên
    solver/engine.py            validate → precheck → solve → đa dạng → verify → explain
    solver/mus.py               core + deletion filter + gợi ý nới lỏng
    verify/plan_verifier.py     oracle độc lập
    explain/explainer.py, explain/messages_vi.py
    advisor/specialization.py, advisor/next_term.py, advisor/what_if.py
    metrics.py, cli.py
    api/app.py, api/schemas.py, api/routers/*.py
  tests/{unit, property, acceptance/features/*.feature, api, fixtures}
frontend/  Vite + React + TS + Tailwind v4; react-router, @tanstack/react-query, zustand, recharts,
           @xyflow/react + @dagrejs/dagre, openapi-typescript
  src/{api, store, pages, components, lib}   e2e/smoke.spec.ts
Makefile, .github/workflows/ci.yml, docker-compose.yml + Dockerfile (tùy chọn)
```

**Nguyên tắc tách lớp (đáp ứng AC-06):** các module `solver`, `explain` và `advisor` chỉ đọc 3 thứ là `Dataset`, `StudentProfile` và `Regulation`. Không có số liệu quy chế nào nằm trong code.

## 6. Dữ liệu

### 6.1 Schema (các trường chính)

- **Course:**
  - định danh và khối lượng: `id`, `name`, `credits` (nguyên dương), `workload` (thang 1–5), `tags[topic]`, `is_active`;
  - điều kiện học (không bắt buộc khai báo): `min_accumulated_credits`, `final_term_only`, `min_gpa`, `historical_fail_rate`;
  - khác: `counts_toward_total` (mặc định là true), `source`.
- **Dependency:** `source`, `target`, `type` ∈ {`PREREQUISITE`, `PRE_COURSE`, `CO_REQUISITE`, `MUTUALLY_EXCLUSIVE`}, và `min_grade?`.
- **Offering:** `course`, `terms` ⊆ {HK1, HK2, HE}, `year_parity` ∈ {null, odd, even}. File import nhận được cả các enum gốc của đặc tả (`FALL_ONLY`, `SPRING_ONLY`, `EVERY_TERM`, `SUMMER_ALLOWED`, `ODD_YEARS_ONLY`).
- **KnowledgeBlock** (dạng cây):
  - `id`, `name`, `rule` ∈ {`ALL_MANDATORY`, `MIN_CREDITS`, `PICK_K_OF_N`}, `required_credits`, `k?`, `specialization?`;
  - mỗi khối có **hoặc** `children[]` **hoặc** `courses[{id, mandatory}]`, tức chỉ khối lá mới chứa môn;
  - khối có `specialization_group: true` thì các khối con của nó là các chuyên ngành.
- **Curriculum:** `id`, `total_credits_required` (138), `credit_rule` ∈ {`at_least`, `exact`}, `standard_main_terms` (8), `blocks`, `specializations[{id, name, block_id, description}]`, `graduation_conditions[]` (GDTC, GDQP, chuẩn ngoại ngữ; dùng làm checklist).
- **Regulation:**
  - `min_credits_main`, `max_credits_main`, `max_credits_summer`, `max_main_terms`;
  - `final_term_min_exempt`, `allow_empty_main_terms`, `allow_double_count_across_blocks` (mặc định false);
  - `load_rules[{when: academic_warning | gpa_at_least:x, min_credits_main?, max_credits_main?}]`.
- **Equivalence:** `canonical`, `equivalents[]`, `kind` ∈ {`EQUIVALENT`, `SUBSTITUTE`}.
- **advisor.json:**
  - `topics` (id → nhãn tiếng Việt);
  - `careers` (id → {name, topics});
  - `specializations` (id → {`topic_profile`, `indicator_courses` (môn → trọng số), `careers[]`});
  - `default_weights` = {academic .35, interest .30, career .15, progress .20}.
- **StudentProfile:**
  - định danh và tiến độ: `id`, `name`, `cohort_year`, `curriculum_id`, `next_term {year, kind}`;
  - kết quả học tập: `records[{course, status ∈ PASSED|FAILED|EXEMPTED|IN_PROGRESS, grade?, term?}]`, `academic_warning`;
  - định hướng: `declared_specialization?`, `interests{topic: 1..5}`, `career_goals[]`;
  - `preferences`: `summer_enabled`, `personal_max_credits`, `target_graduation_term`, `pinned[{course, term}]`, `excluded[]`, `objective_weights{fast, balance, risk, interest}`.

### 6.2 Bộ dữ liệu mẫu `hcmus_cntt_k2020`

Khoảng 90–100 môn. Mọi bản ghi chưa xác minh đều gắn `"source": "sample"`.

```
CNTT_K2020 (≥138)
├─ DC  Giáo dục đại cương 56
│  ├─ LLCT 11 (ALL): BAA00101 Triết học Mác–Lênin 3, BAA00102 KTCT 2, BAA00103 CNXHKH 2, BAA00104 LS ĐCSVN 2, BAA00003 TT HCM 2
│  ├─ XH–KT–KN 5 (MIN): BAA00004 Pháp luật đại cương 3 (BB) + 2 TC tự chọn kỹ năng/kinh tế
│  ├─ Toán–KHTN–CN–MT 36 (MIN): BB vi tích phân 1B/2B, ĐSTT, XSTK, toán rời rạc, toán tổ hợp, vật lý ĐC 1/2 … + tự chọn KHTN cho đủ 36
│  └─ Tin học 4 (ALL): CSC00004 Nhập môn CNTT 4
├─ CSN Cơ sở ngành 38 (ALL): CSC10001 NMLT 4, CSC10002 KTLT 4, CSC10003 PPLT HĐT 4, CSC10004 CTDL&GT 4, CSC10006 CSDL 4,
│                             CSC10007 HĐH 4, CSC10008 MMT 4, CSC10009 HTMT 2, CSC13002 Nhập môn CNPM 4, CSC14003 Cơ sở TTNT 4
├─ CN  Chuyên ngành 24 (specialization_group): KHMT · CNPM · HTTT · MMT&VT · Công nghệ tri thức · Thị giác MT & Robot
│      (mỗi chuyên ngành: 3 môn BB = 12 TC + chọn ≥ 12 TC từ 5–7 môn tự chọn)
├─ TCTD Tự chọn tự do 10 (MIN): môn của chuyên ngành khác + vài môn mở rộng
└─ TN  Tốt nghiệp 10 (MIN): CSC10251 Khóa luận TN 10 (≥110 TC tích lũy, GPA ≥ 7.0, học ở kỳ cuối)
                           ⊗ {CSC10252 Thực tập TN 4, CSC10253 Đồ án TN 6} (≥100 TC)
```

**Yêu cầu với dữ liệu mẫu:**
- Lịch mở môn phải có đủ các dạng: chỉ HK1, chỉ HK2, cả hai kỳ, cho phép học hè, và ít nhất 1 môn chỉ mở năm lẻ. Mục đích là demo được tình huống "lệch pha kỳ mở".
- Khoảng 40 cạnh phụ thuộc, có đủ 4 loại. Phải có một chuỗi dài ít nhất 5 môn (CSC10001→CSC10002→CSC10004→CSC14003→CSC14005→…) để demo AC-05.
- Tổng `required_credits` của các khối cấp cao nhất phải bằng 138.
- Gắn `historical_fail_rate` mẫu cho vài môn khó.
- Các điểm đã xác minh thì giữ đúng:
  - CSC10001–CSC10004 đều 4 TC, đều bắt buộc;
  - CSC10002 và CSC10003 có học trước là CSC10001;
  - CSC10004 có học trước là CSC10002.

**5 sinh viên mẫu** (bối cảnh: hiện là HK1 năm học 2026–2027):

| File | Hồ sơ | Dùng để demo |
|---|---|---|
| sv01 | Tân sinh viên K2026, chưa có điểm, thích AI và dữ liệu. Lập lộ trình từ đầu khóa (HK1 2026–2027). | Trường hợp cơ bản. |
| sv02 | K2025, đã xong 2 kỳ và đang học kỳ thứ 3, GPA khoảng 7.8, chưa chọn chuyên ngành, thích phần mềm và web. | Gợi ý chuyên ngành. |
| sv03 | K2024, rớt CSC10004 và một môn toán, đang bị cảnh báo học tập (tải 10–14 TC). | Lộ trình rủi ro. |
| sv04 | K2021, đã học 10 kỳ (hạn là 12 kỳ), còn một chuỗi bắt buộc gồm 4 môn nối tiếp. | **Vô nghiệm**, demo AC-05/MUS. |
| sv05 | Chuyển từ CTĐT cũ, có các mã môn cũ tương đương. | Môn tương đương, AC-04. |

## 7. Engine

### 7.1 Validator (DV-xx)

Validator kiểm tra 14 nhóm lỗi:
- **DV-01 Trùng mã môn.**
- **DV-02 Tham chiếu tới mã môn không tồn tại.**
- **DV-03 Số TC không hợp lệ.**
- **DV-04 Chu trình phụ thuộc.**
  - Tìm các thành phần liên thông mạnh (SCC) bằng Tarjan, chạy trên toàn bộ các cạnh.
  - Chỉ báo lỗi khi trong SCC có ít nhất một cạnh *bắt buộc học trước* (tiên quyết hoặc học trước).
  - Song hành hai chiều là hợp lệ, vì nó chỉ có nghĩa là hai môn phải học cùng kỳ.
- **DV-05 Môn không có lịch mở.** Nếu môn đó là bắt buộc thì báo lỗi.
- **DV-06 Khối không thể đủ TC.** Ví dụ: tổng TC các môn trong khối nhỏ hơn yêu cầu, hoặc k > N.
- **DV-07 Cây khối sai cấu trúc.**
- **DV-08 Tổng TC các khối cấp cao nhất khác 138.** Đây là cảnh báo, không phải lỗi.
- **DV-09 Hai môn bắt buộc loại trừ nhau.**
- **DV-10 Cấu hình chuyên ngành sai.**
- **DV-11 Môn đã ngừng dạy nhưng vẫn là bắt buộc.**
- **DV-12 Bảng tương đương xung đột.**
- **DV-13 Phụ thuộc trỏ ra ngoài CTĐT.**
- **DV-14 CTĐT có chuỗi găng dài hơn số kỳ chuẩn.** Đây là cảnh báo dành cho khoa.

Nếu có lỗi DV, engine dừng lại và API trả về 422 kèm báo cáo.

### 7.2 Lịch học kỳ và trạng thái sinh viên

**Lịch học kỳ:**
- Mỗi kỳ được biểu diễn là (năm học bắt đầu, loại kỳ), theo thứ tự HK1 → HK2 → Hè.
- Dãy kỳ chạy từ `next_term` đến hạn chót. Hạn chót là kỳ chính thứ `max_main_terms` tính từ khóa, gồm cả kỳ hè cùng năm học.
- Ở mode `explain` (dùng khi tìm MUS), dãy kỳ kéo dài thêm 4 kỳ chính sau hạn chót. Phần này chỉ để chẩn đoán xem cần gia hạn bao lâu.
- Kỳ hè chỉ xuất hiện khi sinh viên bật học hè.

**`student_state`** chuẩn hóa hồ sơ sinh viên:
- quy đổi mã môn tương đương về mã gốc;
- tập `satisfied` gồm các môn PASSED và EXEMPTED, cộng thêm IN_PROGRESS nếu `assume_in_progress_pass` (mặc định là true);
- tập `attempted` gồm `satisfied` cộng các môn FAILED;
- GPA tính theo trọng số TC, kèm số TC đã tích lũy theo từng khối;
- cảnh báo khi sinh viên có môn đã học nhưng không thuộc CTĐT (môn đó không được tính).

### 7.3 Phân tích đồ thị (`graph.py`)

- **`next_offered(c, t)` / `prev_offered(c, t)`:** tìm kỳ mở gần nhất về phía sau hoặc phía trước, theo loại kỳ và năm chẵn/lẻ.
- **ES_c (kỳ sớm nhất của môn c):** duyệt theo thứ tự topo trên các môn chưa thỏa.
  - Cạnh tiên quyết và học trước cộng δ = 1; cạnh song hành cộng δ = 0.
  - `ES_c = next_offered(c, max(t0, max_pred(ES_a + δ)))`.
  - Ràng buộc `min_accumulated_credits` cho thêm một cận dưới: kỳ đầu tiên mà sức chứa W_max cộng dồn đạt được số TC yêu cầu.
- **LS_c (kỳ muộn nhất, theo hạn D):** duyệt topo ngược, chỉ đi qua các môn kế tiếp **bắt buộc**, để việc cắt tỉa không bao giờ loại mất lời giải hợp lệ.
  - `LS_c = prev_offered(c, min(D, min_succ(LS_b − δ)))`.
- **Chuỗi găng:** truy vết ngược môn nào quyết định giá trị ES để in ra chuỗi cụ thể. Dùng cho PC-01 và phần giải trình.
- **`risk_c`** (số nguyên 1–20), cộng từ các thành phần:
  - số môn hậu duệ còn phải học;
  - độ dài chuỗi phía sau;
  - môn chỉ mở 1 lần/năm;
  - `historical_fail_rate`;
  - sinh viên từng rớt môn này.

  Giữ lại từng thành phần để giải trình.
- **`safe(c, t)`:** đúng khi `next_offered(c, t+1) ≤ LS_c(g_target)`, tức là nếu rớt ở kỳ t thì vẫn học lại kịp.

### 7.4 Chẩn đoán nhanh (prechecks)

Đây là các điều kiện cần. Vi phạm bất kỳ điều kiện nào thì chắc chắn vô nghiệm, và hệ thống trả báo cáo ngay, không cần gọi solver.

- **PC-01: chuỗi tiên quyết dài hơn số kỳ còn lại**, tức có môn bắt buộc mà ES > D. Thông điệp mẫu: *"Chuỗi tiên quyết A → B → C → D cần tối thiểu 4 học kỳ nhưng chỉ còn 2 học kỳ trước hạn tối đa (HK2 2026–2027)."*
- **PC-02:** số TC tối thiểu còn thiếu lớn hơn tổng sức chứa của các kỳ còn lại.
- **PC-03:** môn bắt buộc không mở trong thời gian còn lại, hoặc đã ngừng dạy.
- **PC-04:** khối không thể đủ TC sau khi loại các môn bị cấm hoặc không mở.
- **PC-05:** hai môn bắt buộc loại trừ nhau.
- **PC-06:** môn bắt buộc mà sinh viên không đủ GPA, và không có môn thay thế.

### 7.5 Mô hình CP-SAT (`model_builder.build(dataset, state, regulation, prefs, mode)`)

**Ký hiệu:**
- T: các kỳ trong khoảng lập kế hoạch, đánh chỉ số thời gian 0..H−1.
- cand: các môn chưa thỏa mà sinh viên học được.
- A(c): tập kỳ được phép xếp môn c.
  - Mode `optimize`: A(c) là các kỳ có mở môn và nằm trong khoảng [ES_c, LS_c].
  - Mode `explain`: A(c) là toàn bộ các kỳ; việc cấm kỳ không mở được đưa thành một nhóm ràng buộc riêng.

**Biến:**
- `x[c,t]` ∈ {0,1} với t ∈ A(c): môn c xếp vào kỳ t. `sel[c] = Σ_t x[c,t] ≤ 1`.
- `spec[k]`: chuyên ngành k được chọn, với Σ spec = 1. Biến này bị cố định khi sinh viên đã chọn chuyên ngành, hoặc chọn "auto" (lấy chuyên ngành đứng đầu bảng tư vấn).
- `y[c,b]` ∈ {0,1}: môn c (đã thỏa hoặc được chọn) được tính vào khối lá b.
- `load[t] = Σ w_c·x[c,t]` (tổng TC kỳ t) và `wl[t] = Σ workload_c·x[c,t]` (tổng độ nặng kỳ t).
- `le[t]` ∈ {0,1}: kỳ t nằm trong lộ trình. Ràng buộc đơn điệu `le[t+1] ⇒ le[t]`.
  - `grad = Σ_t le[t] − 1` là chỉ số kỳ tốt nghiệp.
  - `fin[t] = le[t] − le[t+1]` bằng 1 đúng ở kỳ cuối.

**Ràng buộc.** Ở mode `explain`, mỗi gạch đầu dòng dưới đây là một hoặc nhiều nhóm có literal riêng.

- **HC-02:** môn đã thỏa (kể cả qua tương đương) không có mặt trong cand; `sel ≤ 1`.
- **HC-04/05/06** (mỗi cạnh là một nhóm). Khi môn trước a chưa thỏa điều kiện:
  - với tiên quyết, nghĩa là chưa ĐẠT a; với học trước và song hành, nghĩa là chưa từng HỌC a;
  - thì với mọi t ∈ A(b): `x[b,t] ≤ Σ_{t'∈A(a), t'<t} x[a,t']`. Với song hành, điều kiện là `t' ≤ t`;
  - nếu a không học được (a ∉ cand) thì `sel[b] = 0`.
- **HC-07** (mỗi cặp là một nhóm): `Σ y[a,·] + Σ y[b,·] ≤ 1` và `sel[a] + sel[b] ≤ 1`.
- **HC-03** (mỗi khối là một nhóm; mỗi môn bắt buộc là một nhóm):
  - `y[c,b] ≤ sel[c]` (môn đã thỏa thì `y ≤ 1`);
  - `Σ_b y[c,b] ≤ 1`, trừ khi bật `allow_double_count`;
  - môn bắt buộc phải được học hoặc đã đạt, và phải tính vào đúng khối của nó (`y[c,b] = 1`);
  - với mọi nút B: `Σ_{lá b⊆B} Σ_c w_c·y[c,b] ≥ req(B)`. Với `PICK_K_OF_N` thì `Σ y ≥ k`;
  - khối của chuyên ngành k chỉ áp dụng khi `spec[k]` bật, và `y[c,b] ≤ spec[k]`;
  - với môn có thuộc ít nhất một khối, `sel[c] ≤ Σ_b y[c,b]`, nghĩa là không xếp môn "vô ích" không tính vào đâu.
- **HC-01:** `Σ_{c,b} w_c·y[c,b] ≥ 138`. Nếu `credit_rule` là `exact` thì dấu là `=`.
- **HC-08** (mỗi kỳ chính có hai nhóm riêng: trần và sàn):
  - trần: `load[t] ≤ W_max_eff`, với W_max_eff là giá trị nhỏ nhất trong 3 nguồn: quy chế, `load_rules`, trần cá nhân;
  - sàn: `load[t] ≥ W_min·le[t+1]`. Kỳ cuối được miễn nhờ `final_term_min_exempt`; nếu không miễn thì dùng `W_min·le[t]`;
  - nếu `allow_empty_main_terms` bật thì mức sàn chỉ áp khi `load[t] ≥ 1`.
- **HC-09:** với kỳ hè, `load[t] ≤ W_max_summer`.
- **HC-10** (mỗi môn là một nhóm): `x[c,t] = 0` ở các kỳ không mở môn. Ở mode `optimize` thì việc này đã được cắt tỉa sẵn qua A(c).
- **HC-11:** `grad ≤ D`.
- **Định nghĩa kỳ tốt nghiệp:** `x[c,t] ≤ le[t]` và `load[t] ≥ fin[t]`, tức kỳ tốt nghiệp phải có ít nhất một môn.
- **Điều kiện môn:**
  - tích lũy tối thiểu M_c: `x[c,t] ⇒ passed_counted + Σ_{t'<t} load[t'] ≥ M_c`;
  - chỉ học kỳ cuối: `x[c,t] ≤ fin[t]`;
  - GPA tối thiểu: lọc ngay khỏi cand.
- **Tùy chọn của sinh viên** (mỗi mục là một nhóm PREF):
  - ghim môn: `x[c,t] = 1`;
  - loại môn: `sel[c] = 0`;
  - kỳ tốt nghiệp mong muốn: `grad ≤ g_user`.

**Các biểu thức mục tiêu dùng chung:**
- `f_grad = grad`: kỳ tốt nghiệp.
- `f_summer = Σ_{hè} used[t]`: số kỳ hè dùng tới, với `used[t] ⇔ load[t] ≥ 1`.
- `f_credits = Σ w_c·sel[c]`: tổng TC phải học thêm.
- `f_front = Σ w_c·t·x[c,t]`: càng nhỏ thì môn càng dồn về sớm.
- `f_sq = Σ_{kỳ chính} sq[t]` với `sq[t] = load[t]²` (dùng `add_multiplication_equality`).
- `f_peak = max_t wl[t]`: độ nặng của kỳ nặng nhất.
- `f_safe = Σ risk_c·Σ_{t: safe(c,t)} x[c,t]`: phần rủi ro được che bởi đệm học lại.
- `f_early = Σ risk_c·t·x[c,t]`: môn rủi ro được xếp sớm đến đâu.
- `f_pref = Σ_{c tự chọn} pref_c·w_c·sel[c]`. Trong đó `pref_c` (0–10) là độ khớp giữa `tags` của môn và sở thích sinh viên; nếu sinh viên chưa khai sở thích thì dùng hồ sơ chủ đề của chuyên ngành.

### 7.6 Các chiến lược (tối ưu theo thứ tự ưu tiên)

Mỗi chiến lược gồm nhiều stage. Sau mỗi stage, cố định giá trị tối ưu vừa tìm được (dùng `≤ best` nếu stage đó chỉ đạt FEASIBLE), rồi dùng `add_hint` với lời giải cũ để tăng tốc stage sau.

| Chiến lược | Thứ tự các stage |
|---|---|
| FAST_TRACK | min f_grad → min f_summer → min f_credits → min f_front |
| BALANCED | Với mỗi g ∈ [g_fast, g_target], chỉ xét các chỉ số là kỳ chính (tối đa 4 giá trị, ưu tiên các giá trị gần g_target): cố định grad = g, rồi min f_summer → min f_credits → min f_sq → min f_peak. Chọn g cho độ lệch chuẩn tải kỳ chính nhỏ nhất; nếu bằng nhau thì chọn g sớm hơn. |
| RISK_AVERSE | grad ≤ g_target → max f_safe → min f_early → min f_credits → min f_sq |
| SPECIALIZATION_FOCUS | grad ≤ g_target → max f_pref → min f_credits → min f_sq |
| PERSONALIZED | Chạy sau 4 chiến lược trên. Dùng 4 phương án đó làm bảng payoff để có điểm lý tưởng z* và điểm tệ nhất zᴺ cho các mục tiêu (f_grad, f_sq, −f_safe, −f_pref). Tối thiểu `Σ round(1000·α_k/(zᴺ_k − z*_k))·f_k`, bỏ thành phần nào có zᴺ = z*. Sau đó min f_credits. Nếu kết quả trùng một phương án khác thì gắn nhãn `duplicate_of`, không ép phải khác. |

Trong đó:
- `g_target = max(g_fast, kỳ tốt nghiệp chuẩn hoặc kỳ sinh viên mong muốn)`.
- Cấu hình solver: `num_workers = min(4, số CPU)`, `max_time_in_seconds` = 3 cho mỗi stage (cấu hình được).
- `solver_status` (OPTIMAL hoặc FEASIBLE) được ghi vào metrics của từng phương án.
- Chạy đa luồng thì kết quả không tất định giữa các lần chạy. Vì vậy test chỉ kiểm tính chất và chỉ số, không so sánh nguyên văn lộ trình.

### 7.7 Đa dạng và so sánh

- Áp dụng cho 4 phương án chiến lược. Nếu ma trận phân bổ của một phương án trùng hoàn toàn với phương án trước đó:
  - giải lại stage cuối, giữ nguyên ràng buộc giá trị tối ưu, và thêm cut `Σ_{(c,t)∈P} x[c,t] ≤ |P| − 1`;
  - nếu thêm cut mà vô nghiệm thì giữ phương án cũ và gắn nhãn `duplicate_of`.
- Khoảng cách giữa hai phương án = số môn khác kỳ + |hiệu đối xứng của tập môn tự chọn| + |chênh kỳ tốt nghiệp|.
- Metrics của mỗi phương án:
  - tiến độ: kỳ tốt nghiệp, số kỳ chính còn lại;
  - tín chỉ: TC phải học thêm, tổng TC, TC dư;
  - độ cân bằng: `load_std`, tải cao nhất và thấp nhất, workload đỉnh, số kỳ hè;
  - rủi ro và sở thích: `risk_coverage` (= f_safe chia tổng trọng số rủi ro), `interest_score`, `focus_ratio`;
  - thông tin chạy: `solver_status`, `solve_ms`.

### 7.8 Verifier (`plan_verifier.py`)

- Kiểm tra lại toàn bộ: HC-01..HC-11, các điều kiện môn và các tùy chọn của sinh viên.
- Phần cấu trúc khối được kiểm qua chứng chỉ `counted_block` mà phương án tự khai cho từng môn, kể cả môn đã đạt (lấy từ biến y).
- Kết quả là danh sách vi phạm, mỗi vi phạm có mã HC.
- Engine chạy verifier trên mọi phương án. Phương án nào có vi phạm thì bị loại và ghi log lỗi; tuyệt đối không trả về.

### 7.9 MUS (`mus.py`)

1. Dựng mô hình ở mode `explain`. Mỗi nhóm ràng buộc ứng với một literal và có metadata `{code, message_vi, courses, terms}`.
2. Giải với assumptions, đặt `num_workers = 1` để lõi xung đột ổn định, rồi lấy lõi qua `sufficient_assumptions_for_infeasibility()`.
3. Lọc lõi bằng deletion filter: thử bỏ từng phần tử, mỗi lần thử có timeout. Kết quả UNKNOWN thì giữ phần tử đó lại và gắn `minimal = false`. Tổng ngân sách là 20 giây.
4. Sinh gợi ý nới lỏng.
   - Áp dụng với các nhóm nới được: học hè, hạn chót, trần tải, ghim/loại môn, kỳ mong muốn, mức sàn.
   - Với mỗi nhóm như vậy, giải lại mô hình đầy đủ nhưng bỏ nhóm đó.
   - Nếu khả thi thì gợi ý: *"Nếu {nới X} thì có thể tốt nghiệp vào {kỳ}"*.

Báo cáo vô nghiệm gồm: các vấn đề prechecks phát hiện (nếu có), MUS, và các gợi ý.

### 7.10 Giải trình (`explainer.py` + `messages_vi.py`)

Mỗi môn trong phương án có 4 phần giải trình:

- **Vì sao chọn môn này:**
  - `MANDATORY`: môn bắt buộc của khối X;
  - `ELECTIVE`: môn tự chọn để đủ TC của khối X, kèm lý do như khớp sở thích, mở khóa môn khác đã chọn, ít TC;
  - `REQUIRED_AS_PREREQ`: cần học để làm tiên quyết cho môn khác.
- **Vì sao xếp ở kỳ này:**
  - kỳ sớm nhất có thể trong lộ trình là kỳ mở đầu tiên sau các môn trước của nó (theo kỳ thực tế đã xếp);
  - với mỗi kỳ mở sớm hơn t' < t, thử dời môn sang t' và chạy verifier để biết nguyên nhân: môn trước chưa học (HC-04), kỳ đó không mở (HC-10), kỳ đó đã đầy (HC-08), chưa đủ TC tích lũy, hoặc môn phải học kỳ cuối;
  - nếu dời sang t' mà không vi phạm luật nào thì ghi rõ: "dời theo chiến lược {mục tiêu}".
- **Phụ thuộc:**
  - môn này cần những môn nào (đã đạt, hoặc xếp ở kỳ nào);
  - môn này mở khóa những môn nào;
  - môn có nằm trên chuỗi găng không.
- **Rủi ro:** điểm rủi ro và các thành phần của nó; môn có đệm học lại không, nếu có thì kỳ học lại là kỳ nào.

Ở cấp phương án, hệ thống tự sinh 3–5 câu nổi bật. Ví dụ: "Tốt nghiệp HK2 2029–2030, sớm hơn chuẩn 1 kỳ nhờ 2 kỳ hè". Mọi thông điệp viết bằng template trong `messages_vi.py` và đều có test.

### 7.11 Tư vấn chuyên ngành (`advisor/specialization.py`)

Mỗi chuyên ngành k được chấm 4 điểm thành phần, đều trong khoảng 0–1:

- **A_k, học lực:** trung bình có trọng số điểm các môn chỉ báo (quy thang 10 về 0..1), co dần về GPA chung (shrinkage, m = 2). Sinh viên chưa có điểm nhận 0.5 và độ tin cậy "thấp".
- **I_k, sở thích:** độ tương đồng cosine giữa vector sở thích của sinh viên và `topic_profile` của chuyên ngành.
- **C_k, nghề nghiệp:** tỉ lệ mục tiêu nghề của sinh viên nằm trong `careers` của chuyên ngành. Không chọn mục tiêu nghề thì nhận mức trung tính 0.5.
- **P_k, tiến độ:**
  - Chạy what-if bằng FAST (stage 1–2) với `spec = k`, để biết kỳ tốt nghiệp sớm nhất g_k và số TC đã đạt tính được vào khối k.
  - Chuẩn hóa so với các chuyên ngành khác.
  - Nếu vô nghiệm thì P_k = 0, kèm lý do.

**Điểm tổng:** `S_k = Σ trọng số·thành phần`. Trọng số mặc định là .35 / .30 / .15 / .20 và sinh viên chỉnh được.

**Kết quả trả về:**
- bảng xếp hạng kèm điểm từng thành phần;
- các gạch đầu dòng giải thích: môn chỉ báo nổi bật, chủ đề khớp, nghề khớp, tác động tiến độ (ví dụ: "+1 kỳ vì chuỗi CSC11xxx chỉ mở HK1");
- độ ổn định: chuyên ngành đứng đầu có giữ nguyên khi nhiễu trọng số ±0.1 hay không.

Khi lập lộ trình, chuyên ngành "auto" chính là chuyên ngành đứng đầu bảng này.

### 7.12 Gợi ý kỳ tới và mô phỏng (`next_term.py`, `what_if.py`)

**Gợi ý kỳ tới:**
- **R (danh sách gợi ý):** các môn ở kỳ đầu tiên của phương án đang chọn, mặc định là PERSONALIZED.
- **E (các môn đủ điều kiện):** môn có mở ở kỳ tới và thỏa mọi điều kiện: đủ tiên quyết/học trước, đủ TC tích lũy và GPA, và còn tính được vào một khối chưa đủ. Môn song hành được phép đăng ký cùng kỳ.
- **Môn thay thế:** các môn trong E nhưng không có trong R, xếp hạng theo: bắt buộc hay không, điểm rủi ro, số môn mở khóa được, độ khớp sở thích. Mỗi môn kèm lý do.
- **Cảnh báo**, ví dụ: "Môn chỉ mở HK1, bỏ lỡ kỳ này sẽ phải chờ 1 năm".

**Mô phỏng rớt môn — `simulate_fail(plan, course, term)`:**
1. Coi như sinh viên đã đạt mọi môn của phương án xếp trước kỳ đó, và mọi môn cùng kỳ trừ môn bị rớt.
2. Đánh dấu môn bị rớt là FAILED, đặt kỳ tiếp theo là kỳ ngay sau.
3. Lập lại lộ trình bằng FAST và PERSONALIZED.
4. Trả về độ chênh kỳ tốt nghiệp và lộ trình mới.

## 8. API (FastAPI, tiền tố `/api`)

Các endpoint viết dạng `def` đồng bộ để FastAPI tự chạy trong threadpool.

| Method | Path | Trả về |
|---|---|---|
| GET | `/health` | — |
| GET | `/datasets` | Danh sách dataset và các hồ sơ quy chế. |
| GET | `/datasets/{ds}/curriculum` | Cây khối và danh sách chuyên ngành. |
| GET | `/datasets/{ds}/courses` | Môn học, phụ thuộc và lịch mở (dùng để vẽ đồ thị). |
| GET | `/datasets/{ds}/validation` | ValidationReport. |
| GET | `/datasets/{ds}/students[/{id}]` | Sinh viên mẫu. |
| POST | `/plans` | Nhận `{dataset, regulation, student \| student_id, preferences, strategies?, simulate_fail?}`. Trả `{status: OK\|INFEASIBLE\|COMPLETED\|DATA_ERROR, plans[], comparison, infeasibility?, warnings[], timings}`. |
| POST | `/advisor/specializations` | Bảng xếp hạng chuyên ngành. |
| POST | `/recommendations/next-term` | Danh sách gợi ý và môn thay thế. |
| POST | `/what-if/fail` | Lộ trình mới và độ chênh. |
| POST | `/datasets/validate-upload` | (Mở rộng thêm nếu kịp.) Nhận file zip CSV, trả báo cáo kiểm tra, không lưu lại. |

- Vô nghiệm **không phải lỗi HTTP**: API vẫn trả 200, với `status` là `INFEASIBLE`.
- Lỗi dữ liệu trả 422.
- CLI `cplan` có các lệnh: `validate`, `plan`, `advise`, `import-csv`, `export-openapi`.

## 9. Frontend (React, giao diện tiếng Việt)

**Thiết lập:**
- Kiểu TypeScript cho API được sinh tự động từ OpenAPI (`cplan export-openapi` rồi `openapi-typescript`, ra `src/api/schema.d.ts`).
- Vite proxy chuyển `/api` sang `:8000`.
- zustand giữ hồ sơ và kết quả hiện tại; react-query lo phần gọi API.

**Các trang:**
1. **Hồ sơ (`/`):**
   - Chọn sinh viên mẫu, hoặc tự chỉnh hồ sơ: bảng môn kèm trạng thái và điểm (tìm được, nhóm theo khối), kỳ tiếp theo, cảnh báo học tập.
   - Tùy chọn: học hè, trần TC cá nhân, kỳ muốn tốt nghiệp, chuyên ngành (hoặc "Để hệ thống gợi ý"), ghim/loại môn, bộ quy chế.
   - Thanh trượt trọng số: Nhanh / Cân bằng / An toàn / Sở thích.
   - Nút **Lập lộ trình**.
2. **Lộ trình (`/plans`):**
   - Mỗi phương án một tab.
   - `TermGrid`: mỗi cột là một kỳ. Thẻ môn tô màu theo khối, gắn nhãn "găng", "hiếm mở", "rủi ro".
   - Thanh tải TC mỗi kỳ, có vạch min/max; thanh tiến độ của từng khối.
   - Bấm vào thẻ môn mở `ExplanationDrawer`: vì sao chọn, vì sao kỳ này, phụ thuộc, rủi ro, và nút "Mô phỏng rớt môn này".
3. **So sánh (`/compare`):** bảng chỉ số, biểu đồ tải theo kỳ (Recharts) chồng các phương án lên nhau, ma trận khoảng cách.
4. **Tư vấn chuyên ngành (`/advisor`):**
   - Form sở thích (thang 1–5) và mục tiêu nghề nghiệp.
   - Thẻ xếp hạng có thanh điểm thành phần A/I/C/P, lý do, kỳ tốt nghiệp what-if, độ tin cậy và độ ổn định.
   - Nút "Chọn và lập lộ trình".
5. **Đăng ký kỳ tới (`/next-term`):** danh sách gợi ý có checkbox, bộ đếm TC so với giới hạn, môn thay thế kèm lý do, các cảnh báo.
6. **Chẩn đoán** (chỉ hiện khi vô nghiệm):
   - Danh sách xung đột, mỗi xung đột có mã luật, thông điệp và các môn liên quan.
   - Chuỗi găng hiển thị trực quan.
   - Gợi ý nới lỏng: bấm vào là áp dụng và lập lại lộ trình.
7. **Dữ liệu (`/data`):** tóm tắt dataset, cây khối, báo cáo kiểm tra, đồ thị tiên quyết (React Flow + dagre, tô sáng chuỗi găng).

## 10. Kiểm thử và xác minh

**Backend (`pytest`):**
- **Unit:**
  - validator: chu trình A→B→C→A phải bị bắt; song hành hai chiều không bị báo lỗi;
  - lịch học kỳ, ES/LS, prechecks;
  - mỗi HC có một test riêng trên fixture nhỏ;
  - verifier bắt được từng loại vi phạm;
  - explainer, advisor (shrinkage, cosine, độ ổn định), và các template thông điệp.
- **Các trường hợp biên ở Mục 4.1 của đặc tả:**
  1. Có chu trình → trả `DATA_ERROR`.
  2. Hai môn A, B cùng chỉ mở HK1 → B phải xếp ở HK1 năm sau.
  3. Nhóm yêu cầu 6 TC nhưng mọi môn đều 4 TC → chọn đủ 8 TC; tổng 140 hợp lệ với `at_least`, vô nghiệm với `exact`.
  4. Kỳ cuối chỉ có 8 TC → được miễn mức sàn.
  5. Nợ môn mà không đủ thời gian → `INFEASIBLE` kèm PC-01.
- **Property-based (hypothesis):** sinh ngẫu nhiên các instance nhỏ: tối đa 5 môn, tối đa 5 kỳ, 1 khối `MIN_CREDITS`. Kiểm 3 tính chất:
  - solver ra lời giải thì verifier không thấy vi phạm nào;
  - kết luận khả thi hay không của solver trùng với kết quả duyệt vét cạn;
  - MUS vẫn vô nghiệm, và bỏ bất kỳ phần tử nào của nó thì trở nên khả thi.
- **Nghiệm thu (pytest-bdd):** các file `features/ac01_…feature` đến `ac07_…feature`, giữ nguyên văn Given/When/Then của đặc tả.
  - AC-01 có 2 kịch bản: `exact` và `at_least`.
  - AC-06: sửa trần 24 thành 20 trong một bản sao dataset ở `tmp_path`, không sửa code.
  - AC-07 kiểm 3 điều:
    - T_grad(P1) nhỏ nhất;
    - std(P2) nhỏ hơn hoặc bằng std của hai phương án còn lại;
    - risk_coverage(P3) lớn hơn hoặc bằng của hai phương án còn lại; ngoài ra mọi cặp phương án có khoảng cách > 0.
- **API:** dùng TestClient chạy mọi endpoint với cả 5 sinh viên mẫu. Riêng sv04 phải nhận 200, status `INFEASIBLE` và không có phương án nào.
- **Chạy trên dữ liệu mẫu:** cả 5 sinh viên chạy đủ mọi chiến lược, mọi phương án đều qua verifier. Ghi lại thời gian; mục tiêu là dưới 10 giây cho mỗi yêu cầu trên 4 CPU.

**Frontend:**
- `npm run typecheck`, `npm run build`, và vitest cho các hàm tiện ích.
- Playwright smoke test (`e2e/smoke.spec.ts`) chạy uvicorn cùng `vite preview`, rồi đi qua kịch bản:
  1. chọn sv01 và bấm **Lập lộ trình**;
  2. thấy ít nhất 4 tab và lưới kỳ;
  3. mở giải trình của một môn;
  4. trang tư vấn có bảng xếp hạng;
  5. chọn sv04 thì thấy báo cáo xung đột.

**CI và Makefile:**
- `ci.yml` gồm 2 phần:
  - backend: ruff và pytest;
  - frontend: `npm ci`, typecheck, build, vitest.
- Makefile có các target:
  - cài đặt: `setup`, `validate-data`;
  - chạy dev: `dev-api`, `dev-web`;
  - kiểm thử: `test`, `lint`, `e2e`.

**MVP hoàn tất khi:**
- mọi test và e2e đều xanh;
- `cplan validate data/hcmus_cntt_k2020` không báo lỗi nào;
- đi trọn được kịch bản demo trong `docs/demo.md` trên UI.

## 11. Các mốc thực thi

Mỗi mốc: chạy test liên quan, commit, rồi `git push -u origin claude/quirky-davinci-q3kngj`.

| Mốc | Nội dung | Coi là xong khi |
|---|---|---|
| M0 | Lưu plan vào `docs/MVP_PLAN.md`, chép đặc tả gốc (mục 1–7) vào `docs/spec.md`, viết `docs/decisions.md`. Dựng khung backend và frontend, Makefile, CI, `.gitignore`. | `pytest` chạy được; `npm run build` thành công. |
| M1 | Domain models, loader, dataset mẫu kèm 5 sinh viên, validator, `cplan validate`. | Validate dữ liệu mẫu không có lỗi; test validator xanh. |
| M2 | Lịch học kỳ, student_state, graph (ES/LS/chuỗi găng/rủi ro), prechecks. | Test các trường hợp biên 1, 2, 5 xanh. |
| M3 | model_builder (mode `optimize`), FAST_TRACK, trích xuất phương án, verifier, `cplan plan`. | AC-01..AC-04, AC-06 và trường hợp biên 3, 4 xanh. |
| M4 | BALANCED, RISK_AVERSE, FOCUS, PERSONALIZED, cơ chế đa dạng, metrics và so sánh. | AC-07 xanh; cả 5 sinh viên mẫu có phương án hợp lệ. |
| M5 | Mode `explain`, MUS, gợi ý nới lỏng. | AC-05 và property test của MUS xanh. |
| M6 | Explainer và `messages_vi`. | Test giải trình xanh. |
| M7 | Tư vấn chuyên ngành, gợi ý kỳ tới, what-if. | Test advisor xanh. |
| M8 | FastAPI và export OpenAPI. | Test API xanh. |
| M9 | Frontend 7 trang và e2e smoke. | Build, vitest và Playwright xanh. |
| M10 | README tiếng Việt; `docs/model.md` giải thích mô hình bằng lời dễ hiểu và đối chiếu công thức với HC/SC và với code; `docs/data-format.md` (CSV cho Phòng Đào tạo, kèm ví dụ curl); `docs/demo.md` (kịch bản demo khoảng 5 phút); Docker Compose (tùy chọn). | Đọc lại toàn bộ và chạy thử. |

## 12. Ghi chú cho model thực thi

- **Python:**
  - cài đặt: `uv venv backend/.venv && uv pip install -e "backend[dev]"`;
  - thư viện chính: `ortools>=9.12` (đã xác nhận có wheel 9.15 cho cp313), `pydantic>=2.7`, `fastapi`, `uvicorn[standard]`;
  - thư viện cho dev: `pytest`, `pytest-bdd`, `hypothesis` (đặt `deadline=None` và giới hạn `max_examples`), `httpx`, `ruff`.
- **API CP-SAT** dạng snake_case (OR-Tools ≥ 9.8):
  - tạo biến và ràng buộc: `new_bool_var`, `add(...).only_enforce_if(...)`, `add_multiplication_equality`;
  - assumptions và hint: `add_assumptions`/`clear_assumptions`, `add_hint`/`clear_hints`;
  - mục tiêu và lõi xung đột: `minimize`/`maximize`, `solver.sufficient_assumptions_for_infeasibility()`.
- **Playwright:**
  - dùng Chromium có sẵn (`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`, build 1194);
  - **không** chạy `playwright install`;
  - pin `@playwright/test` đúng bản khớp build 1194, hoặc đặt `launchOptions.executablePath: '/opt/pw-browsers/chromium'`.
- **Mạng:** `*.hcmus.edu.vn` bị chặn, đừng cố tải. Dựng dữ liệu theo mục 6.2 và mục 13. README phải ghi rõ cần đối chiếu với CTĐT và quy chế chính thức (QĐ 1175/QĐ-KHTN).
- **Git:** không đưa định danh model vào commit hay code. Không tạo PR khi chưa được yêu cầu.

## 13. Nguồn tham khảo cho dữ liệu mẫu

Các nguồn dưới đây được tra qua công cụ tìm kiếm, vì truy cập trực tiếp bị chặn. Cần đối chiếu lại với bản chính thức.

- [FIT HCMUS – Cử nhân tài năng](https://www.fit.hcmus.edu.vn/dai-hoc/cu-nhan-tai-nang): 138 TC, áp dụng từ K2020; đại cương 56 TC gồm LLCT 11, KHXH–KT–KN 5, Toán–KHTN–CN–MT 36, Tin học 4; CSC10001–CSC10004 đều 4 TC.
- [Giới thiệu CN 2019 (FIT)](https://www.fit.hcmus.edu.vn/vn/UserFiles\6410_Gioi-thieu-CN-2019_giao-vu.pdf): tổng ≥ 138 TC; đại cương 56; cơ sở ngành 38; ngành/chuyên ngành ≥ 24.
- [K2022 – Danh sách tiên quyết và học trước](https://www.fit.hcmus.edu.vn/vn/UserFiles/7793_K2022-Danh-sach-tien-quyet-va-hoc-truoc.pdf): quan hệ học trước giữa CSC10001, CSC10002, CSC10003 và CSC10004.
- [Quy chế đào tạo 2021, QĐ 1175/QĐ-KHTN](https://www.ctda.hcmus.edu.vn/wp-content/uploads/2023/03/Quy-che-dao-tao-2021.pdf)
- [Thông báo ĐKHP HK1 2025–2026 (CLC)](https://hcmus.edu.vn/thong-bao-dang-ky-hoc-phan-hoc-ky-1-nam-hoc-2025-2026-chuong-trinh-chat-luong-cao-tang-cuong-tieng-anh-va-viet-phap/): đăng ký 10–22 TC mỗi kỳ.
- [Thông báo cảnh báo học tập HK1 2023–2024](https://hcmus.edu.vn/thong-bao-canh-bao-hoc-tap-va-buoc-thoi-hoc-doi-voi-sinh-vien-he-chinh-quy-tai-hoc-ky-1-nam-hoc-2023-2024/): bị cảnh báo khi đạt dưới 7 TC trong kỳ, trừ sinh viên đã tích lũy từ 130 TC.
- [Danh sách 6 hướng chuyên ngành của FIT (vnreview)](https://vnreview.vn/threads/gioi-cong-nghe-thong-tin-nen-hoc-truong-nao-la-tot-nhat.14106/latest) và [Tuổi Trẻ](https://tuoitre.vn/cu-nhan-cong-nghe-thong-tin-1079245.htm).
