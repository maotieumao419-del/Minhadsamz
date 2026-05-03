# Amazon Ads Automation Pipeline - Workflow Summary

Tài liệu này mô tả chi tiết toàn bộ luồng dữ liệu (Data Pipeline) và tự động hoá được xây dựng trong môi trường bằng ngôn ngữ Python (cốt lõi sử dụng thư viện xử lý tốc độ cao `Polars`).

## Tổng quan Kiến trúc

Quy trình được chia thành nhiều Giai đoạn (Phase) tuần tự để phân tách rõ ràng nhiệm vụ: Bóc tách, Chuẩn hóa, Lọc, Đối chiếu, Xử lý Điền khuyết và Xuất Excel Template.

### 1. Nền tảng (Root / Utilities)
- **Công cụ:** `read_supabase.py`
- **Mục đích:** Xây dựng cách thức kết nối trực tiếp đến **Supabase (Cơ sở dữ liệu Database Cloud)** qua Rest API để trích xuất dữ liệu danh sách SKU và tình trạng. Dữ liệu được lưu về `phase1/output/supabase_data.json`.

### 2. Phase Bổ sung (Data Extraction & Deduplication)
- **Công cụ:** `convert_multisheet.py`
- **Mục đích:** Tự động hoá việc đọc các file báo cáo Excel lớn chứa vô số sheet (như `PPC_Musemory.xlsx`). Dùng engine `calamine` để bung toàn bộ sheet ra và cắt nhỏ thành nhiều file `.json` riêng biệt (mỗi file đại diện cho 1 bảng SKU).
- **Lọc trùng:** Tự động phát hiện và loại bỏ các từ khóa bị lặp lại dựa trên `Target`, `Ghi chú`, `Match Type`, `Placement` để tránh sinh ra dữ liệu trùng lặp ở cuối nguồn gây lỗi Duplicate ID trên Amazon. Kết quả đổ vào `phase_bo_sung/output`.

### 3. Phase 0 (Data Normalization)
- **Công cụ:** `normalize_ghi_chu.py`
- **Mục đích:** Tiền xử lý dữ liệu từ Phase Bổ Sung. Sử dụng Biểu thức chính quy (Regex) để phân tích cột `Ghi chú` thô và tách ra thành các trường dữ liệu rời rạc, có cấu trúc:
  - `Match Type` (exact, phrase, broad)
  - `Bid` (Giá thầu dạng số)
  - `Placement` (Định dạng chuẩn hóa ví dụ: 30T30R30P)
- **Kết quả:** Xóa bỏ khoảng trắng, xuống dòng thừa và lưu file JSON sạch vào `phase0/output`.

### 4. Phase 1 (Filtering)
- **Công cụ:** `filter_sku.py`
- **Mục đích:** Đọc danh sách Data lấy về từ Supabase, dò tìm chỉ mục và xuất ra một mảng các mã SKU chỉ thỏa mãn điều kiện cột `'Status' == 'Tiếp nhận'`. Mảng này được xuất và lưu thành file `sku_tiep_nhan.json` chuyển giao qua Phase 2 làm nguyên liệu đầu vào.

### 5. Phase 2 (Matching & Collecting)
- **Công cụ:** `match_sku_files.py`
- **Mục đích:** Hấp thụ file mảng Json vừa tìm thấy ở trên. Xóa loại bỏ các SKU bị theo dõi trùng lặp. Nhào vào kho lưu trữ JSON chuẩn hóa của **Phase 0** để tìm và **Lôi (Copy)** chính xác những file JSON của riêng các mã SKU có trạng thái 'Tiếp nhận' này tập trung lại vào thư mục `phase2/output`.

### 6. Phase 3 (Data Completeness & Transformation)
- **Công cụ:** `process_phase3.py` & `transfer_to_phase3.py`
- **Mục đích:** 
  - Khâu đầu tiên: Chuyển nhận bàn giao cục data sang thư mục `phase3/input`.
  - Khâu cốt lõi: Triển khai các thuật toán xử lý hàng loạt để vá các khoảng trống dữ liệu `Null`:
    - **Đếm số:** Gán lại toàn bộ giá trị `STT` tịnh tiến từ 1.
    - **Vá Default:** Nhồi chữ `Keyword` vào Loại Campaign và `Chưa tạo` vào Trạng thái.
    - **Lắp ghép Logic:** Ghép nối chuỗi thành Tên Chiến Dịch (`Campaign Name`) cuối cùng với yêu cầu biến ảo tinh vi (đổi "Dấu cách" thành "Dấu gạch dưới" trong Target). Cấu trúc mẫu: `{SKU}_KT_{Match Type}_{Target}_{Placement}_{Date}`.
  - Khâu cuối: Xuất xưởng file JSON hoàn thiện 100% ra `phase3/output`.

### 7. Phase 4 (Bulk Operations Excel Generation)
- **Công cụ:** `process_phase4.py`
- **Mục đích:**
  - Nhận dữ liệu JSON hoàn thiện từ Phase 3.
  - Trích xuất `Portfolio Id` từ file `Listing.json` (nằm ở Phase Bổ sung) để gán cho từng SKU.
  - Áp dụng thuật toán **`build_7_row_block`**: Biến đổi mỗi một Keyword (JSON object) thành một khối gồm **7 dòng** chuẩn của Amazon (Campaign, 3 dòng Bidding Adjustments tách rời % Top/Product/Rest, Ad Group, Product Ad, Keyword).
  - Tự động hóa tạo file Excel `.xlsx` chuyên nghiệp bằng engine `xlsxwriter`, ép định dạng Text chống mất số. 
  - **Kết quả:** Các file Bulk Operations sẵn sàng để upload trực tiếp lên hệ thống quảng cáo của Amazon. Nằm tại `phase4/output`.

---
**Status:** `Completed`, `Verified` & `Deduplicated`.
**Tech Stack:** `Python 3`, `Polars`, `Pandas`, `Supabase-py`, `Regex`, `JSON`, `XlsxWriter`.
