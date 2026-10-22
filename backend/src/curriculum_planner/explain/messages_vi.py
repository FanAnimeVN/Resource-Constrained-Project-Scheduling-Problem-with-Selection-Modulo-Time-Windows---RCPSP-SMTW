"""Template thông điệp tiếng Việt (mọi câu chữ hiển thị cho người dùng nằm ở đây)."""

# ---- chẩn đoán nhanh / vô nghiệm ----
EXPIRED = "Đã hết thời gian đào tạo tối đa (hạn chót {deadline}); không còn học kỳ nào để lập lộ trình."
MANDATORY_UNAVAILABLE = "Môn bắt buộc {course} không thể đăng ký: {reason}."
NO_OFFERING_LEFT = "Môn bắt buộc {course} không còn đợt mở nào trước hạn tối đa ({deadline})."
CHAIN_TOO_LONG = "Chuỗi tiên quyết {chain} cần tối thiểu {need} học kỳ, nhưng chỉ còn {have} học kỳ trước hạn tối đa ({deadline})."
CAPACITY = "Cần học thêm tối thiểu {need} TC nhưng {terms} học kỳ còn lại chỉ chứa tối đa {cap} TC."
BLOCK_IMPOSSIBLE = "Khối «{block}» cần {need} TC nhưng các môn còn có thể học chỉ đủ {have} TC."
EXCLUSIVE_MANDATORY = "Hai môn bắt buộc {a} và {b} loại trừ nhau."
INFEASIBLE_SUMMARY = (
    "Không tìm được lộ trình hợp lệ. Hệ thống không đưa ra lộ trình sai quy chế; dưới đây là nguyên nhân."
)
COMPLETED = "Sinh viên đã đáp ứng đủ yêu cầu tín chỉ của chương trình; không còn môn nào cần xếp."

# ---- nhóm ràng buộc (MUS) ----
GROUP = {
    "TOTAL": "HC-01: tổng tích lũy phải đạt {total} TC",
    "BLOCK": "HC-03: khối «{block}» cần {need} TC",
    "BLOCK_K": "HC-03: khối «{block}» cần chọn {k} môn",
    "MAND": "HC-03: phải hoàn thành môn bắt buộc {course}",
    "PREREQUISITE": "HC-04: {b} có tiên quyết {a} (phải ĐẠT {a} ở kỳ trước)",
    "PRE_COURSE": "HC-05: {b} có học trước {a} (phải đã học {a} ở kỳ trước)",
    "CO_REQUISITE": "HC-06: {b} song hành với {a} (học {a} trước hoặc cùng kỳ)",
    "EXCL": "HC-07: {a} và {b} loại trừ nhau",
    "CAP": "HC-08: {term} tối đa {cap} TC",
    "FLOOR": "HC-08: {term} (không phải kỳ cuối) tối thiểu {floor} TC",
    "SUMMER_CAP": "HC-09: {term} tối đa {cap} TC",
    "OFFER": "HC-10: {course} chỉ mở vào {kinds}",
    "DEADLINE": "HC-11: phải tốt nghiệp trước hạn tối đa {deadline}",
    "ACCUM": "Điều kiện môn: {course} cần tích lũy tối thiểu {m} TC trước khi học",
    "FINAL": "Điều kiện môn: {course} phải học ở học kỳ cuối",
    "PERSONAL_CAP": "Tùy chọn của bạn: tối đa {cap} TC mỗi kỳ chính",
    "PIN": "Tùy chọn của bạn: ghim {course} vào {term}",
    "EXCLUDED": "Tùy chọn của bạn: không học {course}",
    "TARGET": "Tùy chọn của bạn: tốt nghiệp chậm nhất {term}",
}

