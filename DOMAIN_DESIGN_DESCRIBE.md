# Mô Tả Kiến Trúc Domain (Cosmic Python & DDD)

Dự án này tuân thủ chặt chẽ mô hình **Domain-Driven Design (DDD)** và kiến trúc phân lớp theo tư tưởng của cuốn sách **Cosmic Python**. Tài liệu này giải thích chi tiết cách các Entities, Aggregates, và Domain Services tương tác với nhau trong tầng lõi (Domain Layer).

## 1. Domain Entities & Value Objects (Mô Hình Dữ Liệu)

Tầng `src/domain/model` chứa các đối tượng đại diện cho thực thể nghiệp vụ cốt lõi, hoàn toàn không phụ thuộc vào framework, database, hay các thư viện không gian (như Shapely, Geopy).

### 1.1 Hạ Tầng Mạng Lưới (Transit Elements)
- **`Point`**: Tọa độ (lat, lon) cơ bản.
- **`Stop`**: Điểm dừng xe buýt, có tọa độ và ID.
- **`Route`**: Tuyến xe buýt, chứa một danh sách các Trạm (stop_ids) và hình học tuyến (shape). `Route` cung cấp các hành vi nghiệp vụ như tính toán khoảng cách và độ vòng vèo dựa trên `IGeometryCalculator`.
- **`TransitNetwork`**: *Aggregate Root* quản lý toàn bộ cấu trúc hạ tầng. Cho phép tra cứu nhanh Tuyến và Trạm thông qua map dictionary nội bộ.

### 1.2 Nhu Cầu Di Chuyển (Demand Elements)
- **`Zone`**: Một phân vùng địa lý, có Centroid và ranh giới đa giác (Boundary) dùng để tính tỷ lệ phủ sóng và bắt chuyến.
- **`ODPair`**: Biểu diễn một lượng nhu cầu (demand) di chuyển giữa Origin Zone và Destination Zone.
- **`ODMatrix`**: *Aggregate Root* quản lý ma trận nhu cầu và hệ thống Zone.

### 1.3 Kiến Trúc Chuyến Đi (Pathfinding & Trips)
- **`Leg` / `CandidateLeg`**: Một chặng di chuyển (boarding -> alighting) trên một tuyến duy nhất.
- **`Trip`**: Chuyến đi thực tế chứa nhiều chặng `Leg`.
- **`CandidateTrip`**: Chuyến đi dự kiến (thô), chứa nhiều `CandidateLeg` trước khi được filter.
- **`EvaluatedRoutingOption`**: (V2) Ánh xạ 1-1 giữa cấu trúc thô `CandidateTrip` và phương án di chuyển đại diện tối ưu nhất `Trip`.
- **`ODRoutingResultV2`**: Kết quả bao quát nhất, chứa toàn bộ các phương án khả thi (`EvaluatedRoutingOption`) cho một `ODPair` cụ thể.

## 2. Domain Services (Xử Lý Nghiệp Vụ Chuyên Sâu)

Khi biểu diễn nghiệp vụ quá phức tạp để nhét vào một Entity đơn lẻ (ví dụ: thuật toán tìm đường, đánh giá chặng, tính toán KPI), hệ thống sử dụng các Domain Services độc lập nhưng vẫn giữ tính "thuần khiết" của Domain.

### 2.1 Spatial Service (`spatial.py`)
- Giải quyết các bài toán về mặt không gian (điểm nào gần vùng nào, tuyến nào đi qua zone). 
- Đáng chú ý là nó không tự tính toán hàm lượng giác hay bản đồ (không import Shapely) mà *giao phó (delegate)* toàn bộ logic nặng ráp cho Interface `IGeometryCalculator` (được Adapter tiêm vào ở tầng ngoài).

### 2.2 Routing Engine (`routing.py`)
- Kế thừa giao diện `AbstractRouting` và các lớp implement như `DirectConnectionRouting` (Không chuyển tuyến) và `OneTransferRoutingEngine` (1 lần chuyển tuyến).
- Chịu trách nhiệm duyệt Mạng lưới (`TransitNetwork`) để tìm ra tập hợp `CandidateTrip` khả thi nhất giữa 2 Zone O-D.

### 2.3 Trip Filter V2 (`filter_v2.py`)
- **`MinDistanceCandidateTripFilterV2`**: Thuật toán đánh giá và tự động cắt gọt 1 `CandidateTrip` rườm rà thành 1 `Trip` thực tế duy nhất. Nó quyết định trạm lên/xuống nào tốt nhất bằng cách tối ưu hóa khoảng cách đi bộ từ tâm Zone tới trạm, đồng thời đảm bảo khoảng cách di chuyển thực sự trên Route (`get_distance_between_two_stops`) là nhỏ nhất.

### 2.4 KPI Calculators (`kpi_caculator/`)
- Mở rộng tự nhiên thông qua Strategy Pattern: các class `CircuityIndexCalculator` và `TransferRateCalculator` đều tuân thủ abstract `KPICalculator`.
- Khác biệt của V2: Nhận đầu vào là `EvaluatedRoutingOption` vừa khít và sử dụng lại Mạng Mưới (tính circuity index) để trả về Score nghiệp vụ.
- (Luồng logic được xâu chuỗi nhờ Service `GenerateODRoutingResultService` chạy quy trình từ Routing -> Filter -> ODRoutingResultV2).

## 3. Interfaces & Dependency Inversion (Ports)

Điểm neo quan trọng nhất của Clean/Cosmic Python Model nằm ở `src/domain/port.py`:
- `IGeometryCalculator`: Domain không cần biết Shapely hay Geopy. Nó chỉ định nghĩa hành vi ảo như `get_distance_between(p1, p2)` hoặc `calculate_zone_coverage_ratio(zone, stops)`.
- Ở tầng *Adapters* bên ngoài (infrastructure), một class `ShapelyGeometryCalculator` sẽ hiện thực port này bằng kỹ thuật tính toán thực tế.
- **Lợi ích tối thượng**: Giúp Unit Test ở Core Domain chạy cực kỳ nhanh và nhẹ (0.2s cho toàn bộ 25 test case) bằng cách truyền một Dummy Calculator đơn giản thay vì load toàn bộ thư viện AI/GIS vào bộ nhớ.
