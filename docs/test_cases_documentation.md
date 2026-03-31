# Tài Liệu Đặc Tả Bộ Kiểm Thử Định Tuyến (Transit Network Test Suite)

Tài liệu này giải thích chi tiết mục đích và thiết kế của 10 Fake Repositories (`fake_repo_l1` tới `l5` và `fake_repo_f1` tới `f5`) đã được xây dựng để kiểm chứng các thuật toán định tuyến và lọc lộ trình.

---

## Phần 1: Các bài test định tuyến (Routing Test Suite - L1 tới L5)
Tìm kiếm và trả về **tất cả các cách đi có thể (Candidate Trips)** thông qua `CombinedRoutingEngine`.

| File | Mức độ | Mục đích kiểm tra (Routing Logic) | Đặc điểm mạng lưới |
| :--- | :--- | :--- | :--- |
| `fake_repo_l1.py` | L1 - Tối giản | Kiểm tra logic nền tảng nhất: tìm được 1 tuyến đi thẳng duy nhất nối 2 vùng. | 2 Zones, 1 Tuyến nối thẳng, 1 Cặp OD. |
| `fake_repo_l2.py` | L2 - Cạnh tranh trực tiếp | Đảm bảo thuật toán không bỏ sót các lựa chọn tuyến đi thẳng khác nhau giữa 2 vùng. | 2 Zones, 2 Tuyến nối thẳng (1 đi nhanh, 1 đi vòng xa). Trả về 2 Candidate Trips. |
| `fake_repo_l3.py` | L3 - Trung chuyển cơ bản | Kiểm tra logic ghép nối (1-transfer). Nếu không có tuyến thẳng, nó phải tìm được ngã ba ngã tư để đổi sang xe khác. | 3 Zones, 2 Tuyến đứt đoạn phải gặp nhau ở trạm Transfer (Hub). |
| `fake_repo_l4.py` | L4 - Tranh chấp Thẳng vs Chuyển | Kiểm tra tính khách quan của thuật toán: tìm ra cả tuyến đi thẳng (dù rất vòng vèo) và tuyến trung chuyển (dù phải đổi xe nhưng nhanh hơn). | 3 Zones, 1 Tuyến đi thẳng cực vòng, 2 Tuyến chuyển tiếp cực ngắn. Trả về 2 Candidate Trips. |
| `fake_repo_l5.py` | L5 - Mạng lưới tổ nhện (Web) | Gây bối rối thuật toán bằng lưới trạm xen kẽ. Thử thách Engine lùng sục ra toàn bộ các đường cong, ngách chéo, transfer hợp lý giữa nhiều vùng mà không bị lặp vô tận. | 5 Zones, 7 Tuyến cắt nhau chằng chịt, sinh ra hàng loạt tổ hợp chéo. |

---

## Phần 2: Các bài test bộ lọc (Filtering Test Suite - F1 tới F5)
Xử lý đầu ra của Routing, lọc và **chốt hạ chính xác 1 trạm lên, 1 trạm xuống, 1 trạm trung chuyển tối ưu nhất** thông qua `MinDistanceCandidateTripFilterV2`.

