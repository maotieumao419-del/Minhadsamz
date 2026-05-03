import json
import os
import sys
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def classify_evergreen(campaign, today):
    start_date_str = campaign.get("Start Date", "")
    impressions = campaign.get("Impressions", 0)
    
    # Fallback nếu không parse được ngày
    phase = "mature_phase" 
    
    if start_date_str and len(start_date_str) == 8:
        try:
            # Parse ngày tạo chiến dịch từ định dạng YYYYMMDD
            start_date = datetime.strptime(start_date_str, "%Y%m%d")
            # Tính tuổi đời (số ngày) của chiến dịch
            age_days = (today - start_date).days
            
            # Phân loại dựa trên tuổi đời và lượng traffic
            if age_days < 30:
                phase = "launch_phase"  # Mới tạo, đang dò đường tìm keyword ngon
            elif age_days <= 90:
                phase = "growth_phase"  # Bắt đầu có data, cần tối ưu để tăng trưởng
            else:
                # Nếu đã chạy lâu (hơn 90 ngày) mà traffic rất lẹt đẹt (<100 impressions)
                # thì xếp vào nhóm ngủ đông (dormant), tránh bị rule phạt nhầm do data mỏng
                if impressions < 100:
                    phase = "dormant_phase"
                else:
                    phase = "mature_phase" # Trưởng thành, nguồn thu chính, cần giữ vững ROAS
        except ValueError:
            pass

    result = campaign.copy()
    result["Season Phase"] = phase
    
    if phase == "launch_phase":
        result["Season Label"] = "Khởi động (<30 ngày)"
    elif phase == "growth_phase":
        result["Season Label"] = "Tăng trưởng (30-90 ngày)"
    elif phase == "mature_phase":
        result["Season Label"] = "Trưởng thành (>90 ngày)"
    elif phase == "dormant_phase":
        result["Season Label"] = "Ngủ đông (Ít traffic)"

    result["Event Date"] = ""
    result["Days to Event"] = None
    
    return result, phase

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # File input gốc do 1_split_campaigns.py tạo ra
    input_file = os.path.join(base_dir, "phase1", "output", "evergreen", "evergreen.json")
    out_evergreen_dir = os.path.join(base_dir, "phase1", "output", "evergreen")
    
    os.makedirs(out_evergreen_dir, exist_ok=True)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    print("=" * 60)
    print("  PHASE 1 - BƯỚC 3: Phân tách Campaign Evergreen")
    print("=" * 60)

    if not os.path.exists(input_file):
        print(f"❌ Không tìm thấy: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        campaigns = json.load(f)

    launch_list = []
    growth_list = []
    mature_list = []
    dormant_list = []

    for camp in campaigns:
        classified_camp, phase = classify_evergreen(camp, today)
        if phase == "launch_phase":
            launch_list.append(classified_camp)
        elif phase == "growth_phase":
            growth_list.append(classified_camp)
        elif phase == "mature_phase":
            mature_list.append(classified_camp)
        elif phase == "dormant_phase":
            dormant_list.append(classified_camp)

    launch_file = os.path.join(out_evergreen_dir, "launch_phase.json")
    growth_file = os.path.join(out_evergreen_dir, "growth_phase.json")
    mature_file = os.path.join(out_evergreen_dir, "mature_phase.json")
    dormant_file = os.path.join(out_evergreen_dir, "dormant_phase.json")

    with open(launch_file, "w", encoding="utf-8") as f:
        json.dump(launch_list, f, indent=4, ensure_ascii=False)
    with open(growth_file, "w", encoding="utf-8") as f:
        json.dump(growth_list, f, indent=4, ensure_ascii=False)
    with open(mature_file, "w", encoding="utf-8") as f:
        json.dump(mature_list, f, indent=4, ensure_ascii=False)
    with open(dormant_file, "w", encoding="utf-8") as f:
        json.dump(dormant_list, f, indent=4, ensure_ascii=False)

    print(f"  Tổng số Campaign Evergreen đọc vào: {len(campaigns)}")
    print(f"  📁 {os.path.basename(launch_file)}: {len(launch_list)} campaigns")
    print(f"  📁 {os.path.basename(growth_file)}: {len(growth_list)} campaigns")
    print(f"  📁 {os.path.basename(mature_file)}: {len(mature_list)} campaigns")
    print(f"  📁 {os.path.basename(dormant_file)}: {len(dormant_list)} campaigns")
    print("-" * 60)
    print("🎉 Bước 3 hoàn thành!\n")

if __name__ == "__main__":
    main()
