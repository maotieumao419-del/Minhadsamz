import polars as pl
import sys

# 1. Đảm bảo console xuất được tiếng Việt không bị lỗi font
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 2. Định nghĩa đường dẫn file
json_file = r"f:\Minhpython\Test3\phase1\output\supabase_data.json"

print(f"Đang đọc dữ liệu từ: {json_file}")
try:
    # 3. Đọc file JSON trực tiếp vào Polars DataFrame
    df = pl.read_json(json_file)
    
    # 4. Lọc dữ liệu: 
    # Tìm cột "Status" có chứa chữ "Tiếp nhận"
    # Dùng hàm `str.contains()` để lọc chính xác và an toàn kể cả khi có khoảng trắng dư
    df_filtered = df.filter(pl.col("Status").str.contains("Tiếp nhận", literal=True))
    
    # 5. Rút trích riêng cột SKU (chuyển thành dạng danh sách của python)
    sku_list = df_filtered["SKU"].to_list()
    
    print(f"\n--- KẾT QUẢ: Tìm thấy {len(sku_list)} SKU có trạng thái 'Tiếp nhận' ---")
    for i, sku in enumerate(sku_list, start=1):
        print(f" {i}. {sku}")
        
    # 6. Ghi xuất kết quả ra file JSON vào thư mục input của phase 2
    import json
    import os
    
    # Định nghĩa đường dẫn và tạo các thư mục cha nếu chưa có (mặc dù đã dùng code PowerShell tạo ngoài rồi)
    output_json = r"f:\Minhpython\Test3\phase2\input\sku_tiep_nhan.json"
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    
    # Lưu file
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(sku_list, f, indent=4, ensure_ascii=False)
        
    print(f"\n✅ Đã lưu danh sách SKU thành công vào file: {output_json}")
        
except Exception as e:
    print(f"Lỗi khi xử lý dữ liệu: {e}")
