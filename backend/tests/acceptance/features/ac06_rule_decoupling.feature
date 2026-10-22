Feature: AC-06 Tính độc lập của Dữ liệu quy chế (Rule Engine Decoupling)

  Scenario: Thay đổi quy chế đào tạo mà không sửa code thuật toán
    Given Quy chế đào tạo thay đổi Max_Credits kỳ chính từ 24 xuống 20 tín chỉ trong tệp cấu hình
    When Chạy bộ kiểm thử tự động với dữ liệu sinh viên đầu vào giữ nguyên
    Then Mọi phương án lộ trình mới sinh ra đều có số tín chỉ mỗi kỳ <= 20
    And Toàn bộ test suite vượt qua mà không có bất kỳ thay đổi nào trong mã nguồn thuật toán cốt lõi
