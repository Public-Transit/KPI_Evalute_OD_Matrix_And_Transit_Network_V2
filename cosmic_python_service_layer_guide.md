# Cosmic Python Service Layer Guide

Tài liệu này giải thích cách áp dụng kiến trúc chuẩn của "Cosmic Python" (Architecture Patterns with Python) vào bài toán định tuyến và tính KPI mạng lưới giao thông công cộng.

## 1. Phân biệt Entrypoints và Service Layer

Lỗi phổ biến nhất khi áp dụng DDD là code thẳng logic nghiệp vụ vào chỗ nhận API (ví dụ như gọi thẳng Database và thay đổi Entity ở hàm `def main()` hoặc `@app.get("/")`).

**Trong Cosmic Python, chúng ta chia làm 2 lớp:**

### A. Entrypoints (Lớp giao tiếp ngoài) - `src/entrypoints/`
*   **Ví dụ:** `main.py` (CLI), `api.py` (FastAPI).
*   **Nhiệm vụ:** 
    *   Trò chuyện với thế giới bên ngoài (nhận HTTP Request, đọc params).
    *   Khởi tạo các class cơ sở hạ tầng (Database Repositories, Unit Of Work).
    *   Gọi hàm ở **Application Service** và truyền biến vào.
    *   Lấy kết quả từ Service, ép kiểu thành JSON và trả về cho User.
*   **KHÔNG ĐƯỢC:** Tự tay chạy câu lệnh SQL, hoặc tự gọi `route.__update_shape()`.

### B. Application Service (Lớp Case Sử Dụng) - `src/service_layer/service/`
*   **Ví dụ:** `routing_services.py`
*   **Nhiệm vụ:**
    *   Đại diện cho các **Use Case** thực tế của người dùng (Ví dụ: `batch_route_all_od_pairs`, `preview_route_change`, `commit_route_change`).
    *   Nhận `UnitOfWork` từ Entrypoint. 
    *   Mở `with uow:` để bắt đầu một Transaction.
    *   Bảo UoW lấy Entity lên (`uow.transit_network_repo.get(...)`).
    *   Gọi **Domain Service** (như `routing_engine.find(...)`) hoặc gọi method quản lý state của Entity.
    *   Gọi `__uow.commit()__` nếu muốn lưu thay đổi.

## 2. Unit of Work (UoW) - Chìa khoá của Cosmic Python

Bạn sẽ gặp pattern này ở `src/service_layer/unit_of_work.py`.
Tại sao lại cần nó?
Mỗi khi bạn muốn làm một tác vụ: Lấy `Route` từ DB -> Tính toán xem nếu đổi Tuyến này thì các `ODPair` bị tác động thế nào -> Quyết định có lưu hay không.
Nếu code bình thường, bạn mở connection DB -> thao tác -> đôi khi quên đóng, hoặc bị lỗi giữa chừng làm rác DB.

**UoW giải quyết bằng cách:**
*   Dùng `with uow:` -> Mở transaction DB.
*   Mọi API tới DB trong khối `with` này đều dùng chung 1 connection.
*   Nếu không có lệnh `uow.commit()` ở dòng cuối -> **Toàn bộ thay đổi sẽ bị vứt đi (Rollback)**.
*   **Ứng dụng tuyệt vời cho tính năng Preview (service_change_transit_network):** Người dùng muốn xem trước điểm KPIs khi thay 1 bến bus. Service chỉ cần đổi Data in-memory, gọi logic của Domain -> Tính toán trả kết quả ra Entrypoint. Do ta **không gọi** `uow.commit()`, database tự động bỏ qua thay đổi đó.

## 3. Tóm tắt luồng thực thi trong code giả

1. Client gọi **API `/preview-route/ROUTE123`**
2. **Entrypoint** `api_preview_change_route` nhận Request. Nó tạo `DummyUnitOfWork` và gọi Service `calculate_impact_of_route_change`.
3. **Application Service** dùng `with uow` -> kéo Route thật từ DB. Cập nhật bến `update_stops()` trên object in-memory.
4. **Application Service** gọi **Domain Service** `routing_engine` để định tuyến trên mạng lưới mới.
5. Service kết thúc hàm (Không gọi commit), trả `ODRoutingResult` list về cho Entrypoint.
6. **Entrypoint** biến list đó thành JSON trả cho User.
7. Khi User thấy điểm KPI cao, bấm Save. Lần này API `/confirm-route` chạy hàm **Application Service** `change_route_shape`. Ở đây có `uow.commit()`, dữ liệu được lưu thật sự vào DB.
