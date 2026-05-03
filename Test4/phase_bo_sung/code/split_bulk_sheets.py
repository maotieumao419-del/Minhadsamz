# =============================================================================
# Phase Bổ Sung: Tách file Bulk Excel thành các file JSON riêng biệt theo Sheet
# Input:  File BulkSheetExport*.xlsx từ thư mục phase_bo_sung/input
# Output: Các file JSON riêng biệt cho từng sheet tại phase_bo_sung/output
# =============================================================================

import polars as pl
import json
import os
import sys
import glob

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def split_bulk_to_json(excel_path, output_dir):
    """
    Đọc file Bulk Excel của Amazon, tách từng sheet ra thành file JSON riêng.
    
    - Sử dụng engine 'calamine' để đọc nhanh và ổn định.
    - Ép toàn bộ kiểu dữ liệu sang String để tránh lỗi Scientific Notation 
      (ví dụ: Campaign ID bị Excel tự đổi thành 1.53E+13).
    - Bỏ qua các sheet rỗng (0 dòng dữ liệu).
    """
    filename = os.path.basename(excel_path)
    print(f"🚀 Bắt đầu tách file: {filename}")
    print("-" * 60)

    try:
        # Sử dụng Polars đọc toàn bộ các sheet từ file Excel cùng một lúc (nhanh hơn Pandas rất nhiều)
        # Bằng cách để sheet_id=0, ta yêu cầu calamine engine nạp hết dữ liệu
        all_sheets = pl.read_excel(excel_path, sheet_id=0, engine="calamine")
    except Exception as e:
        print(f"❌ Lỗi đọc file Excel: {e}")
        return

    # Đảm bảo thư mục output tồn tại
    os.makedirs(output_dir, exist_ok=True)

    total_sheets = 0
    total_records = 0

    for sheet_name, df in all_sheets.items():
        # Bỏ qua sheet rỗng để tránh tạo ra file JSON trống không có ý nghĩa
        if df.height == 0:
            print(f"  ⏭ Bỏ qua sheet rỗng: '{sheet_name}'")
            continue

        # Tạo tên file an toàn: thay khoảng trắng và dấu gạch chéo bằng dấu gạch dưới / gạch ngang
        safe_name = sheet_name.replace(" ", "_").replace("/", "-")
        json_path = os.path.join(output_dir, f"{safe_name}.json")

        # Chuyển DataFrame (Polars) thành một danh sách các Dictionary, 
        # sẵn sàng để tuần tự hóa (serialize) thành chuỗi JSON
        dict_data = df.to_dicts()

        # Ghi dữ liệu ra file JSON, đảm bảo giữ được các ký tự UTF-8 (ensure_ascii=False)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dict_data, f, indent=4, ensure_ascii=False)

        print(f"  ✅ Sheet '{sheet_name}' → {safe_name}.json ({df.height} dòng, {df.width} cột)")
        total_sheets += 1
        total_records += df.height

    print("-" * 60)
    print(f"🎉 Hoàn thành! Đã tách {total_sheets} sheet, tổng cộng {total_records} bản ghi.")
    print(f"   Output: {output_dir}")


def main():
    # Xác định thư mục gốc (từ phase_bo_sung/code/ lùi 1 cấp về phase_bo_sung/)
    phase_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(phase_dir, "input")
    output_dir = os.path.join(phase_dir, "output")

    print("=" * 60)
    print("  PHASE BỔ SUNG: Tách Bulk Excel → JSON")
    print("=" * 60)
    print(f"  Input:  {input_dir}")
    print(f"  Output: {output_dir}")
    print()

    # Tìm tất cả file Excel trong thư mục input
    excel_files = glob.glob(os.path.join(input_dir, "*.xlsx"))

    if not excel_files:
        print(f"⚠️ Không tìm thấy file Excel nào trong: {input_dir}")
        return

    # Xử lý từng file Excel
    for file_path in excel_files:
        split_bulk_to_json(file_path, output_dir)
        print()


if __name__ == "__main__":
    main()
