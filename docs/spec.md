# Đặc tả bài toán (bản gốc, mục 1–7)

> Nguồn: ProjectTDTT.md do người dùng cung cấp. Giữ nguyên nội dung mục 1–7.

## **1\. Đặc tả bài toán (Formal Problem Specification)**

### **1.1. Bản chất toán học của bài toán**

Hệ thống giải quyết một biến thể mở rộng của bài toán **Lập lịch dự án trong điều kiện giới hạn nguồn lực có cấu trúc lựa chọn** (*Resource-Constrained Project Scheduling Problem with Selection & Modulo-Time Windows \- RCPSP-SMTW*):

* **Đối tượng cần xếp:** Tập hợp các học phần (Course nodes) nằm trong đồ thị có hướng (DAG \- Directed Acyclic Graph biểu diễn quan hệ tiên quyết).  
* **Không gian thời gian:** Tập các học kỳ rời rạc T={1,2,…,Tmax}T={1,2,…,Tmax​}.  
* **Nguồn lực bị chặn:** Số lượng tín chỉ mỗi học kỳ (tương đương dung lượng nguồn lực theo từng thời kỳ).  
* **Thành phần tổ hợp:** Việc chọn các học phần tự chọn sao cho tổng trọng số thỏa mãn cấu trúc cây khối kiến thức (Knapsack-like structure per Knowledge Block).  
* **Hàm mục tiêu đa tiêu chí (Multi-objective):** Tối ưu hóa thời gian tốt nghiệp, độ cân bằng tải tín chỉ, và tối thiểu hóa rủi ro rớt chuỗi môn tiên quyết.

### **1.2. Không gian đầu vào (Input Space)**

1. **Catalog học phần (CC):** Danh mục toàn bộ học phần trong chương trình, mỗi môn c∈Cc∈C có số tín chỉ wc∈N+wc​∈N+.  
2. **Cấu trúc nhóm học phần (GG):** Phân cấp cây môn học (Cơ sở ngành, Chuyên ngành, Tự chọn định hướng...).  
3. **Đồ thị quan hệ phụ thuộc (EE):** Các cung ràng buộc giữa các cặp môn (ci,cj)(ci​,cj​) (tiên quyết, học trước, song hành, loại trừ lẫn nhau).  
4. **Lịch mở môn định kỳ (OO):** Ánh xạ O(c)⊆{1,2,Heˋ}O(c)⊆{1,2,Heˋ} xác định học phần cc chỉ được mở vào những kỳ nào trong năm học.  
5. **Trạng thái sinh viên (SS):** Tập hợp các học phần sinh viên đã tích lũy thành công Cpassed⊂CCpassed​⊂C, và học kỳ bắt đầu lập lộ trình tstarttstart​.  
6. **Quy chế đào tạo (RR):** Giới hạn tín chỉ \[Wmin,Wmax\]\[Wmin​,Wmax​\] cho học kỳ chính và \[0,Wmax\_summer\]\[0,Wmax\_summer​\] cho kỳ phụ, tổng tín chỉ mục tiêu Wtarget=138Wtarget​=138.

### **1.3. Đầu ra (Output Space)**

1. **Nếu bài toán Khả thi (Feasible):**  
   * Tập hợp các phương án lộ trình P={P1,P2,…,Pk}P={P1​,P2​,…,Pk​} với sự khác biệt có ý nghĩa (diversity).  
   * Mỗi phương án PP là một ánh xạ P:Cplan→TP:Cplan​→T, với Cplan⊆C∖CpassedCplan​⊆C∖Cpassed​, gán mỗi môn được chọn vào đúng một học kỳ t∈\[tstart,Tmax\]t∈\[tstart​,Tmax​\].  
   * Đi kèm mỗi môn được xếp là **Cây giải trình (Explanation Trace)**: lý do chọn môn, lý do xếp vào kỳ tt, và các điều kiện kích hoạt.  
2. **Nếu bài toán Bất khả thi (Infeasible):**  
   * Không trả về phương án sai quy chế.  
   * Trả về **Tập con xung đột tối thiểu (Minimal Unsatisfiable Subset \- MUS / IIS)**: chỉ ra chính xác tập các ràng buộc và học phần mâu thuẫn lẫn nhau khiến không thể tìm ra lộ trình (ví dụ: chuỗi tiên quyết dài quá TmaxTmax​, hoặc tổng tín chỉ tối thiểu các môn bắt buộc mở trong kỳ vượt quá WmaxWmax​).

---

