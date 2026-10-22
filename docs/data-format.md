# Định dạng dữ liệu và tích hợp với hệ thống của trường

Mỗi chương trình đào tạo là một thư mục trong `data/`. Thuật toán chỉ đọc dữ liệu, nên muốn đổi luật
(trần tín chỉ, lịch mở môn, môn tương đương…) thì **chỉ cần sửa file**, không sửa code.

```
data/<dataset>/
  courses.json        danh mục học phần
  offerings.json      lịch mở môn
  dependencies.json   tiên quyết / học trước / song hành / loại trừ
  curriculum.json     cây khối kiến thức, chuyên ngành, điều kiện tốt nghiệp
  equivalences.json   môn tương đương / thay thế
  advisor.json        hồ sơ chủ đề, nghề nghiệp, môn chỉ báo cho tư vấn chuyên ngành
  regulations/*.json  một hoặc nhiều bộ quy chế (chọn qua tham số `regulation`)
  students/*.json     hồ sơ sinh viên mẫu (tùy chọn)
```

## Nhập từ CSV (Phòng Đào tạo)

```bash
backend/.venv/bin/cplan import-csv data/csv_example data/demo_import   # chuyển CSV thành JSON, rồi kiểm tra
```

Thư mục `data/csv_example/` có sẵn một bộ CSV nhỏ để tham khảo. Các file:

| File | Cột | Ghi chú |
|---|---|---|
| `courses.csv` | `id,name,credits,workload,tags,offering_terms,year_parity,min_accumulated_credits,final_term_only,min_gpa,historical_fail_rate,is_active` | `offering_terms` nhận một trong hai dạng: `HK1;HK2;HE`, hoặc enum của đặc tả (`FALL_ONLY`, `SPRING_ONLY`, `EVERY_TERM`, `SUMMER_ALLOWED`, `ODD_YEARS_ONLY`). `tags` cách nhau bằng `;`. |
| `dependencies.csv` | `source,target,type,min_grade` | `type` ∈ `PREREQUISITE` (tiên quyết), `PRE_COURSE` (học trước), `CO_REQUISITE` (song hành), `MUTUALLY_EXCLUSIVE` (loại trừ). |
| `blocks.csv` | `id,name,parent,rule,required_credits,k,specialization,specialization_group,kind` | `rule` ∈ `ALL_MANDATORY`, `MIN_CREDITS`, `PICK_K_OF_N`. Chỉ khối lá mới chứa môn. |
| `memberships.csv` | `block_id,course_id,mandatory` | Một môn có thể thuộc nhiều khối, nhưng tín chỉ chỉ được tính một lần. |
| `specializations.csv` | `id,name,block_id,description` | |
| `curriculum.csv` | `id,name,total_credits_required,credit_rule,standard_main_terms,graduation_conditions` | Chỉ có 1 dòng. `credit_rule` ∈ `at_least` (mặc định), `exact`. |
| `equivalences.csv` | `canonical,equivalent,kind` | `kind` ∈ `EQUIVALENT`, `SUBSTITUTE`. |
| `regulation.csv` | `name,min_credits_main,max_credits_main,max_credits_summer,max_main_terms` | Chỉ có 1 dòng. Kết quả ghi vào `regulations/default.json`. |

Sau khi import, lệnh tự chạy bộ kiểm tra DV-01..DV-14. Bộ này phát hiện chu trình phụ thuộc, mã môn không tồn
tại, khối không đủ tín chỉ, hai môn bắt buộc loại trừ nhau…

## Quy chế (`regulations/*.json`)

```json
{
  "id": "default",
  "min_credits_main": 14,
  "max_credits_main": 24,
  "max_credits_summer": 8,
  "final_term_min_exempt": true,
  "max_main_terms": 12,
  "allow_empty_main_terms": false,
  "allow_double_count_across_blocks": false,
  "load_rules": [{ "when": "academic_warning", "min_credits_main": 10, "max_credits_main": 14 }]
}
```

`load_rules` hỗ trợ hai dạng điều kiện:
- `academic_warning`: sinh viên đang bị cảnh báo học tập;
- `gpa_at_least:8.0`: ví dụ cho phép SV giỏi đăng ký nhiều hơn.

## Hồ sơ sinh viên (gửi qua API)

```json
{
  "id": "2212345",
  "name": "Nguyễn Văn A",
  "cohort_year": 2024,
  "curriculum_id": "CNTT_K2020",
  "next_term": { "year": 2026, "kind": "HK2" },
  "records": [
    { "course": "CSC10001", "status": "PASSED", "grade": 8.5, "term": { "year": 2024, "kind": "HK1" } },
    { "course": "CSC10004", "status": "FAILED", "grade": 3.0 }
  ],
  "academic_warning": false,
  "declared_specialization": null,
  "interests": { "ai_ml": 5, "data": 4 },
  "career_goals": ["ai_engineer"]
}
```

- `status` ∈ `PASSED`, `FAILED`, `EXEMPTED`, `IN_PROGRESS`.
- Mã môn cũ được tự quy đổi theo `equivalences.json`.
- `year` là năm bắt đầu của năm học. Ví dụ HK2 2026–2027 ghi là `{"year": 2026, "kind": "HK2"}`.

## Gọi API

```bash
curl -s localhost:8000/api/plans -H 'Content-Type: application/json' -d '{
  "dataset": "hcmus_cntt_k2020",
  "regulation": "default",
  "student_id": "sv02",
  "preferences": { "specialization": "CNPM", "summer_enabled": false },
  "strategies": ["FAST_TRACK", "BALANCED"]
}'
```

Thay `student_id` bằng `"student": { …hồ sơ… }` để gửi hồ sơ thật lấy từ hệ thống đào tạo.

| Endpoint | Chức năng |
|---|---|
| `POST /api/plans` | Lập lộ trình. `status` ∈ `OK`, `INFEASIBLE` (kèm `infeasibility`), `COMPLETED`, `DATA_ERROR` (HTTP 422). |
| `POST /api/advisor/specializations` | Tư vấn chuyên ngành. |
| `POST /api/recommendations/next-term` | Gợi ý đăng ký kỳ tới. |
| `POST /api/what-if/fail` | Mô phỏng rớt môn. |
| `GET /api/datasets…` | Danh mục môn, cây khối, báo cáo kiểm tra, sinh viên mẫu. |

Đặc tả OpenAPI đầy đủ có tại `/docs`, hoặc xuất ra file bằng `cplan export-openapi --out openapi.json`.
