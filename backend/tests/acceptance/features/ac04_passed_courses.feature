Feature: AC-04 Tính bất biến với các môn đã hoàn thành (Idempotency against Passed Courses)

  Scenario: Không bao giờ xếp lại môn sinh viên đã đạt
    Given Sinh viên S đã hoàn thành môn "Nhập môn lập trình" ở kỳ trước với trạng thái "PASSED"
    When Hệ thống tạo bất kỳ lộ trình nào cho sinh viên S
    Then Môn "Nhập môn lập trình" tuyệt đối không xuất hiện trong danh sách các môn cần học tiếp
    And Môn "Nhập môn lập trình" được tự động đánh dấu là điều kiện tiên quyết đã thỏa mãn cho các môn sau