## **2\. Phân loại Ràng buộc: Ràng buộc Bắt buộc (Hard) vs Tiêu chí Ưu tiên (Soft)**

                      ┌───────────────────────────────────────────────┐  
                      │          BÀI TOÁN TỐI ƯU LỘ TRÌNH             │  
                      └──────────────────────┬────────────────────────┘  
                                             │  
                   ┌─────────────────────────┴─────────────────────────┐  
                   ▼                                                   ▼  
      ┌────────────────────────┐                          ┌────────────────────────┐  
      │ HARD CONSTRAINTS (BẮT BUỘC) │                     │ SOFT CONSTRAINTS (ƯU TIÊN) │  
      │  (Vi phạm \= Loại bỏ ngay) │                      │   (Đánh giá hàm mục tiêu)  │  
      └────────────┬───────────┘                          └────────────┬───────────┘  
                   │                                                   │  
 ┌─────────────────┼──────────────────┐              ┌─────────────────┼──────────────────┐  
 ▼                 ▼                  ▼              ▼                 ▼                  ▼  
\[138 Tín chỉ &   \[Ràng buộc phụ  \[Giới hạn Tín chỉ   \[Ưu tiên tốt   \[Phân bổ tải học   \[Giảm thiểu  
Không tính trùng\] thuộc môn học\]   & Kỳ mở môn\]     nghiệp sớm\]    tập cân bằng\]     rủi ro mở môn\]

### **2.1. Hard Constraints (Ràng buộc bắt buộc \- Vi phạm \= Phương án Vô hiệu)**

| Mã | Tên ràng buộc | Định nghĩa toán học / Logic | Mô tả chi tiết |
| :---- | :---- | :---- | :---- |
| **HC-01** | **Ngưỡng tín chỉ tốt nghiệp** | ∑c∈Cpassed∪Cplanwc=138∑c∈Cpassed​∪Cplan​​wc​=138 | Tổng số tín chỉ thuộc danh mục tính điểm tốt nghiệp phải đạt chính xác 138 tín chỉ. |
| **HC-02** | **Không tính trùng lặp** | ∀c∈Cplan,c∉Cpassed∀c∈Cplan​,c∈/Cpassed​ và mỗi cc chỉ xuất hiện tối đa 1 lần trong lộ trình | Nếu một môn thuộc nhiều nhóm kiến thức, tín chỉ của nó chỉ được cộng 1 lần vào tổng 138\. |
| **HC-03** | **Thỏa mãn cấu trúc nhóm môn** | ∀g∈G,∑c∈(Cpassed∪Cplan)∩gwc≥Wgreq∀g∈G,∑c∈(Cpassed​∪Cplan​)∩g​wc​≥Wgreq​ | Phải hoàn thành 100% môn bắt buộc và đạt đủ số tín chỉ tối thiểu theo từng nhóm tự chọn quy định. |
| **HC-04** | **Ràng buộc Tiên quyết (Prerequisite)** | Nếu ci→precjci​→pre​cj​ thì t(cj)≥t(ci)+1t(cj​)≥t(ci​)+1 | Môn cjcj​ chỉ được học khi môn cici​ đã được xếp và hoàn thành ở học kỳ trước đó (hoặc nằm trong CpassedCpassed​). |
| **HC-05** | **Ràng buộc Học trước (Prior Course)** | Nếu ci→priorcjci​→prior​cj​ thì t(cj)≥t(ci)+1t(cj​)≥t(ci​)+1 | Sinh viên phải đăng ký học cici​ ở kỳ trước (điều kiện điểm số/thi sẽ do quy chế xác định). |
| **HC-06** | **Ràng buộc Song hành (Co-requisite)** | Nếu ci↔cocjci​↔co​cj​ thì t(cj)≥t(ci)t(cj​)≥t(ci​) | Môn cjcj​ phải được học cùng kỳ hoặc sau kỳ đã học môn cici​. |
| **HC-07** | **Ràng buộc Loại trừ (Mutually Exclusive)** | Nếu ci⊗cjci​⊗cj​ thì ci∈Cplan⟹cj∉Cplanci​∈Cplan​⟹cj​∈/Cplan​ | Các môn học tương đương hoặc thay thế nhau không được cùng chọn vào lộ trình. |
| **HC-08** | **Giới hạn tải học kỳ chính** | ∀t∈Tmain,Wmin≤∑c:t(c)=twc≤Wmax∀t∈Tmain​,Wmin​≤∑c:t(c)=t​wc​≤Wmax​ | Trừ học kỳ cuối cùng (có thể cho phép dưới WminWmin​ nếu số tín chỉ còn lại ít hơn ngưỡng tối thiểu). |
| **HC-09** | **Giới hạn tải học kỳ phụ (Hè)** | ∀t∈Tsummer,0≤∑c:t(c)=twc≤Wmax\_summer∀t∈Tsummer​,0≤∑c:t(c)=t​wc​≤Wmax\_summer​ | Học kỳ hè không bắt buộc đăng ký, nhưng nếu đăng ký không được vượt trần quy định. |
| **HC-10** | **Khung thời gian mở môn (Availability)** | ∀c∈Cplan,TermType(t(c))∈O(c)∀c∈Cplan​,TermType(t(c))∈O(c) | Môn học chỉ được xếp vào kỳ mà khoa có kế hoạch mở (ví dụ: chỉ mở vào kỳ Thu hoặc kỳ Xuân). |
| **HC-11** | **Thời gian đào tạo tối đa** | max⁡c∈Cplant(c)≤Tlimitmaxc∈Cplan​​t(c)≤Tlimit​ | Lộ trình không được vượt quá số học kỳ tối đa cho phép theo quy chế đào tạo của trường. |

