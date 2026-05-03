import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def load_season_calendar(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def match_season(campaign_name, seasons):
    name_upper = campaign_name.upper()
    for season in seasons:
        if season["keyword"].upper() in name_upper:
            return season
    return None

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_file = os.path.join(base_dir, "phase0", "output", "campaigns.json")
    config_file = os.path.join(base_dir, "Season_Calendar.json")
    
    out_evergreen_dir = os.path.join(base_dir, "phase1", "output", "evergreen")
    out_seasonal_dir = os.path.join(base_dir, "phase1", "output", "seasonal")
    
    os.makedirs(out_evergreen_dir, exist_ok=True)
    os.makedirs(out_seasonal_dir, exist_ok=True)

    print("=" * 60)
    print("  PHASE 1 - BƯỚC 1: Lọc Campaign Evergreen & Seasonal")
    print("=" * 60)

    if not os.path.exists(input_file):
        print(f"❌ Không tìm thấy: {input_file}")
        return
    if not os.path.exists(config_file):
        print(f"❌ Không tìm thấy: {config_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        campaigns = json.load(f)

    calendar = load_season_calendar(config_file)
    seasons = calendar["seasons"]

    evergreen_list = []
    seasonal_list = []

    for camp in campaigns:
        # Kiểm tra xem tên Campaign có chứa keyword Mùa vụ nào không (VD: "Mother's Day", "Christmas")
        # Sự so sánh này không phân biệt hoa thường (nhờ name_upper trong hàm match_season)
        matched = match_season(camp["Campaign Name"], seasons)
        
        if matched:
            # Nếu khớp, lưu tạm thông tin Mùa vụ vào record để script số 2 (classify_seasonal) 
            # có thể sử dụng luôn mà không cần phải chạy lại logic dò tìm
            camp["Matched Season Keyword"] = matched["keyword"]
            camp["Matched Season Label"] = matched["label"]
            camp["Matched Event Date"] = matched["event_date"]
            seasonal_list.append(camp)
        else:
            # Nếu không khớp bất kỳ keyword mùa vụ nào, chiến dịch đó mặc định là Evergreen (quanh năm)
            evergreen_list.append(camp)

    evergreen_file = os.path.join(out_evergreen_dir, "evergreen.json")
    seasonal_file = os.path.join(out_seasonal_dir, "seasonal.json")

    with open(evergreen_file, "w", encoding="utf-8") as f:
        json.dump(evergreen_list, f, indent=4, ensure_ascii=False)
        
    with open(seasonal_file, "w", encoding="utf-8") as f:
        json.dump(seasonal_list, f, indent=4, ensure_ascii=False)

    print(f"  Tổng số Campaign đọc vào: {len(campaigns)}")
    print(f"  📁 {os.path.basename(evergreen_file)}: {len(evergreen_list)} campaigns")
    print(f"  📁 {os.path.basename(seasonal_file)}: {len(seasonal_list)} campaigns")
    print("-" * 60)
    print("🎉 Bước 1 hoàn thành!\n")

if __name__ == "__main__":
    main()
