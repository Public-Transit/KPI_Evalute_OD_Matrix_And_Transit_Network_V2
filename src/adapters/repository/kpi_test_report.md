# Báo Cáo Phân Tích & Kiểm Thử Các Chỉ Số KPI (Spatial Coverage, Circuity, Transfer)

Tài liệu này tổng hợp toàn bộ các trường hợp kiểm thử (test cases) chuyên biệt được thiết kế để đánh giá độ chính xác của 3 bộ tính toán KPI cốt lõi trong hệ thống:
1. **Spatial Coverage KPI** (Tỷ lệ phủ không gian khu vực đầu cuối)
2. **Circuity Index KPI** (Độ vòng vèo của tuyến)
3. **Transfer Rate KPI** (Số lần chuyển tuyến)

---

## Phần 1: Kiểm Thử Spatial Coverage KPI (Tỷ lệ Vùng Phủ)
*(Kế thừa từ `spatial_coverage_test_report.md`)*

**Mục tiêu:** Kiểm tra khả năng tính toán diện tích phủ (coverage area) của các điểm dừng (stops) lên các vùng xuất phát (origin zone) và vùng kết thúc (destination zone). 
- Chỉ sử dụng các stop nằm bên trong vùng OD.
- "Boundary clipping": Các buffer của stop nếu tràn ra ngoài rìa zone sẽ bị cắt bỏ, chỉ tính phần diện tích nằm gọn bên trong zone.

### Các Test Case (Phân tích chi tiết):

| Case | Mục đích | Cấu trúc hạ tầng | Kết quả kỳ vọng | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **SC1** | Tỷ lệ phủ một phần ở trung tâm | Mạng gồm 2 zones vuông vức. Các trạm đặt ngay tại Tâm (Centroid) của từng zone. Bán kính `radius_m = 50`. | Trạm phủ được 1 phần diện tích nhỏ quanh tâm. Giá trị `score_ratio` tỷ lệ thuận theo công thức diện tích đường tròn/hình vuông. | ✅ PASS |
| **SC1 (Bán kính lớn)** | Tràn vùng phủ | Giống hệt SC1 nhưng đẩy bán kính `radius_m = 170`. | Các đường viền buffer bao trọn toàn bộ zone. Kết quả tỷ lệ phủ bị chặn trần (capped) ở mức tối đa `1.0` (100%). | ✅ PASS |
| **SC2** | Cắt nén không gian (Boundary clipping) | Trạm nằm lệch sát bờ viền của zone. | Một nửa vòng tròn buffer của trạm tràn ra khỏi hệ thống zone. Thuật toán cắt bỏ phần thừa -> Diện tích phủ nhỏ hơn so với đặt ở Tâm. | ✅ PASS |
| **SC3** | Trạm ảo/Chồng lấn nhiễu | Tạo các trạm có tọa độ giống hệt nhau hoặc đè lên nhau. | Hệ thống hợp nhất (intersection) bằng Shapely. Không bị tính gấp đôi KPI cho những điểm chồng lấn lên nhau (Diện tích thực tính). | ✅ PASS |
| **SC4** | Cách ly dữ liệu nhiễu giữa chặng | Các trạm không thuộc việc đón/trả ở OD (ví dụ trạm chuyển tuyến nằm ở zone giữa, hoặc các trạm xe lướt qua nhanh). | Bộ tính toán bỏ qua hoàn toàn các trạm sinh ra ở Leg giữa, giữ nguyên sự tinh khiết của Origin Coverage và Destination Coverage. | ✅ PASS |

---

## Phần 2: Kiểm Thử Circuity Index KPI (Độ Vòng Vèo)

**Mục tiêu:** Kiểm chứng công thức tính "Độ vòng vèo" của hành trình = `[Tổng độ dài chặng trên xe bus] / [Độ dài đường chim bay từ X tới Y]`.

### Các Test Case (Phân tích chi tiết):

| Case | Tên Repository | Mô tả Cấu trúc Lộ trình | Kết quả Kịch bản Khởi chạy Thực tế |
| :--- | :--- | :--- | :--- |
| **C1** | `FakeRepoC1` | **Đường chim bay hoàn hảo.** Tuyến xe buýt chạy thẳng tắp không rẽ một lần nào từ Zone 1 đến Zone 2. Khoảng cách đi xe = Khoảng cách thẳng. | **Kết quả KPI:** `score = 1.0` (Tuyệt đối tối ưu). Trả về chính xác thông tin `route_sequence` = `['R1']`. |
| **C2** | `FakeRepoC2` | **Khúc cua U-Turn (Detour).** Xe xuất phát từ Zone 1, chạy một vòng vèo hình chữ U rất dài ra khỏi khung khu vực rồi mới quay đầu về Zone 2. | **Kết quả KPI:** `score = ~2.878` (Khoảng cách trên xe dài gần gấp 3 lần đường chim bay). Phản ánh đúng độ kém hiệu quả của tuyến cong. |

---

## Phần 3: Kiểm Thử Transfer Rate KPI (Số lần Chuyển tuyến)

**Mục tiêu:** Đếm số thao tác đổi xe (transfer) khách hàng phải chịu đựng trong một cấu hình Candidates Trip đã được routing.

### Các Test Case (Phân tích chi tiết):

| Case | Tên Repository | Mô tả Cấu trúc Lộ trình | Kết quả Kịch bản Khởi chạy Thực tế |
| :--- | :--- | :--- | :--- |
| **T1** | `FakeRepoT1` | **Không chuyển tuyến định hướng.** Z1 và Z2 thông nhau trực tiếp bằng một tuyến nối thẳng. | **Kết quả KPI:** `score = 0`. Đại diện cho trải nghiệm đi lại liền mạch (1-Leg Trip). |
| **T2** | `FakeRepoT2` | **Trung chuyển ngã tư (Hub).** Hành khách phải đi tuyến R1 tới vùng Hub, sau đó xuống xe đi bộ sang bến chờ tuyến R2 để đến vùng đích. | **Kết quả KPI:** `score = 1`. (2-Leg Trip). |

*(Lưu ý: Nếu một Test Case vượt quá số lần chuyển tuyến có thể chấp nhận hoặc bị đứt gãy kết nối, KPI này sẽ rớt về mốc `Not valid`)*

---

### Xác Lập & Tái Kiểm Ước
- Tất cả các KPI đều được Inject thành các Modules dưới nền giao diện Service.
- Script tích hợp (Manual Runner) để tính toán Circuity và Transfer nằm tại `tests/test_manual_kpis.py`.
- Tách biệt hoàn toàn tính toán toán học không gian (Geospatial Python Models) và dữ liệu thực thể mô phỏng. Mọi giả định đều trùng khớp kỳ vọng mô hình Toán Học Không Gian bằng `Shapely`.