### **2.2. Soft Constraints (Tiêu chí tối ưu \- Phân hóa các phương án lộ trình)**

Hệ thống tối ưu hóa đa mục tiêu bằng cách cấu hình vector trọng số hàm mục tiêu F=∑αk⋅fk(P)F=∑αk​⋅fk​(P) để tạo ra các nhóm phương án khác biệt rõ rệt:

1. **Phương án 1: Ưu tiên Tốt nghiệp sớm (Fast-Track Graduation)**  
   * **Mục tiêu:** Cực tiểu hóa tổng số học kỳ hoàn thành Tgrad=max⁡c∈Cplant(c)Tgrad​=maxc∈Cplan​​t(c).  
   * **Hành vi:** Đẩy số tín chỉ mỗi kỳ lên tiệm cận WmaxWmax​, tận dụng tối đa các học kỳ hè nếu có môn mở.  
2. **Phương án 2: Tải học tập Cân bằng (Load Balancing & Stress Reduction)**  
   * **Mục tiêu:** Cực tiểu hóa phương sai tải tín chỉ giữa các kỳ: Var(W)=1∣T∣∑t(Wt−Wˉ)2Var(W)=∣T∣1​∑t​(Wt​−Wˉ)2 và cực tiểu hóa việc dồn các môn có đồ án/thực hành nặng vào cùng một kỳ.  
   * **Hành vi:** Số tín chỉ mỗi kỳ duy trì quanh mức trung bình lý tưởng (khoảng 16 \- 18 tín chỉ/kỳ chính), dàn đều độ khó.  
3. **Phương án 3: Giảm thiểu rủi ro mở môn & Nút cổ chai (Critical Path & Offering Risk)**  
   * **Mục tiêu:** Cực đại hóa khoảng cách an toàn (slack time) cho các môn "nút cổ chai" (môn có chuỗi tiên quyết dài phía sau) và ưu tiên học sớm các môn có tần suất mở thấp (chỉ mở 1 lần/năm).  
   * **Hành vi:** Đưa các môn hiếm khi mở và môn gốc của cây tiên quyết lên kỳ sớm nhất có thể; tránh để một môn rớt dẫn đến chậm tiến độ toàn khóa.  
4. **Phương án 4: Tối ưu theo Định hướng chuyên ngành (Specialization Preference)**  
   * **Mục tiêu:** Cực đại hóa độ tập trung của các môn tự chọn theo một cụm chủ đề nhất định thay vì chọn rải rác.

---

## **3\. Mô hình Thực thể Dữ liệu & Quan hệ (Data Architecture)**

Kiến trúc tuân thủ nguyên tắc **Tách biệt hoàn toàn (Decoupling)** giữa:

1. *Dữ liệu danh mục môn học (Course Catalog)*  
2. *Dữ liệu cấu trúc chương trình & Quy chế (Curriculum Rules & Regulations)*  
3. *Dữ liệu hồ sơ sinh viên (Student State)*  
4. *Thuật toán sinh lộ trình (Optimization Engine)*

*![Mermaid diagram]()*

### **3.1. Đặc tả chi tiết các thực thể**

#### **1\. Nhóm thực thể Danh mục & Môn học (Catalog)**

