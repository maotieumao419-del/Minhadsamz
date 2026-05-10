# Giải thích Toàn bộ Luồng chạy Dự án Test 4 (Bình dân học vụ)

Hãy tưởng tượng bạn đang vận hành một cỗ máy tự động hóa khổng lồ để quản lý hàng nghìn từ khóa quảng cáo (Ads) trên Amazon. Thay vì phải làm bằng tay cực khổ, cỗ máy "Test 4" này chia công việc ra làm 6 phân xưởng (Phase) y như một nhà máy thực thụ:

---

### 🏭 Phase Bổ Sung & Phase 0: "Màng lọc rác" (Khu nhập liệu)
*   **Thực trạng:** Bạn tải file báo cáo từ Amazon về, và bạn cũng có file Excel tự theo dõi ở nhà. Hai file này chữ hoa chữ thường lộn xộn, tên cột viết khác nhau.
*   **Máy làm gì:** Phase 0 giống như một cái màng lọc. Nó hút tất cả các loại file lộn xộn này vào, gọt giũa lại tên cột, xóa khoảng trắng thừa, và "ép" tất cả thành một chuẩn định dạng duy nhất (JSON). 
*   **Ý nghĩa:** Nhờ màng lọc này, phần lõi nhà máy bên trong không bao giờ bị "kẹt bánh răng" vì dữ liệu rác.

### 🏭 Phase 1: "Máy phân loại Vòng đời" (Khu phân loại)
*   **Thực trạng:** Có từ khóa mới chạy (cần đốt tiền mua data), có từ khóa chạy lâu rồi (cần vắt sữa lấy lãi), có từ khóa chỉ chạy vào dịp Lễ Tết (Giáng sinh, Valentine...). Không thể áp chung một luật được.
*   **Máy làm gì:** Dựa vào tên Campaign và Ngày tạo, máy sẽ dán nhãn cho từng từ khóa:
    *   **Evergreen (Quanh năm):** Phân thành 4 rổ -> `Launch` (Mới ra), `Growth` (Đang lớn), `Mature` (Trưởng thành), `Dormant` (Ngủ đông).
    *   **Seasonal (Mùa vụ):** Phân thành 3 rổ -> `Pre-season` (Trước lễ), `Peak-season` (Đúng lễ), `Post-season` (Sau lễ).

### 🏭 Phase 2: "Kế toán trưởng" (Khu tổng hợp sổ sách)
*   **Máy làm gì:** Nó đi nhặt số liệu biểu diễn (Click, Order, ACOS, Doanh thu, Chi phí...) ghép nối vào từng từ khóa đã được phân rổ ở Phase 1. Lúc này, mỗi từ khóa đều có một "hồ sơ năng lực" đầy đủ.

### 🏭 Phase 3: "Trợ lý Phân tích AI" (Khu đưa ra Đề xuất)
*   **Thực trạng:** Đã có hồ sơ rồi, giờ cần ai đó phán xét xem từ khóa này đang Tốt hay Xấu để tăng/giảm tiền (Bid).
*   **Máy làm gì:** Hệ thống được nạp một bộ "Luật" (Rule_Engine) và "Rào chắn" (Guardrails) cực kỳ khắt khe cho từng giai đoạn.
    *   Trợ lý đọc hồ sơ: *"À, từ khóa này bị 15 click 0 đơn (Lỗ nặng). Đề xuất TẮT (Pause)."*
    *   Trợ lý đọc hồ sơ khác: *"Từ này ACOS 15% (Quá lời). Đề xuất TĂNG GIÁ 20%."*
    *   **Cơ chế dán nhãn:** Nếu thay đổi là nhỏ và an toàn, Trợ lý dán mác **`AUTO_APPROVED`** (Tự động duyệt). Nếu thay đổi quá lớn (ví dụ đòi tăng giá lên tận $3.0 vượt nóc), Trợ lý sẽ dán mác **`REQUIRES_REVIEW`** (Cờ đỏ, nhờ Sếp duyệt).

### 🏭 Phase 4: "Bàn làm việc của Sếp" (Khu duyệt Excel - HITL)
*   **Thực trạng:** Bạn không có thời gian đọc 1000 từ khóa mỗi ngày.
*   **Máy làm gì:** Nó thu gom TẤT CẢ những từ khóa bị dán cờ đỏ `REQUIRES_REVIEW` (thường chỉ chiếm 1-2% tổng số), xuất ra một file Excel vô cùng đẹp mắt tên là `Action_Required_Dashboard.xlsx`.
*   **Nhiệm vụ của bạn:** Mỗi sáng nhâm nhi ly cafe, mở file Excel này ra, lướt nhanh 10 dòng và phán xử: Dòng nào đồng ý thì để im, dòng nào từ chối thì gõ `REJECT`, dòng nào muốn tự ép giá thì gõ số vào.

### 🏭 Phase 5: "Thư ký chốt sổ" (Khu đóng gói gửi Amazon)
*   **Máy làm gì:** Khi bạn đã duyệt xong Excel, Thư ký sẽ gộp 98% quyết định tự động của Máy (Auto) và 2% quyết định của Bạn (từ file Excel) thành một khối.
*   **Cắt gọt:** Nó vứt hết các cột báo cáo nháp, chỉ giữ lại đúng 8 cột bắt buộc của Amazon (hoặc đầy đủ 30 cột tùy cấu hình), tạo ra file `Amazon_Upload_Ready.xlsx`.

### 🏭 Phase 6: "Hải quan kiểm duyệt" (Khu xác thực ID & Format)
*   **Thực trạng:** Bạn lo lắng nếu file Phase 5 bị nhầm lẫn ID thì khi upload lên Amazon sẽ gây lỗi hàng loạt.
*   **Máy làm gì:** Đây là chốt chặn cuối cùng. Nó cầm file của Phase 5 đối chiếu ngược lại với dữ liệu gốc ban đầu ở Phase Bổ Sung.
    *   Nếu phát hiện một dòng bị sai ID hoặc sai định dạng, nó sẽ **đá văng** dòng đó ra một file lỗi riêng (`Validation_Errors.xlsx`) để bạn sửa tay.
    *   Chỉ những dòng hoàn toàn sạch sẽ và chính xác mới được đưa vào file `Amazon_Upload_Verified.xlsx`.
*   **Hoàn thành:** Bạn chỉ việc cầm file đã qua kiểm duyệt ở Phase 6 này upload lên Seller Central là yên tâm 100%!
