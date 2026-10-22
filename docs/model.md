# Mô hình toán và cách hệ thống hoạt động

Tài liệu này giải thích bộ tối ưu bằng lời dễ hiểu và chỉ rõ mỗi luật trong đặc tả nằm ở đâu trong code.
Ví dụ xuyên suốt: sinh viên **sv01** (tân sinh viên K2026) cần tích lũy 138 TC.

## 1. Ý tưởng chính

Hãy tưởng tượng một bảng: mỗi hàng là một môn, mỗi cột là một học kỳ. Hệ thống phải đánh dấu
*tối đa một ô* trên mỗi hàng (môn học ở kỳ nào, hoặc không học) sao cho mọi luật đều thỏa, rồi trong
các cách đánh dấu hợp lệ thì chọn cách tốt nhất theo một tiêu chí nào đó (ra trường sớm, tải đều…).

Cách làm trong đặc tả gốc gồm 2 giai đoạn: chọn môn tự chọn trước (knapsack), xếp kỳ sau. Hệ thống này **làm
cả hai việc trong cùng một mô hình CP-SAT**. Lý do: nếu tách đôi, giai đoạn 1 có thể chọn một bộ môn tự chọn mà
giai đoạn 2 không xếp được, vì vướng lịch mở môn hoặc tiên quyết. Với khoảng 100 môn × 20 kỳ, sau khi cắt tỉa
còn khoảng 200–600 biến, nên CP-SAT giải trong vài trăm mili-giây.

## 2. Tiền xử lý: cửa sổ thời gian theo chu kỳ (`analysis/graph.py`)

- **ES (kỳ sớm nhất)** của môn c là kỳ *mở môn* đầu tiên sau khi mọi môn điều kiện của c đã có thể học.
  - Ví dụ: Nhập môn lập trình (CSC10001) chỉ mở HK1. Kỹ thuật lập trình (CSC10002) chỉ mở HK2. Cấu trúc dữ
    liệu (CSC10004) chỉ mở HK1.
  - Vậy ES(CSC10004) = HK1 năm sau, **không phải** "kỳ của CSC10002 + 1". Đây chính là phần "modulo" trong
    tên bài toán.
- **LS (kỳ muộn nhất)** tính ngược từ hạn chót. Chỉ lan truyền qua các môn kế tiếp *bắt buộc*, nhờ vậy việc cắt
  tỉa không bao giờ loại mất một lời giải hợp lệ.
- Biến x[c,t] chỉ được tạo khi kỳ t có mở môn c và ES ≤ t ≤ LS. Nhờ đó mô hình nhỏ đi nhiều lần.
- **Chẩn đoán nhanh** (`analysis/prechecks.py`) là các điều kiện cần. Vi phạm một điều kiện là chắc chắn vô
  nghiệm, nên hệ thống báo ngay mà không cần gọi solver:

  | Mã | Ý nghĩa |
  |---|---|
  | PC-01 | Chuỗi tiên quyết dài hơn số kỳ còn lại. In ra chuỗi cụ thể. |
  | PC-02 | Không đủ sức chứa tín chỉ trong các kỳ còn lại. |
  | PC-03 | Môn bắt buộc không thể học: đã ngừng dạy, không còn đợt mở, hoặc không đủ GPA. Nhóm này gộp luôn PC-06 của kế hoạch. |
  | PC-04 | Khối kiến thức không thể đủ tín chỉ. |
  | PC-05 | Hai môn bắt buộc loại trừ nhau. |

## 3. Biến và ràng buộc (`solver/model_builder.py`)

**Biến:**

| Biến | Ý nghĩa |
|---|---|
| `x[c,t]` | Môn c học ở kỳ t. |
| `sel[c] = Σ_t x[c,t] ≤ 1` | Môn c có được chọn hay không. |
| `y[c,b]` | Tín chỉ của môn c được tính vào khối lá b. Đây là "chứng chỉ" chống tính trùng. |
| `le[t] = 1 ⇔ t ≤ kỳ tốt nghiệp` | Đánh dấu kỳ còn nằm trong lộ trình. Kỳ tốt nghiệp = `Σ le − 1`. |

**Ràng buộc**, đối chiếu với đặc tả:

