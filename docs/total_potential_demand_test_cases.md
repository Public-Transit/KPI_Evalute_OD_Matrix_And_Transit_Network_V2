# Tài liệu mô tả các Test Case Đánh giá Nhu cầu Tiềm năng (Total Potential Demand)

Tài liệu này chi tiết hóa 5 kịch bản kiểm thử nhằm xác minh tính chính xác của thuật toán đo lường mức độ đóng góp của một Chuyến xe (Trip) đối với nhu cầu di chuyển của các cặp OD (Candidate Trips).

---

### Test 1: Nhu cầu OD giao với biên Trip
* **Mục tiêu:** Kiểm tra khả năng ghi nhận Demand khi lộ trình hành khách (Candidate Trip) chỉ giao tiếp với Trip đánh giá tại đúng điểm biên (điểm đầu/cuối).
* **Kịch bản:**
  - **Hành khách (Candidate Trip):** Đi từ Vùng Z1 đến Vùng Z3 (Lộ trình S1 → S7).
  - **Chuyến xe đánh giá (Trip):** 
    - Trip 1: Chạy đoạn S7 → S10 trên Tuyến R1 (Chỉ chạm Candidate tại S7).
    - Trip 2: Chuyển tuyến S2 → S5 (R1) rồi S5 → S18 (R2).
* **Kết quả mong muốn:** Hệ thống xác định điểm giao duy nhất là S5 hoặc S7. Vì không có quãng đường chung (segment overlap) thực sự đáng kể trên cùng một tuyến, Demand được tính toán chính xác (thường là 0 lưu lượng được phục vụ hoặc chỉ phục vụ tại điểm dừng đơn lẻ).
* **Kết quả thực tế:** [OK]

---

### Test 2: Nhu cầu OD giao một phần với Trip
* **Mục tiêu:** Kiểm tra khả năng tìm kiếm và ghi nhận phần lộ trình trùng nhau (partial overlap segment) giữa khách và chuyến xe.
* **Kịch bản:**
  - **Hành khách (Candidate Trip):** Đi từ Vùng Z2 đến Vùng Z3 (Lộ trình S3 → S7).
  - **Chuyến xe đánh giá (Trip):**
    - Trip 1: Chạy đoạn S5 → S9 trên R1.
    - Trip 2: Chuyển tuyến R2 (S12 → S5) sau đó R1 (S5 → S10).
* **Kết quả mong muốn:** Hệ thống phải nhận diện được đoạn chung là S5 → S7 trên Tuyến R1. Toàn bộ nhu cầu của cặp OD này sẽ được tính cho phần năng lực phục vụ của Trip trên đoạn chung đó.
* **Kết quả thực tế:** [OK]

---

### Test 3: Nhu cầu OD nằm hoàn toàn trong Trip
* **Mục tiêu:** Kiểm tra bài toán Trip đánh giá bao phủ toàn bộ lộ trình khách hàng cần đi.
* **Kịch bản:**
  - **Hành khách (Candidate Trip):** Đi từ Vùng Z3 đến Vùng Z4 (Lộ trình S6 → S9).
  - **Chuyến xe đánh giá (Trip):**
    - Trip 1: Chạy suốt chặng dài S4 → S10 trên R1.
    - Trip 2: Chạy R2 (S11 → S5) sau đó R1 (S5 → S10).
* **Kết quả mong muốn:** Hệ thống ghi nhận Trip đáp ứng 100% nhu cầu của OD này vì đoạn S6 → S9 nằm gọn trong hành trình của chuyến xe.
* **Kết quả thực tế:** [OK]

---

### Test 4: Nhu cầu OD bao trùm hết Trip
* **Mục tiêu:** Xác minh trường hợp Trip đánh giá quá ngắn so với hành trình dài của khách hàng.
* **Kịch bản:**
  - **Hành khách (Candidate Trip):** Đi xuyên suốt từ Vùng Z1 đến Vùng Z4 (Lộ trình S1 → S10).
  - **Chuyến xe đánh giá (Trip):**
    - Trip 1: Chỉ chạy đoạn ngắn S4 → S7 trên R1.
    - Trip 2: Chạy R1 (S3 → S5) rồi rẽ sang R2 (S5 → S16).
* **Kết quả mong muốn:** Hệ thống xác định Trip chỉ đóng góp một phần công sức phục vụ OD (đoạn S4 → S7 hoặc S3 → S5). Demand của OD vẫn được ghi nhận dưới dạng phục vụ một chặng nối.
* **Kết quả thực tế:** [OK]

---

### Test 5: Candidate Trip dùng 1 đoạn trong Trip rồi rẽ sang Route khác
* **Mục tiêu:** Kiểm tra bài toán phức tạp khi khách hàng phải chuyển tuyến, và Trip đánh giá chỉ hỗ trợ được chặng đầu/giữa của khách trước khi khách rẽ hướng.
* **Kịch bản:**
  - **Hành khách (Candidate Trip):** Đi từ Z1 đến Z8. Sử dụng R1 (S1 → S8) làm chặng đầu, sau đó trung chuyển sang R3 (S8 → S28) để tới đích.
  - **Chuyến xe đánh giá (Trip):**
    - Trip 1: Chạy trên R1 đoạn S3 → S9.
    - Trip 2: Chạy R2 (S12 → S5) sau đó nối sang R1 (S5 → S10).
* **Kết quả mong muốn:** Hệ thống phải phân tách được lộ trình Candidate chặng 1 (R1) giao với Trip đang xét tại đoạn S3 → S8 (với Trip 1) hoặc S5 → S8 (với Trip 2). Phần lộ trình khách đi trên Tuyến R3 sẽ không được tính vì không liên quan đến Trip đang đánh giá.
* **Kết quả thực tế:** [OK]