* **`Course` (Học phần):**  
  * `course_id` (PK): Mã học phần duy nhất.  
  * `name`: Tên học phần.  
  * `credits`: Số tín chỉ chuẩn (nguyên dương).  
  * `workload_weight`: Trọng số độ khó/thời lượng thực hành (phục vụ soft constraint cân bằng tải).  
  * `is_active`: Trạng thái môn học còn được giảng dạy hay không.  
* **`CourseDependency` (Quan hệ phụ thuộc):**  
  * `source_course_id` (FK): Môn điều kiện.  
  * `target_course_id` (FK): Môn chịu ràng buộc.  
  * `dependency_type`: Enum (`PREREQUISITE` \- tiên quyết, `PRE_COURSE` \- học trước, `CO_REQUISITE` \- song hành, `MUTUALLY_EXCLUSIVE` \- thay thế/loại trừ).  
  * `minimum_grade`: Điểm số tối thiểu yêu cầu (nếu quy chế phân biệt mức đạt).  
* **`OfferingSchedule` (Quy tắc mở môn):**  
  * `course_id` (FK): Mã học phần.  
  * `term_pattern`: Quy tắc chu kỳ mở môn (`FALL_ONLY`, `SPRING_ONLY`, `EVERY_TERM`, `SUMMER_ALLOWED`, `ODD_YEARS_ONLY`...).  
  * `department_restriction`: Điều kiện hạn chế đặc thù từ khoa.

#### **2\. Nhóm thực thể Quy chế & Chương trình (Curriculum & Rules)**

* **`Curriculum` (Chương trình đào tạo):**  
  * `curriculum_id` (PK): Phiên bản CTĐT (ví dụ: CNTT Khóa 2024).  
  * `total_credits_required`: 138 tín chỉ.  
  * `effective_year`: Năm áp dụng.  
* **`KnowledgeBlock` (Khối kiến thức / Nhóm môn):**  
  * `block_id` (PK): Mã khối kiến thức (Đại cương, Cơ sở nhóm ngành, Chuyên ngành, Đồ án tốt nghiệp).  
  * `curriculum_id` (FK): Thuộc CTĐT nào.  
  * `parent_block_id` (FK): Hỗ trợ cấu trúc cây phân cấp nhiều tầng.  
  * `selection_rule_type`: Enum (`ALL_MANDATORY`, `MIN_CREDITS`, `PICK_K_OF_N`).  
  * `required_credits`: Số tín chỉ tối thiểu phải đạt trong nhóm này.  
* **`CourseGroupMembership` (Môn học thuộc Nhóm):**  
  * `block_id` (FK), `course_id` (FK).  
  * `is_mandatory_in_group`: Bắt buộc hay tự chọn trong nhóm này.  
* **`AcademicRegulation` (Quy chế đào tạo):**  
  * `regulation_id` (PK): Mã bộ quy chế.  
  * `min_credits_main_term`: Tín chỉ tối thiểu kỳ chính (ví dụ: 14).  
  * `max_credits_main_term`: Tín chỉ tối đa kỳ chính (ví dụ: 25).  
  * `max_credits_summer_term`: Tín chỉ tối đa kỳ hè (ví dụ: 8).  
  * `max_terms_allowed`: Số học kỳ tối đa trước khi bị buộc thôi học.  
  * `final_term_min_exempt`: Cờ cho phép kỳ cuối không bị chặn dưới bởi `min_credits`.

#### **3\. Nhóm thực thể Sinh viên & Lịch sử (Student State)**

* **`StudentProfile` (Hồ sơ sinh viên):**  
  * `student_id` (PK): Mã số sinh viên.  
  * `curriculum_id` (FK): Khung CTĐT áp dụng.  
  * `current_term_index`: Học kỳ hiện tại.  
  * `expected_objective_weights`: Cấu hình ưu tiên cá nhân (ví dụ: muốn tốt nghiệp sớm hay học nhàn).  
* **`StudentAcademicRecord` (Học bạ tích lũy):**  
  * `student_id` (FK), `course_id` (FK).  
  * `status`: Enum (`PASSED` \- đã đạt, `FAILED` \- không đạt, `EXEMPTED` \- miễn trừ/chuyển đổi).  
  * `term_completed`: Kỳ đã hoàn thành.

#### **4\. Nhóm thực thể Lộ trình đề xuất (Output Study Plan)**

* **`StudyPlan` (Phương án lộ trình):**  
  * `plan_id` (PK), `student_id` (FK).  
  * `strategy_type`: Loại chiến lược (`FAST_TRACK`, `BALANCED`, `RISK_AVERSE`).  
  * `metrics`: JSON chứa các chỉ số (tổng kỳ hoàn thành, độ lệch chuẩn tín chỉ, điểm rủi ro).  
