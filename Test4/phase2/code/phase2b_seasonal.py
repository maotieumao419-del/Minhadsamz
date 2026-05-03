import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    phase1_seasonal_dir = os.path.join(base_dir, "phase1", "output", "seasonal")
    keywords_file = os.path.join(base_dir, "phase0", "output", "keywords.json")
    output_dir = os.path.join(base_dir, "phase2", "output")
    
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  PHASE 2B: Lọc & Nhóm Keyword Seasonal")
    print("=" * 60)

    if not os.path.exists(keywords_file):
        print(f"❌ Không tìm thấy: {keywords_file}")
        return

    # Đọc dữ liệu
    campaigns = []
    for phase in ["pre_season", "peak_season", "post_season"]:
        fpath = os.path.join(phase1_seasonal_dir, f"{phase}.json")
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                campaigns.extend(json.load(f))
    
    with open(keywords_file, "r", encoding="utf-8") as f:
        keywords = json.load(f)

    # 1. Tạo lookup dictionary cho seasonal campaigns
    seasonal_campaigns = {}
    for c in campaigns:
        if c.get("Season Phase") != "evergreen":
            seasonal_campaigns[c["Campaign ID"]] = c

    # 2. Phân loại keywords
    pre_season_kws = []
    peak_season_kws = []
    post_season_kws = []
    paused_review_kws = []

    for kw in keywords:
        camp_id = kw.get("Campaign ID")
        if camp_id in seasonal_campaigns:
            camp_info = seasonal_campaigns[camp_id]
            phase = camp_info["Season Phase"]
            state = kw.get("State")
            
            # Enrich keyword: Gom chung chỉ số của Keyword và thông tin của Campaign (Mùa vụ, Ngày lễ)
            enriched_kw = {
                "Campaign ID": kw["Campaign ID"],
                "Campaign Name": camp_info["Campaign Name"],
                "Ad Group ID": kw["Ad Group ID"],
                "Keyword ID": kw["Keyword ID"],
                "Keyword Text": kw["Keyword Text"],
                "Match Type": kw["Match Type"],
                "Bid": kw["Bid"],
                "State": kw["State"],
                "Impressions": kw["Impressions"],
                "Clicks": kw["Clicks"],
                "Spend": kw["Spend"],
                "Sales": kw["Sales"],
                "Orders": kw["Orders"],
                "Units": kw.get("Units", 0),
                "Click-through Rate": kw.get("Click-through Rate", 0),
                "Conversion Rate": kw.get("Conversion Rate", 0),
                "ACOS": kw.get("ACOS", 0),
                "CPC": kw.get("CPC", 0),
                "ROAS": kw.get("ROAS", 0),
                "Season Phase": phase,
                "Season Label": camp_info["Season Label"],
                "Event Date": camp_info.get("Event Date", ""),
                "Days to Event": camp_info.get("Days to Event", None)
            }
            
            # Phân luồng dựa theo trạng thái (State) và Mùa vụ (Phase)
            if state == "enabled":
                if phase == "pre_season":
                    pre_season_kws.append(enriched_kw)
                elif phase == "peak_season":
                    peak_season_kws.append(enriched_kw)
                elif phase == "post_season":
                    post_season_kws.append(enriched_kw)
            elif state == "paused":
                # Tính năng đặc biệt: Nếu Keyword đang bị tắt (Paused), nhưng Campaign của nó
                # chuẩn bị vào mùa (Pre) hoặc đang vào mùa (Peak), ta sẽ gom nó ra một file riêng
                # để User có thể cân nhắc "Bật lại" (Enable) thay vì bỏ quên nó.
                if phase in ["pre_season", "peak_season"]:
                    paused_review_kws.append(enriched_kw)
                # Paused + post_season -> Bỏ qua (Đã qua mùa, kệ nó tắt)

    # 3. Xuất file
    output_seasonal_dir = os.path.join(output_dir, "seasonal")
    os.makedirs(output_seasonal_dir, exist_ok=True)

    def write_json(filename, data):
        path = os.path.join(output_seasonal_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return path

    f_pre = write_json("pre_season.json", pre_season_kws)
    f_peak = write_json("peak_season.json", peak_season_kws)
    f_post = write_json("post_season.json", post_season_kws)
    f_paused = write_json("paused_seasonal_review.json", paused_review_kws)

    # 4. In thống kê
    print(f"  Thống kê Seasonal Campaigns: {len(seasonal_campaigns)} campaigns")
    print(f"    - Pre-season:  {len(pre_season_kws)} keywords (enabled)")
    print(f"    - Peak-season: {len(peak_season_kws)} keywords (enabled)")
    print(f"    - Post-season: {len(post_season_kws)} keywords (enabled)")
    print(f"    - Paused review: {len(paused_review_kws)} keywords (paused, sắp/đang mùa)")
    print("-" * 60)
    print("  📁 Các file đã lưu:")
    print(f"    {os.path.basename(f_pre)}")
    print(f"    {os.path.basename(f_peak)}")
    print(f"    {os.path.basename(f_post)}")
    print(f"    {os.path.basename(f_paused)}")
    print("-" * 60)
    print("🎉 Phase 2B hoàn thành!\n")

if __name__ == "__main__":
    main()
