import polars as pl
import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def convert_all_sheets_to_json(excel_path, output_dir):
    print(f"Bắt đầu đọc file: {excel_path}\n")
    
    # Dùng sheet_id=0 để xả toàn bộ tất cả các sheet trong Excel ra cùng lúc
    # Kết quả trả về là một Dictionary (Từ điển) cấu trúc: {"Tên_Sheet": DataFrame_của_sheet_đó}
    try:
        all_sheets_dict = pl.read_excel(excel_path, sheet_id=0, engine="calamine")
        
        # Đảm bảo thư mục đầu ra tồn tại
        os.makedirs(output_dir, exist_ok=True)
        
        # Duyệt qua từng Sheet và xuất ra file JSON riêng
        for sheet_name, df in all_sheets_dict.items():
            print(f"➤ Đang xử lý Sheet: '{sheet_name}' ({df.height} dòng)")
            
            # Đặt tên file xuất ra theo tên sheet (loại bỏ ký tự lạ nếu có)
            safe_name = sheet_name.replace(" ", "_").replace("/", "-")
            json_path = os.path.join(output_dir, f"{safe_name}.json")
            
            # Xuất sang Dictionary của py và đẩy ra JSON chuẩn Supabase
            dict_data = df.to_dicts()
            
            # --- LỌC TRÙNG: Loại bỏ các khối JSON có nội dung giống hệt nhau ---
            original_count = len(dict_data)
            seen = set()
            unique_data = []
            for item in dict_data:
                # Chỉ lấy các cột quyết định việc tạo Campaign Name để so sánh
                target_val = str(item.get("Target") or "").strip().lower()
                ghi_chu_val = str(item.get("Ghi chú") or "").strip().lower()
                match_type_val = str(item.get("Match Type") or "").strip().lower()
                placement_val = str(item.get("Placement") or "").strip().lower()
                
                # Tạo key duy nhất không phân biệt hoa thường và khoảng trắng dư
                item_key = f"{target_val}|{ghi_chu_val}|{match_type_val}|{placement_val}"
                
                if item_key not in seen:
                    seen.add(item_key)
                    unique_data.append(item)
            
            duplicates_removed = original_count - len(unique_data)
            if duplicates_removed > 0:
                print(f"   ⚠ Đã loại bỏ {duplicates_removed} khối JSON trùng lặp (giữ {len(unique_data)}/{original_count})")
            # --- KẾT THÚC LỌC TRÙNG ---
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(unique_data, f, indent=4, ensure_ascii=False)
                
            print(f"   Đã lưu: {json_path}")
            
        print("\n✅ Xử lý hoàn tất tất cả các Sheet!")
        
    except Exception as e:
        print(f"Lỗi đọc file: {e}")

if __name__ == "__main__":
    # Nguồn cấp: File Excel nhiều sheet của bạn (lấy tất cả excel trong input)
    input_dir = r"f:\Minhpython\Test3\phase_bo_sung\input"
    out_dir = r"f:\Minhpython\Test3\phase_bo_sung\output"
    
    import glob
    excel_files = glob.glob(os.path.join(input_dir, "*.xlsx"))
    if excel_files:
        for input_file in excel_files:
            convert_all_sheets_to_json(input_file, out_dir)
    else:
        print(f"Không tìm thấy file Excel nào trong {input_dir}")