* **`ScheduledCourse` (Học phần được xếp):**  
  * `plan_id` (FK), `course_id` (FK).  
  * `term_index`: Học kỳ được gán (tt).  
  * `explanation_tags`: Dữ liệu vết (Vết phụ thuộc, lý do chọn môn tự chọn, kỳ mở môn tương ứng).

---

## **4\. Các trường hợp biên (Edge Cases) & Phân tích rủi ro hệ thống**

### **4.1. Các trường hợp biên (Edge Cases)**

1. **Chu trình phụ thuộc ẩn (Circular Dependency Deadlock):**  
   * *Tình huống:* Dữ liệu CTĐT qua nhiều lần cập nhật xuất hiện chu trình gián tiếp: Môn A→B→C→AA→B→C→A.  
   * *Hành vi yêu cầu:* Module kiểm tra tính hợp lệ dữ liệu (Catalog Validator) phải phát hiện chu trình bằng thuật toán Tarjan/DFS trước khi đưa vào Solver và báo lỗi dữ liệu cấu hình.  
2. **Kỳ mở môn gây bế tắc thời gian (Offering Window Phase Shift):**  
   * *Tình huống:* Môn AA là tiên quyết của BB. Môn AA chỉ mở kỳ Mùa Thu (Kỳ 1, 3, 5). Môn BB cũng chỉ mở kỳ Mùa Thu.  
   * *Hệ quả:* Sinh viên học AA ở Kỳ 1, không thể học BB ở Kỳ 2 (vì BB không mở), buộc phải đợi đến Kỳ 3\. Lộ trình tự động bị kéo dài thêm 1 năm. Nếu không tính đến, sinh viên sẽ bị trễ hạn đào tạo tối đa.  
3. **Hiện tượng "Thừa tín chỉ bất khả kháng" trong nhóm tự chọn:**  
   * *Tình huống:* Nhóm tự chọn yêu cầu tối thiểu 6 tín chỉ. Các môn trong nhóm đều có số tín chỉ là 4\.  
   * *Hệ quả:* Sinh viên bắt buộc phải học 2 môn \= 8 tín chỉ (vượt 2 tín chỉ). Khi đó, tổng tín chỉ thực học có thể vượt 138 (thành 140 tín chỉ).  
   * *Hành vi yêu cầu:* Cần xác nhận quy tắc: 138 là con số chính xác tuyệt đối (=138=138) hay là ngưỡng cận dưới (≥138≥138).  
4. **Ngoại lệ học kỳ cuối (Terminal Semester Deficit):**  
   * *Tình huống:* Ở học kỳ áp chót, sinh viên đã tích lũy được 130 tín chỉ. Kỳ cuối chỉ còn 8 tín chỉ (Khóa luận tốt nghiệp). Quy chế kỳ chính yêu cầu tối thiểu 14 tín chỉ.  
   * *Hành vi yêu cầu:* Hệ thống phải có rule cho phép miễn trừ cận dưới (WminWmin​) cho học kỳ tốt nghiệp cuối cùng.  
5. **Sinh viên "Nợ môn" làm vỡ chuỗi:**  
   * *Tình huống:* Sinh viên năm 3 còn nợ môn Toán cao cấp (tiên quyết của nhiều môn chuyên ngành), quỹ thời gian đào tạo còn lại Tremain\<Tremain​\< chiều dài đường đi dài nhất (Critical Path) của các môn còn lại.  
   * *Hành vi yêu cầu:* Hệ thống phát hiện ngay bài toán vô nghiệm và xuất báo cáo xung đột thay vì cố ép lộ trình sai.

### **4.2. Rủi ro hệ thống & Rủi ro thuật toán**

┌─────────────────────────────────┬──────────────────────────────────┬─────────────────────────────────┐  
│ RỦI RO KIẾN TRÚC & DỮ LIỆU     │ RỦI RO THUẬT TOÁN TỔ HỢP         │ RỦI RO VẬN HÀNH & TÍNH ĐÚNG     │  
├─────────────────────────────────┼──────────────────────────────────┼─────────────────────────────────┤  
│ • Dữ liệu quy chế bị "hard-code"│ • Bùng nổ tổ hợp (Combinatorial  │ • Thuật toán đưa ra lộ trình ảo │  
│   khiến mỗi lần đổi luật phải     │   Explosion) khi nhóm tự chọn     │   (không có giảng viên/lớp học  │  
│   viết lại solver.               │   quá rộng.                      │   thực tế để đăng ký).          │  
│ • Không giải thích được lý do   │ • Rơi vào bẫy cục bộ (Local Opt) │ • Sinh viên đã học môn tương    │  
│   khi bài toán Infeasible.      │   nếu dùng Metaheuristics thuần. │   đương nhưng mã môn khác nhau. │  
└─────────────────────────────────┴──────────────────────────────────┴─────────────────────────────────┘

