import os
import glob
import json
import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    phase3_output_dir = os.path.join(base_dir, "phase3", "output")
    phase4_output_dir = os.path.join(base_dir, "phase4", "output")
    
    os.makedirs(phase4_output_dir, exist_ok=True)
    
    print("=" * 60)
    print("  PHASE 4: XÂY DỰNG HUMAN-REVIEW DASHBOARD")
    print("=" * 60)
    
    # Gom tất cả file JSON từ Phase 3
    json_files = glob.glob(os.path.join(phase3_output_dir, "**", "*.json"), recursive=True)
    
    review_items = []
    
    for fpath in json_files:
        keywords = load_json(fpath)
        for kw in keywords:
            if kw.get("Approval Status") == "REQUIRES_REVIEW":
                kw["Source File"] = os.path.basename(fpath)
                review_items.append(kw)
                
    if not review_items:
        print("  🎉 Tuyệt vời! Không có Keyword nào vi phạm rào chắn cần duyệt.")
        return
        
    print(f"  🚨 Phát hiện {len(review_items)} Keywords cần con người phê duyệt!")
    
    # Transform data
    transformed_data = []
    for item in review_items:
        cvr = round(item.get("Orders", 0) / item.get("Clicks", 1) * 100, 2) if item.get("Clicks", 0) > 0 else 0.0
        
        row = {
            "Season Phase": item.get("Season Phase", ""),
            "Campaign Name": item.get("Campaign Name", ""),
            "Keyword Text": item.get("Keyword Text", ""),
            "Match Type": item.get("Match Type", ""),
            "Impressions": item.get("Impressions", 0),
            "Clicks": item.get("Clicks", 0),
            "Orders": item.get("Orders", 0),
            "Spend": item.get("Spend", 0.0),
            "Sales": item.get("Sales", 0.0),
            "ACOS": item.get("ACOS", 0.0),
            "CVR": f"{cvr}%",
            "Current Bid": item.get("Bid", 0.0),
            "Suggested Action": item.get("Suggested Action", ""),
            "Suggested Bid": item.get("Suggested Bid", ""),
            "Review Reason": item.get("Review Reason", ""),
            "Final Human Decision (YES/REJECT)": "YES", # Default là YES để tiện duyệt
            "Final Human Bid": "", # Trống để User tự điền nếu muốn override
            "Campaign ID": item.get("Campaign ID", ""),
            "Ad Group ID": item.get("Ad Group ID", ""),
            "Keyword ID": item.get("Keyword ID", "")
        }
        transformed_data.append(row)
        
    df = pd.DataFrame(transformed_data)
    
    output_path = os.path.join(phase4_output_dir, "Action_Required_Dashboard.xlsx")
    
    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Human Review")
        print(f"  ✅ Đã xuất Dashboard ra file: {output_path}")
        print("  👉 Vui lòng mở file, kiểm tra cột 'Review Reason' và chốt quyết định tại cột 'Final Human Decision'.")
    except Exception as e:
        print(f"❌ Lỗi khi xuất Excel: {e}")
        print("Đang thử xuất sang CSV...")
        csv_path = output_path.replace(".xlsx", ".csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"  ✅ Đã xuất tạm ra CSV: {csv_path}")

if __name__ == "__main__":
    main()