RELAX = {
    "DEADLINE": "Nếu được gia hạn thời gian đào tạo, có thể tốt nghiệp vào {term}.",
    "CAP": "Nếu được đăng ký vượt trần tín chỉ ({detail}), có thể tốt nghiệp vào {term}.",
    "FLOOR": "Nếu được phép đăng ký dưới mức tối thiểu ({detail}), có thể tốt nghiệp vào {term}.",
    "PERSONAL_CAP": "Nếu bỏ giới hạn tín chỉ cá nhân, có thể tốt nghiệp vào {term}.",
    "PIN": "Nếu bỏ ghim {detail}, có thể tốt nghiệp vào {term}.",
    "EXCLUDED": "Nếu cho phép học {detail}, có thể tốt nghiệp vào {term}.",
    "TARGET": "Nếu lùi kỳ tốt nghiệp mong muốn, có thể tốt nghiệp vào {term}.",
    "SUMMER": "Nếu bật học kỳ hè, có thể tốt nghiệp vào {term}.",
}

# ---- giải trình từng môn ----
SEL_MANDATORY = "Môn bắt buộc của khối «{block}»."
SEL_ELECTIVE = "Môn tự chọn được chọn để đủ {need} TC của khối «{block}»."
SEL_PREREQ = "Cần học để làm điều kiện cho {targets}."
SEL_OTHER = "Môn được chọn để hoàn tất yêu cầu tín chỉ."
WHY_INTEREST = "khớp sở thích của bạn ({topics})"
WHY_UNLOCK = "là môn trước của {targets} cũng có trong lộ trình"
WHY_RISK_LOW = "ít rủi ro (không có chuỗi môn phụ thuộc phía sau)"
WHY_SHORT = "chỉ {credits} TC"

TIME_EARLIEST = "Đây là học kỳ sớm nhất có thể."
TIME_BLOCKED_PREREQ = "Không thể học ở {term}: môn trước {pre} chưa hoàn thành (xếp ở {pre_term})."
TIME_BLOCKED_NOT_PASSED = "Không thể học ở {term}: chưa đạt môn tiên quyết {pre}."
TIME_BLOCKED_OFFER = "Không thể học ở {term}: môn chỉ mở vào {kinds}."
TIME_BLOCKED_CAP = "Không thể học ở {term}: kỳ đó sẽ vượt trần {cap} TC."
TIME_BLOCKED_ACCUM = "Không thể học ở {term}: chưa tích lũy đủ {m} TC."
TIME_BLOCKED_FINAL = "Môn phải học ở học kỳ cuối của lộ trình."
TIME_BLOCKED_SUCC = "Không thể dời sang {term}: các môn khác trong lộ trình sẽ vi phạm ràng buộc."
TIME_BLOCKED_OTHER = "Không thể học ở {term}: {reason}."
TIME_STRATEGY = "Có thể học sớm hơn ({term}) nhưng được dời để {goal}."
STRATEGY_GOAL = {
    "FAST_TRACK": "tốt nghiệp sớm nhất",
    "BALANCED": "cân bằng tải các học kỳ",
    "RISK_AVERSE": "ưu tiên môn rủi ro cao học trước",
    "SPECIALIZATION_FOCUS": "tập trung theo định hướng",
    "PERSONALIZED": "dung hòa các mục tiêu theo trọng số của bạn",
}
REQ_PASSED = "{pre}: đã hoàn thành."
REQ_PLANNED = "{pre}: xếp ở {term}."
RETAKE_SAFE = "Nếu không đạt, có thể học lại ở {term} mà vẫn kịp tốt nghiệp đúng mục tiêu."
RETAKE_UNSAFE = "Nếu không đạt, việc học lại sẽ làm chậm tiến độ tốt nghiệp."

# ---- tóm tắt phương án ----
HL_GRAD = "Dự kiến tốt nghiệp {term} ({n} học kỳ chính nữa)."
HL_VS_STANDARD_EARLY = "Sớm hơn tiến độ chuẩn {n} học kỳ chính."
HL_VS_STANDARD_LATE = "Chậm hơn tiến độ chuẩn {n} học kỳ chính."
HL_VS_STANDARD_ON = "Đúng tiến độ chuẩn."
HL_LOAD = "Tải mỗi kỳ chính từ {lo} đến {hi} TC (độ lệch chuẩn {std})."
HL_SUMMER = "Sử dụng {n} học kỳ hè."
HL_RISK = "{pct}% trọng số rủi ro của môn bắt buộc có đệm học lại."
HL_SURPLUS = "Tích lũy {total} TC (dư {surplus} TC so với yêu cầu)."
