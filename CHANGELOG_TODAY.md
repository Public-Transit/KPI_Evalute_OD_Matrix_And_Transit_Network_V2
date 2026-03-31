# CHANGELOG: Đợt Nâng Cấp Kiến Trúc Domain V2 (Hôm Nay)

Tài liệu này ghi chú lại luồng ý tưởng và các công việc thực tế đã triển khai trong đợt refactor Domain sang V2.

## 1. Tách Biệt Logic Lọc Chuyến Đi (Filter V2)
- **Ý tưởng của bạn:** Muốn tách logic lọc (`filter.py`) sang V2. Ở V2, bộ lọc nhận vào duy nhất 1 `CandidateTrip` (chuyến đi thô) và trả ra 1 `Trip` (chuyến đi thực tế tối ưu nhất) thay vì nhận một mảng list.
- **Thực thi:** Khởi tạo `filter_v2.py` với class `MinDistanceCandidateTripFilterV2`. Logic được chuyển đổi thành công để ép kiểu chuẩn 1-1, đánh giá qua khoảng cách đi bộ từ Zone Centroid.

## 2. Kết Nối Luồng V2 Vào Service & API
- **Ý tưởng của bạn:** Khớp luồng V2 mới làm vào tầng Application Service và Entrypoint (API) để in ra danh sách các cặp OD kèm theo "những chuyến đi khả thi nhất".
- **Thực thi:** 
  - Thêm function `batch_route_all_od_pairs_v2` vào `routing_services.py`.
  - Mở một endpoint mới `@app.post("/api/routes/v2/feasible-trips")` trong `api.py` có khả năng xuất trực tiếp raw JSON các chuyến đi thành công.

## 3. Cấu Trúc Lại Routing Result và KPI.
- **Ý tưởng của bạn:** Nhóm 1 `CandidateTrip` và `Trip` tương ứng thành 1 entity có tên `EvaluatedRoutingOption`. Sửa `ODRoutingResultV2` chứa một list các Option này. Tái thiết kế các hàm KPI (`kpi_base.py`, `transfer_kpi`, `circuity_kpi`) để nhận đầu vào là thẻ `EvaluatedRoutingOption` mới này. Xóa hẳn thiết kế cũ.
- **Thực thi:** 
  - Bạn đã chủ động đập đi xây lại core structure nghiệp vụ này và xóa các file rác V1 (`filter.py`, `routing_result.py`). 
  - Đội ngũ AI tiến hành rà soát 1 lượt toàn bộ thư mục `domain`, fix tự động các lỗi `NameError` và `ImportError` do thiếu thư viện ở các file liên quan để luồng của bạn hoàn toàn chạy thông suốt.

## 4. Đồng Bộ Unit Test & Viết Docs
- **Ý tưởng của bạn:** Yêu cầu dọn dẹp và cập nhật lại toàn bộ bộ Unit Test do việc xóa V1 làm hỏng cú pháp. Đồng thời viết file mô tả cấu trúc hệ thống.
- **Thực thi:**
  - Sửa và pass toàn bộ 25 bài Unit Test (Sửa hàng loạt các lỗi cú pháp IndentationError và Import do đổi cấu trúc).
  - Khai tử file test cũ không còn tác dụng `test_spatial_coverage_kpi.py`.
  - Chỉnh sửa `project_understanding.md` xóa các keyword V1.
  - Sáng tác file `DOMAIN_DESIGN_DESCRIBE.md` tóm tắt toàn bộ khái niệm DDD đang được áp dụng trong project. Đóng gói kiến trúc Domain chuẩn 100% không còn xung đột.
