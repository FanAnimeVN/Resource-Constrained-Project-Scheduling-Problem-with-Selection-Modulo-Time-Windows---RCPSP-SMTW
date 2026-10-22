Feature: AC-02 Kiểm tra tính hợp lệ của chuỗi Tiên quyết và Kỳ mở môn (Topological & Calendar Validity)

  Scenario: Môn học chỉ được xếp sau khi môn tiên quyết đã hoàn thành và đúng kỳ mở môn
    Given Môn "Hệ quản trị CSDL" có tiên quyết là "Cấu trúc dữ liệu và giải thuật"
    And Môn "Hệ quản trị CSDL" chỉ được mở vào "Học kỳ Mùa Thu"
    When Hệ thống xếp lịch cho môn "Hệ quản trị CSDL" vào học kỳ T_k
    Then Kỳ T_k phải là Học kỳ Mùa Thu
    And Môn "Cấu trúc dữ liệu và giải thuật" phải được xếp ở học kỳ T_m với T_m < T_k (hoặc nằm trong C_passed)
