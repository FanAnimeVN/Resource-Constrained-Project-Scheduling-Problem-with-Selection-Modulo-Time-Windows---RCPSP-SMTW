Feature: AC-05 Khả năng giải thích khi bài toán Bất khả thi (Infeasibility & MUS Explanation)

  Scenario: Trả về tập xung đột tối thiểu khi không thể tìm ra lộ trình hợp lệ
    Given Sinh viên chỉ còn tối đa 2 học kỳ trước khi hết thời gian đào tạo
    And Danh sách môn bắt buộc còn lại đòi hỏi một chuỗi tiên quyết gồm 4 môn nối tiếp nhau (A -> B -> C -> D)
    When Hệ thống thực thi thuật toán tìm kiếm lộ trình
    Then Hệ thống KHÔNG được trả về bất kỳ phương án lộ trình nào
    And Hệ thống trả về mã trạng thái INFEASIBLE kèm theo báo cáo xung đột
    And Báo cáo chỉ đích danh: Chiều dài chuỗi tiên quyết (4 kỳ) vượt quá số kỳ còn lại (2 kỳ)