* **Giải pháp cho bùng nổ tổ hợp:** Áp dụng phương pháp phân tầng: Giai đoạn 1 giải bài toán chọn tập môn tự chọn thỏa mãn khối kiến thức (0/1 Knapsack / Set Covering); Giai đoạn 2 lập lịch thời gian cho tập môn đã chọn bằng CP-SAT (Constraint Programming) hoặc IP (Integer Programming).  
* **Giải pháp giải thích Infeasibility:** Tích hợp bộ trích xuất tập con không thỏa tối thiểu (Conflict Refiner / MUS Extractor) để truy vết chính xác tập ràng buộc gây nghẽn.

---

## **5\. Các thông tin còn thiếu cần Người dùng (Product Owner) xác nhận**

Để hoàn thiện bản đặc tả này thành bản thiết kế kỹ thuật, tôi cần bạn làm rõ **6 nhóm câu hỏi nghiệp vụ** sau:

### **Câu hỏi 1: Quy định cụ thể về ngưỡng tín chỉ mỗi kỳ**

1. Giá trị WminWmin​ và WmaxWmax​ chuẩn cho một học kỳ chính là bao nhiêu tín chỉ?  
2. Có phân biệt giới hạn tín chỉ theo học lực của sinh viên không (ví dụ: GPA khá/giỏi được đăng ký tối đa 25-28 tín chỉ, GPA trung bình chỉ được tối đa 18-20 tín chỉ)?  
3. Kỳ hè (Summer Term) có được tự động xếp môn không, hay chỉ được xếp khi sinh viên bật tùy chọn "Muốn học kỳ hè"? Giới hạn tối đa của kỳ hè là bao nhiêu tín chỉ?

### **Câu hỏi 2: Bản chất của con số 138 tín chỉ**

1. Con số 138 tín chỉ là **bằng chính xác tuyệt đối (=138=138)** hay là **ngưỡng tối thiểu (≥138≥138)**?  
2. Trong trường hợp tổ hợp môn tự chọn có tín chỉ lẻ dẫn đến tổng tín chỉ bằng 139 hoặc 140, hệ thống có được chấp nhận phương án đó không?

### **Câu hỏi 3: Ranh giới chính xác giữa "Học trước" (Pre-course) và "Tiên quyết" (Prerequisite)**

1. Trong quy chế của trường, điều kiện "Học trước" được định nghĩa cụ thể là gì? (Ví dụ: Chỉ cần tham gia học và có điểm thi ≥0≥0, hay phải đạt điểm thi rớt nhưng có điểm danh, hay điểm số ≥3.0≥3.0 trên thang 10?).  
2. Nếu sinh viên rớt môn "Tiên quyết" thì chắc chắn không được học môn sau; còn nếu rớt môn "Học trước" thì có được phép học môn sau hay không?

### **Câu hỏi 4: Quy tắc thay thế và Môn tương đương (Equivalence)**

1. Khi một môn học cũ bị hủy bỏ hoặc đổi mã môn, quy tắc ánh xạ môn tương đương được cấu hình như thế nào?  
2. Sinh viên đã học môn thay thế C1′C1′​ thì hệ thống có tự động hiểu là đã thỏa mãn điều kiện tiên quyết cho môn C2C2​ (vốn đòi hỏi môn gốc C1C1​) hay không?

### **Câu hỏi 5: Khung thời gian đào tạo tối đa**

1. Thời gian đào tạo chuẩn là bao nhiêu học kỳ (ví dụ: 8 kỳ \= 4 năm)?  
2. Thời gian đào tạo tối đa cho phép là bao nhiêu học kỳ trước khi bị quá hạn (ví dụ: 12 kỳ \= 6 năm)?

### **Câu hỏi 6: Yêu cầu về mức độ đa dạng giữa các lộ trình**

1. Khi sinh ra nhiều phương án (ví dụ: 3 phương án), bạn định nghĩa thế nào là "khác biệt có ý nghĩa"?  
   * Khác nhau về **tập môn tự chọn** được chọn?  
   * Hay khác nhau về **thời điểm xếp môn** (phân bố kỳ)?  
   * Hay khác nhau về **tổng số học kỳ tốt nghiệp** (ví dụ: 3.5 năm vs 4.0 năm)?

