# Tài liệu: Đặc tả các Test Case Định tuyến & Bộ lọc (Transit Network)

Tài liệu này mô tả chi tiết các bộ repository giả lập (Fake Repositories) được xây dựng để kiểm chứng tính đúng đắn của công cụ định tuyến (`routing.py`) và logic lọc hành trình (`filter_v2.py`). Các trường hợp thử nghiệm bao gồm từ kết nối cơ bản đến các tình huống hình học không gian phức tạp.

---

## 1. Bộ Thử nghiệm Định tuyến Tịnh tiến (Dòng L - Level)
**Mục tiêu:** Xác minh rằng `CombinedRoutingEngine` tìm thấy toàn bộ các tùy chọn `CandidateTrip` hợp lệ (đi thẳng và chuyển tuyến 1 lần).

| Case | Tên | Mục đích | Kiến trúc mạng lưới |
| :--- | :--- | :--- | :--- |
| **L1** | Tối giản | Kiểm tra kết nối cơ bản nhất. | 2 Vùng, 1 Tuyến đi thẳng. |
| **L2** | Cạnh tranh trực tiếp | Tìm kiếm nhiều ứng viên đi thẳng. | 2 Vùng, 2 Tuyến đi thẳng (Nhanh vs Chậm). |
| **L3** | Trung chuyển bắt buộc | Kiểm tra logic chuyển tuyến 1 lần. | 3 Vùng, 2 Tuyến gặp nhau tại Hub (Không có đường thẳng). |
| **L4** | Lựa chọn hỗn hợp | Kiểm tra cả đi thẳng và chuyển tuyến. | 3 Vùng, 1 Tuyến thẳng dài vs 1 Lộ trình chuyển tiếp ngắn. |
| **L5** | Lưới tổ nhện | Thử nghiệm tìm đường trong mạng lưới dày đặc. | 5 Vùng, 7 Tuyến cắt nhau chằng chịt (Web pattern). |

**Chứng minh Logic:**
Chạy script `src/adapters/repository/visualize_repo/run_all_levels.py`. Kết quả sẽ tính toán các candidate và lưu biểu đồ tại thư mục `test_plots/`.

---

## 2. Bộ Thử nghiệm Lọc & Tối ưu hóa (Dòng F - Filter)
**Mục tiêu:** Xác minh rằng `MinDistanceCandidateTripFilterV2` chọn chính xác `Trip` tối ưu (trạm lên, trạm xuống và trạm trung chuyển cụ thể) từ một `CandidateTrip`.

| Case | Tên | Mục đích | Logic kiểm chứng |
| :--- | :--- | :--- | :--- |
| **F1** | Ưu tiên Tiếp cận | Ưu tiên khoảng cách đi bộ ngắn nhất. | Chọn trạm có khoảng cách Euclidean tới tâm vùng (centroid) nhỏ nhất. |
| **F2** | Xử lý Hòa (Tie-Breaker) | Ưu tiên quãng đường trên xe khi khoảng cách đi bộ bằng nhau. | Khi khoảng cách đi bộ bằng nhau tuyệt đối, chọn trạm giúp giảm thiểu quãng đường di chuyển trên xe. |
| **F3** | Điểm Trung chuyển | Lựa chọn điểm giao tối ưu. | Nếu 2 tuyến chung nhau nhiều trạm, chọn trạm trung chuyển giúp tổng quãng đường trên xe nhỏ nhất. |
| **F4** | Đặc quyền Tiếp cận | Ưu tiên đi bộ ngắn hơn xe chạy. | Kiểm chứng việc chọn trạm gần tâm (đi bộ ít) ngay cả khi nó khiến hành trình trên xe dài hơn (ngược chiều tối ưu quãng đường). |
| **F6** | Xử lý Hòa Chuyển Tuyến (O/D Symmetry) | Khử hòa khi có nhiều trạm O/D cách đều tâm. | Tương tự F2 nhưng áp dụng cho trip có 1 lần chuyển tuyến. Yêu cầu tính tổng quãng đường xe bus (route distance) của cả 2 chặng cộng lại để quyết định trạm ưu tiên. |
| **F5** | Lưới Ma trận Lớn | Tìm kiếm tối ưu trong 27 tổ hợp. | Kiểm tra khả năng lọc ra hành trình tối ưu duy nhất trong một ma trận trạm phức tạp. |

