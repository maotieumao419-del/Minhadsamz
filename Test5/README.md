# Test 5: Amazon Ads UI Dashboard

## Bối cảnh
Test 5 là dự án mở rộng nhằm cung cấp giao diện trực quan (UI) dựa trên nền tảng báo cáo Excel để quản lý hiệu suất Amazon Ads. Công cụ này xử lý dữ liệu từ file Bulk Operations (Amazon) kết hợp với các quy tắc kinh doanh từ Test 4 (Rule Engine) nhằm xây dựng bảng điều khiển cho Seller. 

Dự án này là Giai đoạn 1 (Phase 1: Excel Dashboard) và sẽ tạo tiền đề để nâng cấp lên giao diện Web ở Giai đoạn 2.

## Cấu trúc thư mục
- `input/`: Đặt file `BulkSheetExport.xlsx` tải từ Amazon vào đây.
- `output/`: Thư mục lưu kết quả `Amazon_Ads_Dashboard_{date}.xlsx`.
- `code/`: Chứa file mã nguồn `generate_dashboard.py`
- `config/`: Chứa `Rule_Engine.json` và `Season_Calendar.json` lấy từ Test 4.

## Các tính năng trên Dashboard
Script tự động sinh ra 1 file Excel duy nhất chứa 4 sheet chính:
1. **📊 OVERVIEW**: Thông số KPI toàn bộ tài khoản (Spend, Sales, ACOS, ROAS...).
2. **🎯 CAMPAIGNS**: Thông tin chi tiết của tất cả các chiến dịch quảng cáo, gán Health Tag tự động.
3. **🔑 KEYWORDS**: Hiệu suất từng Keyword/ASIN, và Đề xuất tăng/giảm Bid (theo Rule Engine).
4. **🔍 SEARCH TERMS**: Khai thác dữ liệu "Customer Search Term" thực tế để chặn keyword rác hoặc mở rộng keyword tiềm năng.

## Hướng dẫn sử dụng
1. Đảm bảo đã có file `.xlsx` ở thư mục `input`.
2. Mở Command Prompt hoặc Terminal.
3. Chạy script:
   ```cmd
   f:\Minhpython\venv\Scripts\python.exe f:\Minhpython\Test5\code\generate_dashboard.py
   ```
4. Mở thư mục `output/` để xem file báo cáo được sinh ra.