| Luật trong đặc tả | Công thức | Ghi chú |
|---|---|---|
| HC-01 Ngưỡng 138 TC | `Σ w·y ≥ 138` (`= 138` nếu `credit_rule = exact`) | Mặc định là ≥ (xem `docs/decisions.md`). |
| HC-02 Không trùng lặp | Môn đã đạt (kể cả qua tương đương) không được đưa vào mô hình; `Σ_b y[c,b] ≤ 1` | |
| HC-03 Cấu trúc khối | Mỗi nút B của cây: `Σ w·y ≥ req(B)`. Môn bắt buộc: `y[c,b] = 1`. Môn được chọn phải được tính vào một khối nào đó. | |
| HC-04 Tiên quyết | `x[b,t] ≤ Σ_{t'<t} x[a,t']` | Bỏ qua nếu a đã ĐẠT (điểm ≥ `min_grade`). |
| HC-05 Học trước | như trên | Bỏ qua nếu a đã từng HỌC (kể cả rớt). |
| HC-06 Song hành | `x[b,t] ≤ Σ_{t'≤t} x[a,t']` | |
| HC-07 Loại trừ | `sel[a] + sel[b] ≤ 1`; không tính tín chỉ cả hai | |
| HC-08 Tải kỳ chính | `load[t] ≤ Wmax`; `load[t] ≥ Wmin` khi t chưa phải kỳ cuối (`le[t+1] = 1`) | Kỳ cuối được miễn sàn (trường hợp biên 4.1.4). |
| HC-09 Tải kỳ hè | `load[t] ≤ Wmax_summer`; kỳ hè chỉ xuất hiện khi SV bật | |
| HC-10 Kỳ mở môn | Không tạo biến ở kỳ không mở (mode explain: `x = 0` gắn literal) | |
| HC-11 Hạn đào tạo | Khoảng lập kế hoạch dừng ở hạn chót (mode explain: `grad ≤ D` gắn literal) | |
| Điều kiện môn | Tích lũy tối thiểu: `x[c,t] ⇒ đã đạt + Σ_{t'<t} load ≥ M`. Học kỳ cuối: `x[c,t] ⇒ le[t+1] = 0` | Ví dụ khóa luận cần ≥ 110 TC và phải học ở kỳ cuối. |
| Tùy chọn SV | Ghim môn, loại môn, trần tín chỉ riêng, kỳ tốt nghiệp mong muốn | |

## 4. Năm chiến lược (`solver/strategies.py`)

Hệ thống không cộng các mục tiêu với trọng số cố định (vì khó chọn trọng số). Thay vào đó nó tối ưu **theo thứ
tự ưu tiên (lexicographic)**: tối ưu mục tiêu 1, khóa giá trị đó lại, rồi mới tối ưu mục tiêu 2…

| Phương án | Thứ tự tối ưu |
|---|---|
| Tốt nghiệp sớm | kỳ tốt nghiệp ↓ → số kỳ hè ↓ → tín chỉ ↓ → dồn môn về sớm |
| Cân bằng tải | tốt nghiệp ≤ g_target → kỳ hè ↓ → tín chỉ ↓ → **tải đỉnh** ↓ → Σ tải² ↓ (≈ phương sai, vì tổng tín chỉ đã cố định) → độ nặng đỉnh ↓ |
| An toàn | tốt nghiệp ≤ g_target → tín chỉ ↓ → **đệm học lại** ↑ → môn rủi ro học sớm |
| Theo định hướng | tốt nghiệp ≤ g_target → tín chỉ ↓ → độ khớp sở thích của môn tự chọn ↑ |
| Đề xuất cho bạn | Compromise Programming (xem bên dưới) |

- **g_target** = max(kỳ tốt nghiệp sớm nhất, kỳ tốt nghiệp chuẩn hoặc kỳ SV mong muốn). Nghĩa là các phương án
  "nhàn" vẫn không được trễ hơn tiến độ chuẩn.
- **Đệm học lại** của môn bắt buộc c xếp ở kỳ t: đúng khi lượt mở kế tiếp của c sau kỳ t vẫn ≤ LS(c) tính theo
  g_target. Nói cách khác, nếu rớt thì vẫn học lại kịp mà không trễ tốt nghiệp. Mỗi môn có trọng số rủi ro
  1..20, cộng từ: số môn phụ thuộc, độ dài chuỗi phía sau, mở 1 lần/năm, tỉ lệ rớt lịch sử, từng rớt.
- **Compromise Programming** cho phương án "Đề xuất cho bạn":
  1. Lấy 4 phương án trên làm bảng payoff, xác định điểm lý tưởng z* và điểm tệ nhất zᴺ của từng mục tiêu
     (kỳ tốt nghiệp, tải đỉnh, đệm học lại, sở thích).
  2. Tối thiểu `Σ α_k (f_k − z*_k)/(zᴺ_k − z*_k)`, với α là trọng số SV kéo trên giao diện.
