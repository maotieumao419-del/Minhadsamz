import os
import shutil
import glob
import sys

# Đảm bảo console xuất tiếng Việt mượt mà
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def transfer_to_phase3():
    phase2_output_dir = r"f:\Minhpython\Test3\phase2\output"
    phase3_input_dir = r"f:\Minhpython\Test3\phase3\input"
    
    # Tạo thư mục đầu vào cho phase 3 nếu chưa có
    os.makedirs(phase3_input_dir, exist_ok=True)
    
    # Xóa file JSON cũ trong phase3/input để tránh dữ liệu cũ từ lần chạy trước
    old_files = glob.glob(os.path.join(phase3_input_dir, "*.json"))
    if old_files:
        for old_f in old_files:
            os.remove(old_f)
        print(f"🧹 Đã xóa {len(old_files)} file cũ trong Phase 3 Input.")
    
    print(f"Bắt đầu luân chuyển dữ liệu từ Phase 2 sang Phase 3...")
    
    # Tìm tất cả file json sinh ra từ output phase 2
    json_files = glob.glob(os.path.join(phase2_output_dir, "*.json"))
    
    if not json_files:
        print("❌ Không tìm thấy file JSON nào trong Phase 2 Output.")
        return
        
    count = 0
    for file_path in json_files:
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(phase3_input_dir, file_name)
        
        # Tiến hành copy file
        shutil.copy2(file_path, dest_path)
        print(f" ✅ Đã nạp file: {file_name}")
        count += 1
        
    print(f"\n🚀 Đã chuyển tiếp thành công {count} cấu trúc JSON vào: {phase3_input_dir}")

if __name__ == "__main__":
    transfer_to_phase3()
