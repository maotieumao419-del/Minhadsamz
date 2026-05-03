import json
import os
import sys
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def load_season_calendar(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def classify_seasonal(campaign, thresholds, today):
    pre_season_days = thresholds.get("pre_season_days", 21)
    post_season_days = thresholds.get("post_season_days", 7)

    event_date_str = campaign.get("Matched Event Date")
    if not event_date_str:
        # Fallback if somehow not matched
        return campaign, "evergreen"

    # Tính toán số ngày còn lại cho đến ngày lễ (Days to Event)
    event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
    days_remaining = (event_date - today).days

    # Phân loại vòng đời mùa vụ dựa vào ngưỡng (thresholds) cấu hình trong Season_Calendar.json
    # - Nếu số ngày âm nhiều hơn post_season_days: Đã qua mùa từ lâu -> post_season
    # - Nếu số ngày âm nhưng vẫn nằm trong post_season_days, hoặc vừa đúng ngày: Đang ở đuôi mùa -> post_season
    # - Nếu số ngày còn lại nhỏ hơn hoặc bằng pre_season_days: Đang ở giai đoạn chạy nước rút (cao điểm) -> peak_season
    # - Nếu còn rất xa mới tới ngày lễ: Mới bắt đầu chạy đà -> pre_season
    if days_remaining < -post_season_days:
        phase = "post_season"
    elif days_remaining < 0:
        phase = "post_season"
    elif days_remaining <= pre_season_days:
        phase = "peak_season"
    else:
        phase = "pre_season"

    result = campaign.copy()
    result["Season Label"] = campaign.pop("Matched Season Label")
    result["Event Date"] = campaign.pop("Matched Event Date")
    result["Days to Event"] = days_remaining
    result["Season Phase"] = phase
    # Clean up temp key
    result.pop("Matched Season Keyword", None)
    
    return result, phase

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_file = os.path.join(base_dir, "phase1", "output", "seasonal", "seasonal.json")
    config_file = os.path.join(base_dir, "Season_Calendar.json")
    out_seasonal_dir = os.path.join(base_dir, "phase1", "output", "seasonal")
    
    os.makedirs(out_seasonal_dir, exist_ok=True)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    print("=" * 60)
    print("  PHASE 1 - BƯỚC 2: Phân tách Campaign Seasonal")
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
    thresholds = calendar["thresholds"]

    pre_list = []
    peak_list = []
    post_list = []

    for camp in campaigns:
        classified_camp, phase = classify_seasonal(camp, thresholds, today)
        if phase == "pre_season":
            pre_list.append(classified_camp)
        elif phase == "peak_season":
            peak_list.append(classified_camp)
        elif phase == "post_season":
            post_list.append(classified_camp)

    pre_file = os.path.join(out_seasonal_dir, "pre_season.json")
    peak_file = os.path.join(out_seasonal_dir, "peak_season.json")
    post_file = os.path.join(out_seasonal_dir, "post_season.json")

    with open(pre_file, "w", encoding="utf-8") as f:
        json.dump(pre_list, f, indent=4, ensure_ascii=False)
    with open(peak_file, "w", encoding="utf-8") as f:
        json.dump(peak_list, f, indent=4, ensure_ascii=False)
    with open(post_file, "w", encoding="utf-8") as f:
        json.dump(post_list, f, indent=4, ensure_ascii=False)

    print(f"  Tổng số Campaign Seasonal đọc vào: {len(campaigns)}")
    print(f"  📁 {os.path.basename(pre_file)}: {len(pre_list)} campaigns")
    print(f"  📁 {os.path.basename(peak_file)}: {len(peak_list)} campaigns")
    print(f"  📁 {os.path.basename(post_file)}: {len(post_list)} campaigns")
    print("-" * 60)
    print("🎉 Bước 2 hoàn thành!\n")

if __name__ == "__main__":
    main()
