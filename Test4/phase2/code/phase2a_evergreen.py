import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    campaigns_file = os.path.join(base_dir, "phase1", "output", "evergreen", "evergreen.json")
    keywords_file = os.path.join(base_dir, "phase0", "output", "keywords.json")
    output_dir = os.path.join(base_dir, "phase2", "output")
    output_evergreen_dir = os.path.join(output_dir, "evergreen")
    output_file = os.path.join(output_evergreen_dir, "evergreen.json")

    os.makedirs(output_evergreen_dir, exist_ok=True)

    print("=" * 60)
    print("  PHASE 2A: Lọc & Nhóm Keyword Evergreen")
    print("=" * 60)

    if not os.path.exists(campaigns_file):
        print(f"❌ Không tìm thấy: {campaigns_file}")
        return
    if not os.path.exists(keywords_file):
        print(f"❌ Không tìm thấy: {keywords_file}")
        return

    # Đọc dữ liệu campaigns
    phase1_evergreen_dir = os.path.join(base_dir, "phase1", "output", "evergreen")
    campaigns = []
    for phase in ["launch_phase", "growth_phase", "mature_phase", "dormant_phase"]:
        fpath = os.path.join(phase1_evergreen_dir, f"{phase}.json")
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                campaigns.extend(json.load(f))
    
    with open(keywords_file, "r", encoding="utf-8") as f:
        keywords = json.load(f)

    # 1. Tạo lookup dictionary cho evergreen campaigns
    evergreen_campaigns = {c["Campaign ID"]: c for c in campaigns}

    # 2. Lọc và enrich keywords (Gắn thêm thông tin Campaign vào từng Keyword)
    evergreen_keywords = []
    for kw in keywords:
        camp_id = kw.get("Campaign ID")
        # Chỉ lấy những keyword thuộc Evergreen Campaigns và đang được BẬT (enabled)
        if camp_id in evergreen_campaigns and kw.get("State") == "enabled":
            camp_info = evergreen_campaigns[camp_id]
            
            # Khởi tạo keyword enriched với thứ tự field gọn gàng
            # Mục đích: Gom cả dữ liệu Campaign (Tên, Label vòng đời) và Keyword vào 1 object
            # để Phase 3 chấm điểm dễ dàng hơn mà không cần join lại.
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
                "Season Phase": camp_info["Season Phase"],
                "Season Label": camp_info["Season Label"]
            }
            evergreen_keywords.append(enriched_kw)

    # 3. Phân luồng keywords vào các "xô" (buckets) tương ứng
    # Thay vì để tất cả keyword evergreen chung 1 cục, ta chia nhỏ ra 4 file
    # để Phase 3 có thể load từng file và áp dụng rule/ngưỡng khác nhau.
    launch_kws = []
    growth_kws = []
    mature_kws = []
    dormant_kws = []

    for kw in evergreen_keywords:
        phase = kw["Season Phase"]
        if phase == "launch_phase":
            launch_kws.append(kw)
        elif phase == "growth_phase":
            growth_kws.append(kw)
        elif phase == "mature_phase":
            mature_kws.append(kw)
        elif phase == "dormant_phase":
            dormant_kws.append(kw)

    def write_json(filename, data):
        path = os.path.join(output_evergreen_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return path

    write_json("launch_phase.json", launch_kws)
    write_json("growth_phase.json", growth_kws)
    write_json("mature_phase.json", mature_kws)
    write_json("dormant_phase.json", dormant_kws)

    print(f"  Đã lọc: {len(evergreen_keywords)} keywords (thuộc {len(evergreen_campaigns)} campaigns Evergreen)")
    print(f"    - Khởi động (<30 ngày): {len(launch_kws)} keywords")
    print(f"    - Tăng trưởng (30-90 ngày): {len(growth_kws)} keywords")
    print(f"    - Trưởng thành (>90 ngày): {len(mature_kws)} keywords")
    print(f"    - Ngủ đông (Ít traffic): {len(dormant_kws)} keywords")
    print("-" * 60)
    print("🎉 Phase 2A hoàn thành!\n")

if __name__ == "__main__":
    main()