---

## **6\. Tiêu chí nghiệm thu có thể kiểm thử tự động (Automated Acceptance Criteria)**

Mọi quy tắc sẽ được kiểm thử bằng các kịch bản tự động theo định dạng BDD (Behavior-Driven Development / Given-When-Then):

### **AC-01: Kiểm tra tính bảo toàn và không trùng lặp tín chỉ (Credit Integrity)**

gherkin  
Scenario: Lộ trình hoàn thành phải đạt đúng ngưỡng và không tính trùng môn  
 Given Chương trình đào tạo yêu cầu tích lũy 138 tín chỉ  
 And Môn học C\_101 thuộc cả "Khối Cơ sở nhóm ngành" và "Khối Chuyên ngành hẹp A" với số tín chỉ là 3  
 When Hệ thống sinh ra một lộ trình học tập P  
 Then Tổng số tín chỉ của các môn trong P cộng với các môn đã tích lũy phải đạt đúng 138  
 And Môn C\_101 chỉ được xuất hiện đúng 1 lần trong lộ trình P  
 And Số tín chỉ của C\_101 chỉ được cộng đúng 1 lần (3 tín chỉ) vào tổng số tín chỉ tích lũy

### **AC-02: Kiểm tra tính hợp lệ của chuỗi Tiên quyết và Kỳ mở môn (Topological & Calendar Validity)**

gherkin  
Scenario: Môn học chỉ được xếp sau khi môn tiên quyết đã hoàn thành và đúng kỳ mở môn  
 Given Môn "Hệ quản trị CSDL" có tiên quyết là "Cấu trúc dữ liệu và giải thuật"  
 And Môn "Hệ quản trị CSDL" chỉ được mở vào "Học kỳ Mùa Thu"  
 When Hệ thống xếp lịch cho môn "Hệ quản trị CSDL" vào học kỳ T\_k  
 Then Kỳ T\_k phải là Học kỳ Mùa Thu  
 And Môn "Cấu trúc dữ liệu và giải thuật" phải được xếp ở học kỳ T\_m với T\_m \< T\_k (hoặc nằm trong C\_passed)

### **AC-03: Kiểm tra tuân thủ trần và sàn tín chỉ mỗi kỳ (Credit Load Bounds)**

gherkin  
Scenario: Mỗi học kỳ chính phải nằm trong giới hạn tín chỉ quy chế  
 Given Quy chế quy định kỳ chính có Min\_Credits \= 14 và Max\_Credits \= 24  
 When Duyệt qua tất cả các học kỳ t trong lộ trình đề xuất (ngoại trừ kỳ tốt nghiệp cuối cùng)  
 Then Tổng số tín chỉ được xếp trong kỳ t phải \>= 14  
 And Tổng số tín chỉ được xếp trong kỳ t phải \<= 24

### **AC-04: Tính bất biến với các môn đã hoàn thành (Idempotency against Passed Courses)**

gherkin  
Scenario: Không bao giờ xếp lại môn sinh viên đã đạt  
 Given Sinh viên S đã hoàn thành môn "Nhập môn lập trình" ở kỳ trước với trạng thái "PASSED"  
 When Hệ thống tạo bất kỳ lộ trình nào cho sinh viên S  
 Then Môn "Nhập môn lập trình" tuyệt đối không xuất hiện trong danh sách các môn cần học tiếp  
 And Môn "Nhập môn lập trình" được tự động đánh dấu là điều kiện tiên quyết đã thỏa mãn cho các môn sau

### **AC-05: Khả năng giải thích khi bài toán Bất khả thi (Infeasibility & MUS Explanation)**

gherkin  
Scenario: Trả về tập xung đột tối thiểu khi không thể tìm ra lộ trình hợp lệ  
 Given Sinh viên chỉ còn tối đa 2 học kỳ trước khi hết thời gian đào tạo  
 And Danh sách môn bắt buộc còn lại đòi hỏi một chuỗi tiên quyết gồm 4 môn nối tiếp nhau (A \-\> B \-\> C \-\> D)  
 When Hệ thống thực thi thuật toán tìm kiếm lộ trình  
 Then Hệ thống KHÔNG được trả về bất kỳ phương án lộ trình nào  
 And Hệ thống trả về mã trạng thái INFEASIBLE kèm theo báo cáo xung đột  
 And Báo cáo chỉ đích danh: Chiều dài chuỗi tiên quyết (4 kỳ) vượt quá số kỳ còn lại (2 kỳ)

