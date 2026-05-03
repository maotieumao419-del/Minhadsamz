import os
import sys

# Đảm bảo console xuất được tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from supabase import create_client, Client

from dotenv import load_dotenv

# Tải các biến môi trường từ file .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# 1. Các thông tin cần thiết từ dự án Supabase của bạn. 
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 2. Khởi tạo một đối tượng "Client" để kết nối với Supabase.
# client này sẽ là cầu nối để ta gửi lệnh lên Supabase.
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Lỗi khởi tạo kết nối: {e}")
    # Nếu kết nối thất bại ngay từ bước này do URL/KEY không hợp lệ, thoát chương trình.
    exit()

def get_data_from_supabase(table_name="your_table_name"):
    """
    Hàm này lấy tất cả dữ liệu từ một bảng trên Supabase.
    Bạn truyền tên bảng muốn lấy vào biến table_name.
    """
    try:
        # 3. Thực hiện truy vấn (lấy dữ liệu dể đọc)
        # - table(table_name): Chọn bảng cần lấy dữ liệu
        # - select("*"): Lấy toàn bộ các cột. Nếu chỉ muốn một số cột, ghi tên cột: select("id, name")
        # - execute(): Bắt đầu thực thi lệnh và lấy kết quả trả về từ server Supabase.
        response = supabase.table(table_name).select("*").execute()
        
        # 4. Trích xuất dữ liệu từ kết quả (response)
        # response có nhiều trường, nhưng ta chỉ cần quan tâm `data` chứa dữ liệu dạng một list các JSON.
        data = response.data
        
        print(f"Đã lấy thành công {len(data)} bản ghi từ bảng '{table_name}'.")
        print("\n--- Bản ghi đầu tiên mẫu ---")
        
        if len(data) > 0:
            print(data[0])  # In dòng đầu tiên ra màn hình dạng Từ điển (Dictionary) của Python
        else:
            print("Bảng này hiện chưa có dữ liệu.")
            
        return data

    except Exception as e:
        # Nếu bảng có RLS (Row Level Security) khóa chặt chặn đọc, hoặc sai tên bảng, sẽ báo lỗi ở đây.
        print(f"Lỗi khi thực hiện lấy dữ liệu từ Supabase: {e}")
        return None

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    # Đã cập nhật thành bảng '123'
    my_table = "123" 
    
    # 5. Gọi hàm bên trên để lấy data
    my_data = get_data_from_supabase(my_table)
    
    # 6. Dùng Polars để chuyển đổi và xuất file kết quả
    if my_data is not None and len(my_data) > 0:
        import polars as pl
        import json
        
        # Tạo DataFrame từ list data
        df = pl.DataFrame(my_data)
        print("\n--- Dữ liệu trong Polars DataFrame ---")
        print(df.head(3))  # In thử 3 dòng ra console
        
        # Tạo thư mục output nếu chưa có
        output_dir = r"f:\Minhpython\Test3\phase1\output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Xuất ra file Excel
        excel_path = os.path.join(output_dir, "supabase_data.xlsx")
        df.write_excel(excel_path)
        print(f"\n Đã lưu toàn bộ dữ liệu ra file Excel: {excel_path}")
        
        # Xuất ra file JSON
        json_path = os.path.join(output_dir, "supabase_data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(my_data, f, indent=4, ensure_ascii=False)
        print(f" Đã lưu toàn bộ dữ liệu ra file JSON: {json_path}")

