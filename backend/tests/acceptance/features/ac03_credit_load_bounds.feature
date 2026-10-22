Feature: AC-03 Kiểm tra tuân thủ trần và sàn tín chỉ mỗi kỳ (Credit Load Bounds)

  Scenario: Mỗi học kỳ chính phải nằm trong giới hạn tín chỉ quy chế
    Given Quy chế quy định kỳ chính có Min_Credits = 14 và Max_Credits = 24
    When Duyệt qua tất cả các học kỳ t trong lộ trình đề xuất (ngoại trừ kỳ tốt nghiệp cuối cùng)
    Then Tổng số tín chỉ được xếp trong kỳ t phải >= 14
    And Tổng số tín chỉ được xếp trong kỳ t phải <= 24
