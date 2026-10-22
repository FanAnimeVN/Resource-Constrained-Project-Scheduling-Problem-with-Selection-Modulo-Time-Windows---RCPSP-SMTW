Feature: AC-07 Tính đa dạng có ý nghĩa giữa các phương án đề xuất (Plan Diversity)

  Scenario: Các phương án đề xuất phải phản ánh các chiến lược mục tiêu khác nhau
    Given Yêu cầu sinh ra 3 phương án lộ trình cho sinh viên
    When Hệ thống trả về 3 phương án P_1, P_2, P_3
    Then P_1 phải tối ưu về số học kỳ (Fast-Track) với T_grad nhỏ nhất
    And P_2 phải tối ưu về độ lệch chuẩn tín chỉ (Balanced) với Var(Credits) nhỏ nhất
    And P_3 phải tối ưu về độ trễ an toàn môn nút cổ chai (Risk-Averse)
    And Ma trận phân bổ kỳ giữa P_1, P_2, P_3 không được trùng nhau hoàn toàn (Distance metric > 0)
