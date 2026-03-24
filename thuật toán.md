# Tài liệu Tổng quan Thuật toán và Logic Hệ thống Đánh giá Mạng lưới Xe buýt

Tài liệu này trình bày các ý tưởng, thuật toán và luồng logic cốt lõi được sử dụng để đánh giá mạng lưới xe buýt dựa trên dữ liệu nhu cầu đi lại (Ma trận O-D). Tài liệu tập trung vào mặt ý tưởng khái quát để làm tài liệu tham khảo hoặc chuyển giao cho các hệ thống AI khác.

## 1. Bài toán Tìm Đường (Routing Algorithms)
Mục tiêu là tìm ra các lộ trình khả thi cho hành khách đi từ một Vùng xuất phát (Origin Zone) đến một Vùng đích (Destination Zone) trên mạng lưới xe buýt. Hệ thống giải quyết theo hai trường hợp: đi thẳng và chuyển tuyến 1 lần.

### 1.1. Luồng đi thẳng (0-Transfer)
Ý tưởng là tìm những lộ trình mà hành khách có thể lên xe tĩnh tại một trạm ở Vùng xuất phát và xuống xe thẳng tại một trạm ở Vùng đích trên cùng một tuyến xe buýt.
**Thuật toán:**
1. Lấy danh sách tất cả các tuyến xe buýt có đi ngang qua Vùng xuất phát và Vùng đích.
2. Tìm kiếm phần giao của hai danh sách để ra được các "tuyến chung" đi qua cả hai vùng.
3. Đối với mỗi tuyến chung, xác định danh sách các trạm nằm trong Vùng xuất phát (trạm lên) và trạm nằm trong Vùng đích (trạm xuống).
4. Áp dụng điều kiện thứ tự: Trạm lên phải nằm TRƯỚC trạm xuống trên hành trình di chuyển của tuyến xe buýt đó. (Việc kiểm tra này sử dụng cấu trúc lập chỉ mục thứ tự trạm để so sánh độ ưu tiên nhanh chóng).
5. Nếu thỏa mãn, ghi nhận đây là lộ trình khả thi để hành khách đi thẳng một mạch.

### 1.2. Luồng đổi xe (1-Transfer)
Ý tưởng là tìm những lộ trình cần đổi xe đúng 1 lần. Hành khách lên xe tuyến A ở Vùng xuất phát, sau đó đổi sang tuyến B tại một trạm giao cắt ở giữa, và đi tiếp tuyến B tới Vùng đích.
**Thuật toán:**
1. Thu thập danh sách Tuyến 1 (đi qua Vùng xuất phát) và Tuyến 2 (đi qua Vùng đích). Loại bỏ các tuyến có thể đi thẳng ra khỏi hai nhóm này.
2. Với mỗi cặp (Tuyến 1, Tuyến 2), tìm ra tập hợp các "Trạm chung" làm trạm trung chuyển (transfer stops).
3. Kiểm tra tính hợp lệ về chiều di chuyển trên Tuyến 1: Trạm lên (ở Vùng xuất phát) phải được tuyến đi ngang qua TRƯỚC KHI tới Trạm trung chuyển.
4. Kiểm tra tính hợp lệ về chiều di chuyển trên Tuyến 2: Trạm trung chuyển phải được đi ngang qua TRƯỚC KHI tuyến đó tới Trạm xuống (ở Vùng đích).
5. Khi bộ ba (Trạm lên, Trạm trung chuyển, Trạm xuống) cùng thỏa mãn các điều kiện chiều đi của hai tuyến tương ứng, một hành trình 1 lần đổi xe sẽ được thiết lập thành công.

## 2. Lọc và Chọn Trạm Tối Ưu (Filtering Strategy)
Giữa hai Vùng Xuất phát và Đích có thể có nhiều trạm để người dân lên/xuống xe. Hệ thống cần chọn ra chỉ một lộ trình với các trạm có "khoảng cách đi bộ và di chuyển tối ưu nhất".

### 2.1. Tối ưu cho đi thẳng (0-transfer)
- **Lọc trạm lên**: Trong tập hợp các trạm lên khả thi, chọn trạm có khoảng cách đường chim bay (Euclidean distance) gần nhất với Trọng tâm (Centroid) của Vùng xuất phát.
- **Lọc trạm xuống**: Tương tự, chọn bến có khoảng cách đường chim bay gần nhất tới Trọng tâm của Vùng đích.

### 2.2. Tối ưu cho đổi xe (1-transfer)
- Lọc trạm lên và trạm xuống: Cách tiếp cận dùng Trọng tâm tương tự như trường hợp đi thẳng.
- **Lọc trạm trung chuyển tối ưu**: Nếu có nhiều trạm giao cắt giữa Tuyến 1 và Tuyến 2, hệ thống sẽ chọn trạm sao cho **tốc độ di chuyển tổng thể là hài hòa nhất**. Cụ thể bằng cách lấy Trạm tối thiểu hóa được **tổng** khoảng cách trực tiếp từ nó nhìn về hai Trọng tâm (Vùng xuất phát và Vùng đích).

