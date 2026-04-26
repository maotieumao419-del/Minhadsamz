import os
import json
import shutil
import sys

# Đảm bảo console xuất tiếng Việt mượt mà
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- CÁC ĐƯỜNG DẪN CẦN THIẾT ---
sku_json_path = r"f:\Minhpython\Test3\phase2\input\sku_tiep_nhan.json"
source_dir = r"f:\Minhpython\Test3\phase0\output"
output_dir = r"f:\Minhpython\Test3\phase2\output"

# Đảm bảo thư mục output tồn tại (phòng trường hợp xoá nhầm)
os.makedirs(output_dir, exist_ok=True)

# Xóa file JSON cũ trong output để tránh dữ liệu cũ từ lần chạy trước
import glob as _glob
old_files = _glob.glob(os.path.join(output_dir, "*.json"))
if old_files:
    for old_f in old_files:
        os.remove(old_f)
    print(f"🧹 Đã xóa {len(old_files)} file cũ trong Phase 2 Output.")

try:
    # 1. Nạp danh sách SKU đang ở trạng thái 'Tiếp nhận'
    print(f"Đang đọc danh sách mục tiêu từ: {sku_json_path}")
    with open(sku_json_path, 'r', encoding='utf-8') as f:
        sku_list = json.load(f)
    
    # Dùng hàm `set` của Python để loại bỏ các SKU bị trùng lặp trong mảng
    unique_skus = list(set(sku_list))
    print(f"➜ Dữ liệu yêu cầu có {len(unique_skus)} SKU độc nhất. Bắt đầu đối chiếu...\n")

    found_count = 0
    # 2. Duyệt qua từng SKU để quét file
    for sku in unique_skus:
        # Chuẩn hoá lại tên file khớp vòng lặp xuất file (thay dấu cách bằng _, thay '/' bằng '-')
        safe_name = sku.replace(" ", "_").replace("/", "-")
        expected_filename = f"{safe_name}.json"
        
        source_file = os.path.join(source_dir, expected_filename)
        dest_file = os.path.join(output_dir, expected_filename)
        
        # 3. Kiểm tra xem file json cho SKU này có thực sự tồn tại trong thư mục nhiều sheet không
        if os.path.exists(source_file):
            # Nếu có, thực hiện Copy file qua thư mục mới
            shutil.copy2(source_file, dest_file)
            print(f" ✅ Đã chuyển: {expected_filename}")
            found_count += 1
        else:
            # Nếu file Excel lúc đầu không hề có sheet mang mã SKU này
            print(f" ❌ Kho dữ liệu không chứa sheet cho: {sku}")
            
    print(f"\n🚀 TỔNG KẾT: Đã lôi ra thành công {found_count}/{len(unique_skus)} file JSON đạt điều kiện 'Tiếp nhận'.")
    print(f"Đích đến: {output_dir}")

except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")