- **Đa dạng (AC-07):** nếu một phương án trùng hoàn toàn phương án trước, hệ thống thêm một cut buộc khác đi ít
  nhất một ô mà vẫn giữ giá trị tối ưu. Không làm được thì gắn nhãn "trùng" chứ không trả phương án kém hơn.

**Khác với kế hoạch ban đầu:**
- Phương án Cân bằng không duyệt từng kỳ tốt nghiệp g. Thay vào đó nó tối ưu "tải đỉnh rồi Σ tải²" với
  `grad ≤ g_target`: kết quả tương đương nhưng chỉ cần một chuỗi giải.
- Đệm học lại chỉ tính trên môn bắt buộc, vì môn tự chọn rớt thì có thể thay bằng môn khác.

## 5. Bộ kiểm chứng độc lập (`verify/plan_verifier.py`)

Bộ kiểm chứng viết lại toàn bộ luật bằng Python thuần, không dùng mô hình CP-SAT.
- Mọi phương án phải qua bộ này trước khi trả về. Phương án nào có vi phạm sẽ bị loại và ghi log, không bao giờ
  đến tay người dùng.
- Property test dùng nó làm chuẩn đối chiếu: trên hàng chục bài toán ngẫu nhiên, kết luận "khả thi" của solver
  phải trùng với kết quả duyệt vét cạn.

## 6. Giải thích khi vô nghiệm: MUS (`solver/mus.py`)

1. Dựng mô hình ở **mode explain**: không cắt tỉa, khoảng thời gian kéo dài thêm 4 kỳ sau hạn chót, và mỗi
   *nhóm luật nghiệp vụ* gắn một literal. Ví dụ "HC-05: CSC10004 cần học trước CSC10002" là một nhóm,
   "HC-11: hạn chót" là một nhóm.
2. Lấy lõi từ CP-SAT (`sufficient_assumptions_for_infeasibility`), rồi **lọc xóa**: bỏ thử từng luật; nếu vẫn
   vô nghiệm thì bỏ hẳn luật đó.
3. Kết quả là một tập luật tối thiểu: bỏ bất kỳ luật nào thì bài toán có lời giải.

Ví dụ với sv04:

```
HC-03: khối «Kiến thức cơ sở ngành» cần 38 TC
HC-05: Cấu trúc dữ liệu và giải thuật (CSC10004) có học trước Kỹ thuật lập trình (CSC10002)
HC-10: Cấu trúc dữ liệu và giải thuật (CSC10004) chỉ mở vào HK1
HC-11: phải tốt nghiệp trước hạn tối đa HK2 2026–2027
→ Gợi ý: nếu được gia hạn thời gian đào tạo, có thể tốt nghiệp vào HK2 2028–2029.
```

## 7. Giải trình từng môn (`explain/explainer.py`)

Câu hỏi "Vì sao Cơ sở trí tuệ nhân tạo xếp ở HK2 2027–2028 mà không sớm hơn?" được trả lời như sau:
1. Thử dời môn sang từng kỳ mở sớm hơn.
2. Để bộ kiểm chứng nói luật nào bị vi phạm. Ví dụ: "môn trước CSC10004 xếp ở HK1 2027–2028" hoặc "kỳ đó đã
   đủ 24 TC".
3. Nếu dời được mà không vi phạm luật nào, giải trình ghi rõ môn bị dời *theo chiến lược*, ví dụ để cân bằng tải.

## 8. Tư vấn chuyên ngành (`advisor/specialization.py`)

Điểm = Σ trọng số × thành phần:

| Thành phần | Cách tính |
|---|---|
| Học lực (A) | Trung bình có trọng số điểm các môn chỉ báo, co về GPA chung khi có ít điểm (shrinkage, m = 2). |
| Sở thích (I) | Cosine giữa vector sở thích (thang 1–5) và hồ sơ chủ đề của chuyên ngành. |
| Nghề nghiệp (C) | Tỉ lệ mục tiêu nghề của SV thuộc chuyên ngành. |
| Tiến độ (P) | Chạy thử bộ tối ưu với chuyên ngành đó để biết kỳ tốt nghiệp sớm nhất, rồi chuẩn hóa so với các chuyên ngành khác. |

Hệ thống cũng kiểm tra **độ ổn định**: chuyên ngành đứng đầu có còn đứng đầu khi mỗi trọng số thay đổi ±0,1 không.
