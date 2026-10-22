Feature: AC-01 Kiểm tra tính bảo toàn và không trùng lặp tín chỉ (Credit Integrity)

  Scenario Outline: Lộ trình hoàn thành phải đạt đúng ngưỡng và không tính trùng môn
    Given Chương trình đào tạo yêu cầu tích lũy 138 tín chỉ theo quy tắc "<rule>"
    And Môn học C_101 thuộc cả "Khối Cơ sở nhóm ngành" và "Khối Chuyên ngành hẹp A" với số tín chỉ là 3
    When Hệ thống sinh ra một lộ trình học tập P
    Then Tổng số tín chỉ của các môn trong P cộng với các môn đã tích lũy phải đạt đúng 138
    And Môn C_101 chỉ được xuất hiện đúng 1 lần trong lộ trình P
    And Số tín chỉ của C_101 chỉ được cộng đúng 1 lần (3 tín chỉ) vào tổng số tín chỉ tích lũy

    Examples:
      | rule     |
      | exact    |
      | at_least |