| File | Mức độ | Mục đích kiểm tra (Filtering Logic) | Tính năng được Focus |
| :--- | :--- | :--- | :--- |
| `fake_repo_f1.py` | F1 - Access Distance Priority | Kiểm tra thuật toán ưu tiên hàng đầu việc **đi bộ ít nhất**. Bắt buộc phải chọn trạm gần tâm vùng (Centroid) nhất trong vô số trạm của tuyến. | Tính khoảng cách Euclidean `distance_to`. |
| `fake_repo_f2.py` | F2 - Tie-Breaker Symmetry | Nhắm vào lỗi ranh giới (edge-case). Đặt các trạm đối xứng hoàn hảo quanh tâm (khoảng cách đi bộ bằng nhau tuyệt đối). Bắt thuật toán phải khởi động **tiêu chí phụ**: Chọn trạm giúp *ngồi trên xe bus ngắn nhất*. (Đã fix lỗi dấu phẩy động ở case này). | Logic `score == min_access_score` kèm dung sai `1e-4`. |
| `fake_repo_f3.py` | F3 - Transfer Optimization | Ép bộ lọc phân tích trạm trung chuyển. Nếu 2 tuyến giao nhau ở nhiều trạm, nó phải chọn trạm chuyển giúp **tổng quãng đường ngồi trên 2 xe** là nhỏ nhất (tránh bị chở đi vòng). | Logic tối ưu hóa mảng `transfer_stop_ids`. |
| `fake_repo_f4.py` | F4 - Access vs Travel Priority | Xác minh ưu tiên việc đi bộ ngắn nhất ngay cả khi phải ngồi xe bus lâu hơn (Đánh đổi quãng đường). | Kiểm chứng việc chọn trạm gần tâm O/D bất kể khoảng cách giữa các trạm trên tuyến. |
| `fake_repo_f6.py` | F6 - Transfer Symmetry Tie-Breaker | Áp dụng logic lọc tie-breaker của 0-transfer lên trip 1-transfer. Khi các trạm Lên/Xuống cách đều tâm (hòa access distance), bắt buộc duyệt mọi tổ hợp (board, transfer, alight) để chọn cụm có tổng quãng đường xe chạy (route distance) tối ưu nhất thay vì chọn ngẫu nhiên. | Logic duyệt tổ hợp bộ 3 trạm `(b_id, t_id, a_id)` để tìm `min_route_dist`. |
| `fake_repo_f5.py` | F5 - Multi-Dimensional Mesh | Mức độ "ác liệt" nhất. Quăng mạng lưới chi chít với 27 tổ hợp trạm (Lên - Xuống - Chuyển). Cài một bẫy lộ trình (Detour 1000m). Buộc thuật toán tìm ra "Kim chỉ nam" duy nhất sau nhiều bước duyệt ma trận tuyến. | Tích hợp toàn bộ mọi logic tìm khoảng cách tối thiểu từ A tới Z. |

---

## Phần 3: Đề Xuất Test Case Khủng (FakeRepo_Master)
Trong tương lai, để đem hệ thống này vào thực tế (mức Production), chúng ta thiếu một bài test hỗn hợp. Dưới đây là đề xuất xây dựng **`fake_repo_master.py`** – một sa bàn mô phỏng môi trường thế giới thực.

### Mô hình "Mini Smart City" giả lập:
1. **Quy mô lớn (Scale):**
   - **15+ Zones** đan xen (Có những Zone bị đè lên nhau - Overlapping, đại diện cho việc chia phân khu hành chính phức tạp).
   - **10+ Routes** với các đặc điểm thực tế:
      - *Trunk lines (Tuyến trục)*: Chạy xuyên tâm thành phố, trạm thưa, khoảng cách giữa các trạm cực dài (nhanh).
      - *Feeder lines (Tuyến gom)*: Chạy rề rà vòng vèo quanh khu dân cư ngoại ô, thả khách ở điểm có Trunk line.
      - *Circular loop (Tuyến vòng)*: Chạy xoay tròn quanh trung tâm thương mại.
   - **50+ Stops** điểm dừng rải rác.
2. **Kịch bản OD Matrix Đa Chiều (Complex Scenarios):**
   Khởi tạo một lượng lớn `OD_Pairs` (ví dụ 10-20 cặp) để đánh giá nhiều góc độ cùng lúc:
   - **Kịch bản 1:** Đi từ ngoại ô vào lõi tâm (Bắt buộc phải xài Feeder -> Trunk. Nếu thuật toán khôn phải biết chọn Trunk thay vì đi Feeder đến hết đường rùa bò).
   - **Kịch bản 2:** Hai vùng cạnh nhau cách 200m (Thuật toán có filter out không? Hay vẫn ép khách đi vòng 3km tiền bus?).
   - **Kịch bản 3:** Từ Bắc xuống Nam (Phải chuyển tuyến 2 lần: Feeder -> Trunk -> Feeder). *Lưu ý: System hiện chỉ support 1-transfer, nếu nhét case 2-transfer vào nó phải trả về danh sách rỗng, hoặc nâng cấp code để xử lý.*
   - **Kịch bản 4:** Tuyến đi thẳng mất 3 tiếng đi vòng quanh thành phố, còn tuyến 1-transfer cắt ngang thành phố mất 30 phút. Thuật toán có tính ra đúng KPI Transfer Rate hay Circuity Index bị phạt nặng đối với tuyến đi thẳng không?

### Giá trị của Master Case:
- **Stress-Test (Kiểm tra tải):** Chạy hàm `kpi_calculator.py` cho toàn bộ ma trận này xem có bị Timeout hoặc tràn RAM không.
- **Tích hợp liền mạch (Integration):** Kiểm chứng luồng chảy dữ liệu từ Repository -> Routing Engine -> Filtering -> Data Dumper một cách hoàn chỉnh.
