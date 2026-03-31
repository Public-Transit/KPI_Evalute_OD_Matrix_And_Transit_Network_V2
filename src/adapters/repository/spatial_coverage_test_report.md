# Báo Cáo Kiểm Thử Spatial Coverage

## Tóm Tắt

Tài liệu này mô tả các mạng kiểm thử đơn giản và các trường hợp xác thực đã được bổ
sung để kiểm tra tính đúng đắn của
`src/domain/service/kpi_caculator/spatial_coverage_kpi.py`.

Phạm vi được chốt cho bộ kiểm thử này:

- Chỉ sử dụng các stop nằm bên trong vùng OD để kiểm tra spatial coverage.
- Không có test case nào sử dụng stop nằm ngoài origin zone hoặc destination zone.
- "Boundary clipping" được hiểu là stop vẫn nằm trong zone, nhưng vùng phủ buffer của
  stop vượt ra ngoài polygon của zone nên phần vượt ra ngoài phải bị loại bỏ trước
  khi tính diện tích.

## Thực Thi Kiểm Thử

Các lệnh đã chạy:

1. `.\\.venv\\Scripts\\python.exe -m pytest tests/domain/service/kpi_caculator/test_spatial_coverage_kpi.py -q -p no:cacheprovider`
2. `.\\.venv\\Scripts\\python.exe -m pytest tests/domain/service/kpi_caculator/test_spatial_coverage_kpi_repo_cases.py -q -p no:cacheprovider`
3. `.\\.venv\\Scripts\\python.exe -m pytest tests/domain/service/kpi_caculator -q -p no:cacheprovider`

Kết quả quan sát được:

- Bộ test spatial coverage hiện có: `3 passed`
- Bộ test spatial coverage mới dùng fake repo: `5 passed`
- Toàn bộ test trong nhóm KPI calculator: `10 passed`

## Các Trường Hợp Kiểm Thử

### SC1 - Stop ở giữa zone cho ra tỷ lệ phủ một phần như kỳ vọng

- Repository: `FakeRepoSC1`
- Cấu trúc mạng:
  - `Z1` và `Z2` là hai hình chữ nhật đơn giản có cùng kích thước.
  - `S1_CENTER` và `S2_CENTER` nằm tại centroid của từng zone.
- Input:
  - Candidate trip gồm một leg `R1`
  - Boarding stops: `{"S1_CENTER"}`
  - Alighting stops: `{"S2_CENTER"}`
  - `radius_m = 50`
- Hành vi kỳ vọng:
  - Coverage của origin và destination đều dương và đối xứng.
  - `score_ratio = origin_coverage_ratio * destination_coverage_ratio`.
- Kết quả thực tế:
  - `origin_coverage_ratio = 0.16982907741291478`
  - `destination_coverage_ratio = 0.16982907741291478`
  - `score_ratio = 0.0288419155349218`
  - `origin_stop_count = 1`
  - `destination_stop_count = 1`
- Trạng thái: PASS

### SC1 - Bán kính lớn làm coverage được chặn ở 1

- Repository: `FakeRepoSC1`
- Input:
  - Cùng mạng và cùng candidate trip như SC1
  - `radius_m = 170`
- Hành vi kỳ vọng:
  - Mỗi zone được phủ kín bởi buffer của stop.
  - Coverage ratio được chặn ở `1.0`.
- Kết quả thực tế:
  - `origin_coverage_ratio = 1.0`
  - `destination_coverage_ratio = 1.0`
  - `score_ratio = 1.0`
- Trạng thái: PASS

### SC2 - Stop nằm trong zone nhưng gần biên bị cắt bởi biên zone

- Repository: `FakeRepoSC2`
- Cấu trúc mạng:
  - `S1_EDGE` vẫn nằm trong `Z1`, nhưng ở gần biên của zone.
  - `S2_CENTER` nằm gần tâm của `Z2`.
- Input:
  - Kiểm tra geometry coverage trên `Z1`
  - `radius_m = 50`
- Hành vi kỳ vọng:
  - Coverage vẫn dương vì stop nằm trong zone.
  - Coverage nhỏ hơn case stop ở gần tâm vì một phần buffer nằm ngoài polygon của
    zone và phải bị loại bỏ.
- Kết quả thực tế:
  - `edge_ratio = 0.1314002742228597`
  - Giá trị tham chiếu của case centered = `0.16982907741291478`
  - Quan hệ được xác nhận: `0 < edge_ratio < centered_ratio`
- Trạng thái: PASS

### SC3 - Buffer chồng nhau hoặc trùng nhau không bị tính hai lần

- Repository: `FakeRepoSC3`
- Cấu trúc mạng:
  - `S1_CENTER` và `S1_DUPLICATE` có cùng tọa độ.
  - `S1_NEAR` vẫn nằm trong cùng zone và có buffer chồng lên buffer đầu tiên.
- Input:
  - Kiểm tra geometry coverage trên `Z1`
  - `radius_m = 50`
- Hành vi kỳ vọng:
  - Stop trùng nhau không được làm tăng diện tích phủ.
  - Stop ở gần có thể làm tăng diện tích phủ, nhưng chỉ theo phần hợp của hai vùng
    buffer chồng nhau.
- Kết quả thực tế:
  - Tỷ lệ phủ với một stop = `0.16982907741291478`
  - Tỷ lệ phủ với stop trùng tọa độ = `0.1698290774129148`
  - Tỷ lệ phủ với stop gần và chồng buffer = `0.2175569835770958`
  - Quan hệ được xác nhận: `single < nearby < single * 2`
- Trạng thái: PASS

### SC4 - Spatial KPI chỉ dùng leg đầu và leg cuối của candidate trip

- Repository: `FakeRepoSC4`
- Cấu trúc mạng:
  - Candidate trip có 3 leg.
  - Stop boarding của leg đầu là `S1_EDGE`.
  - Stop alighting của leg cuối là `S2_EDGE`.
  - Leg giữa chứa `S1_NOISE` và `S2_NOISE`, là các stop có thể làm tăng coverage nếu
    bị tính nhầm.
- Input:
  - Candidate trip:
    - `R1`: boarding `{"S1_EDGE"}`, alighting `{"H1"}`
    - `R2`: boarding `{"S1_NOISE"}`, alighting `{"S2_NOISE"}`
    - `R3`: boarding `{"H2"}`, alighting `{"S2_EDGE"}`
  - `radius_m = 50`
- Hành vi kỳ vọng:
  - Origin coverage chỉ dùng boarding stops của leg đầu.
  - Destination coverage chỉ dùng alighting stops của leg cuối.
  - Các stop gây nhiễu ở leg giữa không được ảnh hưởng tới coverage và stop count.
- Kết quả thực tế:
  - `origin_coverage_ratio = 0.1314002742228597`
  - `destination_coverage_ratio = 0.1314002742228597`
  - `score_ratio = 0.017266032065842724`
  - `origin_stop_count = 1`
  - `destination_stop_count = 1`
- Trạng thái: PASS

## Ghi Chú

- Các assertion số học dùng `pytest.approx` vì phép tính diện tích của Shapely dựa
  trên số thực dấu phẩy động.
- Bộ test này cố ý không kiểm tra stop nằm ngoài vùng OD, vì điều đó không phù hợp
  với cách `EvaluatedRoutingOption -> candidate_trip` hiện đang được dùng cho spatial
  coverage trong dự án này.