## 3. Tính toán Hình học và Không gian (Spatial Operations)

### 3.1. Phép Giao cắt Tuyến và Vùng (Intersection)
- Để máy định vị được tuyến xe có đi ngang Vùng (Zone) hay không, hệ thống áp dụng phép toán kiểm tra sự bao hàm không gian hình học đa giác (Polygon containment). Thuật toán này xét tọa độ điểm (Point) của trạm có nằm lọt vào bên trong Đa giác ranh giới của Vùng đó hay không.

### 3.2. Đo Lường Diện tích Vùng phủ (Spatial Coverage)
- **Chuẩn hóa Tọa độ (Map Projection)**: Để diện tích đầu ra đúng đơn vị hệ mét, các tọa độ địa lý cầu vòng cung (Lat/Lon) được ánh xạ lên một mặt phẳng ảo cục bộ thông qua công thức lượng giác, lấy Trọng tâm Vùng làm gốc. Điều này triệt tiêu tình trạng sai số méo mó diện tích do độ cong bề mặt Trái Đất.
- **Thuật toán Độ Phủ (Coverage Area Computation)**:
  1. Dựng một "Vòng tròn đệm" (Buffer) có bán kính quét cố định (ví dụ: 500 mét) xung quanh mọi trạm xe buýt.
  2. Gộp nối tập hợp các vòng tròn đệm của cụm nhóm trạm này lại thành 1 Mảng khối địa hình duy nhất (Union Polygon).
  3. Lấy phần giao cắt (Intersection) giữa KHỐI ĐỊA HÌNH BAO TRẠM và ĐA GIÁC ĐỊA BÀN VÙNG (Zone Polygon).
  4. Lấy Diện tích của Khối Bị Giao Cắt chia cho Diện tích Tổng hợp của Đa giác Vùng sẽ ra được "Tỷ lệ Không gian Được Phủ".

## 4. Đặc tả Tính các Chỉ số Hiệu năng (KPIs Calculation)
Lộ trình thực sẽ được đưa vào chấm điểm qua ba KPI cơ bản minh họa chất lượng Dịch vụ Hành khách:

1. **Transfer Rate (Tỷ lệ chuyển tuyến/Số lần đổi xe)**: Chấm điểm dựa trên tính chất hành trình mất 0 hay 1 lần đổi xe qua module Routing.
2. **Circuity Index (Chỉ số vòng vèo)**: Đo lường mức độ lắt léo, kém trực tiếp của chuyến đi thực tế vì phụ thuộc vào lộ trình ngoằn ngoèo của đường nội đô. 
    - *Công thức:* `(Tổng độ dài quãng đường lăn bánh theo từng đoạn trạm dừng)` / `(Khoảng cách đường chim bay đi trực tiếp từ Trạm Đầu lộ trình đến Trạm Cuối lộ trình)`. Tỷ lệ càng sát mức 1.0 nghĩa là xe chạy càng thẳng tắp và người dân càng đỡ phí thời gian.
3. **Spatial Coverage KPI (Độ bao phủ Không gian)**: Biểu diễn khả năng xe buýt tiếp cận và lan tỏa rộng ở phần đầu-cuối chuyến. Chấm điểm bằng cách nhân Tỷ lệ Vùng phủ (tính ở mục 3) của Vùng Xuất phát với Tỷ lệ Vùng phủ của Vùng Đích.

## 5. Luồng Thực Thi Tổng Thể (Main Pipeline)
Quá trình phân tích hệ thống trải qua chu trình sau:
1. **Truy xuất dữ liệu (Data Loading)**: Nạp vào hệ thống mạng lưới cơ sở hạ tầng (Các Trạm, Các Tuyến, Các Khu Vực) và Nhu cầu (Luồng đi lại của hành khách bằng Ma Trận gốc-đích O-D).
2. **Tìm đường đa kịch bản (Preprocessing/Routing)**: Với mỗi Cặp Tọa Độ Cần Đi Lại, hệ thống quét cả giải pháp Đổi xe 1 Lần và Không Đổi Xe, sau đó vận dụng Thuật Toán Màng lọc (Filtering) để quyết định được Lộ Trình/Trạm Giao Cắt là Tốt nhất trong trường hợp dồi dào giải pháp.
3. **Tổng hợp Hệ mét và Xuất báo cáo (KPI Evaluation)**: Ốp các Thuật toán KPI vào hệ các Lộ Trình xuất sắc lọt qua bộ lọc trên. Kết hợp chéo các điểm thành Bảng KPI Tổng (định dạng JSON).
