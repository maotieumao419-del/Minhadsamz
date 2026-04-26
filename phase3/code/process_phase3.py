import os
import glob
import json
import sys
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Đường dẫn thư mục
input_dir = r"f:\Minhpython\Test3\phase3\input"
output_dir = r"f:\Minhpython\Test3\phase3\output"

# Đảm bảo output tồn tại
os.makedirs(output_dir, exist_ok=True)

# Xóa file JSON cũ trong output để tránh dữ liệu cũ từ lần chạy trước đi vào Phase 4
old_output_files = glob.glob(os.path.join(output_dir, "*.json"))
if old_output_files:
    for old_f in old_output_files:
        os.remove(old_f)
    print(f"🧹 Đã xóa {len(old_output_files)} file cũ trong Phase 3 Output.")

# Lấy danh sách toàn bộ file json
json_files = glob.glob(os.path.join(input_dir, "*.json"))

if not json_files:
    print("❌ Không có file JSON nào trong input của Phase 3!")
    exit()

print(f"Bắt đầu xử lý {len(json_files)} file JSON cho Phase 3...\n")

date_suffix = datetime.now().strftime("%Y%m%d")

for file_path in json_files:
    file_name = os.path.basename(file_path)
    
    # 1. Trích xuất tên SKU (bằng cách bỏ đuôi .json)
    sku_name = os.path.splitext(file_name)[0]
    
    print(f"➜ Đang xử lý SKU: {sku_name}")
    
    # Đọc cấu trúc JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    stt_counter = 1
    # Xử lý từng dòng trong kết quả
    for row in data:
        # 1. STT đánh từ 1 đến hết
        row["STT"] = stt_counter
        stt_counter += 1
        
        # 2. Loại Campaign mặc định là "Keyword"
        row["Loại Campaign"] = "Keyword"
        
        # 3. Trạng thái mặc định để "Chưa tạo"
        row["Trạng thái"] = "Chưa tạo"
        
        # Làm sạch chuỗi Target (tuỳ chọn hữu ích vì đôi khi có dấu xuống dòng \n từ Excel)
        target = str(row.get("Target") or "").strip()
        row["Target"] = target
        
        # 4. Đọc dữ liệu đã chuẩn hóa từ Phase 0 (thay vì parse lại từ "Ghi chú")
        # Match Type: đã chuẩn hóa thành exact / phrase / broad (viết thường)
        match_type = row.get("Match Type") or "unknownmatch"
        
        # Bid: giá trị số thập phân (ví dụ: 0.6, 0.35, 0.56)
        bid = row.get("Bid")
        
        # Placement: đã chuẩn hóa thành dạng "30T30R30P" từ Phase 0
        placement = row.get("Placement") or "UnknownPlacement"
        
        # 5. Lắp ghép tên chiến dịch
        # Yêu cầu mới: dấu cách của target khi đưa vào campaign name thay bằng gạch dưới
        target_in_campaign = target.replace(" ", "_")
        # Cấu trúc: "SKU_KT_Match Type_Target_Placement_YYYYMMDD"
        campaign_name = f"{sku_name}_KT_{match_type}_{target_in_campaign}_{placement}_{date_suffix}"
        row["Campaign Name"] = campaign_name
        
    # Ghi file xuất ra Output
    output_path = os.path.join(output_dir, file_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print(f"   ✅ Đã hoàn thiện và lưu vào: {output_path}")
    print(f"   Mẫu Campaign Name dòng 1: {data[0].get('Campaign Name') if data else 'N/A'}\n")

print("🎉 Hoàn tất quy trình hoàn thiện dữ liệu Phase 3!")