**Chứng minh Logic:**
Chạy script `src/adapters/repository/visualize_repo/run_filter_tests.py`. Đầu ra console sẽ in chi tiết các trạm được chọn, chứng minh tính toán chính xác. Biểu đồ lưu tại `filter_plots/`.

---

## 3. Bộ Thử nghiệm Tọa độ Ngoài Tuyến (Dòng Off - Off-Route)
**Mục tiêu:** Xác minh rằng `ShapelyGeometryCalculator` xử lý đúng các trạm không nằm khớp hoàn toàn trên đỉnh (vertex) của hình dạng tuyến đường (Route shape).

| Case | Tên | Mục đích | Thử thách không gian |
| :--- | :--- | :--- | :--- |
| **Off1** | Trạm giữa cạnh | Nội suy tuyến tính. | Trạm nằm trên đoạn thẳng nối 2 đỉnh nhưng không phải là đỉnh của Route. |
| **Off2** | Sai số GPS (Drift) | Chiếu điểm gần nhất. | Trạm nằm lệch hẳn ra ngoài tuyến đường (offset). Hệ thống phải chiếu vuông góc để tính toán. |

**Chứng minh Logic:**
Chạy script `src/adapters/repository/visualize_repo/run_off_route_tests.py`. Nó chứng minh hệ thống tự động "snap" trạm vào tuyến và tính toán quãng đường phân đoạn chính xác.

---

## 4. Bộ Thử nghiệm Tổng hợp Master (Master Case - Mini City)
**Mục tiêu:** Mô phỏng một thành phố nhỏ hoàn chỉnh để kiểm tra hiệu năng (stress-test) và tính toàn vẹn của luồng dữ liệu từ Routing, Filtering đến tính toán KPI.

| Case | Tên | Thành phần | Kịch bản thử nghiệm |
| :--- | :--- | :--- | :--- |
| **Master** | Mini Smart City | 15 Vùng, 10 Tuyến (Trục, Gom, Vòng), 50+ Trạm. | Kết hợp định tuyến xuyên thành phố, trung chuyển đa điểm và các tuyến vòng vèo. Mã trạm được đánh số đơn giản (`#1`, `#2`,...) để dễ quan sát dãn nhãn. |

**Chứng minh Logic:**
Chạy script `src/adapters/repository/visualize_repo/run_master_test.py`. Kết quả sẽ phân tích đồng thời nhiều cặp OD và hiển thị bản đồ toàn thành phố trong thư mục `master_plots/`.

---

## 5. Lưu ý về Giới hạn Thuật toán Định tuyến (Routing Constraints)

Hiện tại, bộ máy định tuyến `CombinedRoutingEngine` có một số đặc điểm quan trọng cần lưu ý khi thiết kế Test Case hoặc dữ liệu thực tế:

1. **Chuyển tuyến tại Trạm chung (Physical Intersection):** 
   - Thuật toán tìm bước chuyển (`OneTransferRoutingEngine`) hiện chỉ nhận diện việc chuyển tuyến nếu hai lộ trình **giao nhau tại ít nhất một mã trạm (Stop ID) trùng nhau tuyệt đối**.
   - **Chưa hỗ trợ:** Việc đi bộ giữa hai trạm khác nhau (ví dụ: Xuống trạm A, đi bộ 50m sang trạm B để lên tuyến khác) chưa được tính là một bước chuyển tuyến hợp lệ trong thuật toán này.
   - **Hệ quả:** Khi thiết kế Test Case chuyển tuyến (như L3, L4, Master), bạn phải đảm bảo có ít nhất một điểm dừng được liệt kê trong danh sách `stops_seq` của cả hai Route.

2. **Giới hạn 1 lần chuyển tuyến:**
   - Hệ thống hiện tại chỉ tìm kiếm các hành trình đi thẳng hoặc chuyển tuyến **duy nhất 1 lần**. Các hành trình phức tạp hơn (2+ lần chuyển) sẽ không được tìm thấy.