### **AC-06: Tính độc lập của Dữ liệu quy chế (Rule Engine Decoupling)**

gherkin  
Scenario: Thay đổi quy chế đào tạo mà không sửa code thuật toán  
 Given Quy chế đào tạo thay đổi Max\_Credits kỳ chính từ 24 xuống 20 tín chỉ trong tệp cấu hình  
 When Chạy bộ kiểm thử tự động với dữ liệu sinh viên đầu vào giữ nguyên  
 Then Mọi phương án lộ trình mới sinh ra đều có số tín chỉ mỗi kỳ \<= 20  
 And Toàn bộ test suite vượt qua mà không có bất kỳ thay đổi nào trong mã nguồn thuật toán cốt lõi

### **AC-07: Tính đa dạng có ý nghĩa giữa các phương án đề xuất (Plan Diversity)**

gherkin  
Scenario: Các phương án đề xuất phải phản ánh các chiến lược mục tiêu khác nhau  
 Given Yêu cầu sinh ra 3 phương án lộ trình cho sinh viên  
 When Hệ thống trả về 3 phương án P\_1, P\_2, P\_3  
 Then P\_1 phải tối ưu về số học kỳ (Fast-Track) với T\_grad nhỏ nhất  
 And P\_2 phải tối ưu về độ lệch chuẩn tín chỉ (Balanced) với Var(Credits) nhỏ nhất  
 And P\_3 phải tối ưu về độ trễ an toàn môn nút cổ chai (Risk-Averse)  
 And Ma trận phân bổ kỳ giữa P\_1, P\_2, P\_3 không được trùng nhau hoàn toàn (Distance metric \> 0\)  
---

## **7\. Kiến trúc Hệ thống Đề xuất (Architectural Blueprint)**

Để đáp ứng yêu cầu "tách biệt dữ liệu \- quy tắc \- thuật toán" và "khả năng giải thích", kiến trúc đề xuất gồm 4 lớp sau:

┌────────────────────────────────────────────────────────────────────────┐  
│ 1\. DATA LAYER (JSON / Database)                                        │  
│   • course\_catalog.json (Môn học, tín chỉ, độ khó)                     │  
│   • curriculum\_tree.json (Khối kiến thức, quy tắc nhóm, 138 TC)        │  
│   • offering\_rules.json (Lịch mở môn kỳ Thu/Xuân/Hè)                  │  
│   • academic\_regulations.json (Min/Max tín chỉ, thời gian tối đa)       │  
└───────────────────────────────────┬────────────────────────────────────┘  
                                   │  
                                   ▼  
┌────────────────────────────────────────────────────────────────────────┐  
│ 2\. MODEL COMPILER & VALIDATOR                                          │  
│   • Kiểm tra chu trình phụ thuộc (Cycle Detection)                    │  
│   • Lập bản đồ đồ thị DAG & tính đường găng (Critical Path)            │  
│   • Biên dịch dữ liệu & quy chế thành bài toán CSP/ILP toán học        │  
└───────────────────────────────────┬────────────────────────────────────┘  
                                   │  
                                   ▼  
┌────────────────────────────────────────────────────────────────────────┐  
│ 3\. CORE OPTIMIZATION ENGINE (Rule-agnostic Solver)                     │  
│   • Constraint Programming Solver (e.g., OR-Tools CP-SAT)             │  
│   • Đa hàm mục tiêu (Lexicographic / Weighted Sum Search)              │  
│   • Bộ trích xuất xung đột tối thiểu (MUS Extractor for Infeasibility)│  
└───────────────────────────────────┬────────────────────────────────────┘  
                                   │  
                                   ▼  
┌────────────────────────────────────────────────────────────────────────┐  
│ 4\. EXPLANATION & PRESENTATION LAYER                                    │  
│   • Giải trình vết xếp môn (Vì sao môn X học ở kỳ Y)                  │  
│   • So sánh chỉ số giữa các phương án (Fast vs Balanced vs Risk)      │  
│   • Báo cáo chẩn đoán nguyên nhân khi không có phương án hợp lệ       │  
└────────────────────────────────────────────────────────────────────────┘  
---

Xin mời bạn xem xét bản đặc tả trên. Hãy cung cấp phản hồi hoặc giải đáp **6 nhóm câu hỏi ở Mục 5** để chúng ta chốt phương án và bước sang giai đoạn thiết kế mô hình toán / thuật toán chi tiết\!
