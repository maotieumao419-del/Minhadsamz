import os
import glob
import json
import pandas as pd
from datetime import datetime
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

AMAZON_TEMPLATE_COLUMNS = [
    'Product', 'Entity', 'Operation', 'Campaign ID', 'Ad Group ID', 'Portfolio ID',
    'Ad ID', 'Keyword ID', 'Product Targeting ID', 'Campaign Name', 'Ad Group Name',
    'Start Date', 'End Date', 'Targeting Type', 'State', 'Daily Budget', 'SKU',
    'Ad Group Default Bid', 'Bid', 'Keyword Text', 'Native Language Keyword',
    'Native Language Locale', 'Match Type', 'Bidding Strategy', 'Placement',
    'Percentage', 'Product Targeting Expression', 'Audience ID', 'Shopper Cohort Percentage',
    'Shopper Cohort Type'
]

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def safe_float(val):
    if pd.isna(val) or val == "":
        return ""
    try:
        return float(val)
    except:
        return ""

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    phase3_output_dir = os.path.join(base_dir, "phase3", "output")
    phase4_output_dir = os.path.join(base_dir, "phase4", "output")
    phase5_output_dir = os.path.join(base_dir, "phase5", "output")
    
    os.makedirs(phase5_output_dir, exist_ok=True)
    
    print("=" * 60)
    print("  PHASE 5: XÂY DỰNG FILE UPLOAD AMAZON CUỐI CÙNG")
    print("=" * 60)
    
    human_decisions = {}
    dashboard_path = os.path.join(phase4_output_dir, "Action_Required_Dashboard.xlsx")
    
    if os.path.exists(dashboard_path):
        try:
            df_human = pd.read_excel(dashboard_path)
            for _, row in df_human.iterrows():
                kw_id = str(row.get("Keyword ID", "")).replace(".0", "")
                if not kw_id or kw_id == "nan": continue
                
                decision = str(row.get("Final Human Decision (YES/REJECT)", "")).strip().upper()
                human_bid = safe_float(row.get("Final Human Bid", ""))
                suggested_bid = safe_float(row.get("Suggested Bid", ""))
                
                if decision in ["REJECT", "NO", "N", "KHÔNG", "KHONG", "HUỶ", "HUY", ""]:
                    human_decisions[kw_id] = {"status": "REJECTED"}
                else:
                    # Logic lấy Bid: Ưu tiên Final Human Bid, nếu trống lấy Suggested Bid
                    final_human_bid = human_bid if human_bid != "" else suggested_bid
                    human_decisions[kw_id] = {
                        "status": "APPROVED",
                        "human_bid": final_human_bid
                    }
            print(f"  ✅ Đã đọc {len(human_decisions)} phán quyết từ file Excel.")
        except Exception as e:
            print(f"  ❌ Lỗi khi đọc file Excel Dashboard: {e}")
    else:
        print("  ⏭ Không tìm thấy file Excel Dashboard. Sẽ chỉ lấy các quyết định AUTO_APPROVED.")
        
    json_files = glob.glob(os.path.join(phase3_output_dir, "**", "*.json"), recursive=True)
    
    upload_rows = []
    rejected_count = 0
    auto_count = 0
    human_count = 0
    
    for fpath in json_files:
        keywords = load_json(fpath)
        for kw in keywords:
            action = kw.get("Suggested Action", "")
            if not action: continue
            
            approval_status = kw.get("Approval Status", "")
            kw_id = str(kw.get("Keyword ID", "")).replace(".0", "")
            
            final_action = action
            final_bid = safe_float(kw.get("Suggested Bid", ""))
            
            if approval_status == "REQUIRES_REVIEW":
                if kw_id not in human_decisions:
                    rejected_count += 1
                    continue
                
                human_record = human_decisions[kw_id]
                if human_record["status"] == "REJECTED":
                    rejected_count += 1
                    continue
                    
                human_count += 1
                if human_record["human_bid"] != "":
                    final_bid = human_record["human_bid"]
                    # Nếu User set một Bid mới thay vì Pause
                    if final_action == "Pause" and final_bid != "" and final_bid != 0:
                        final_action = "Update Bid"
                    
            elif approval_status == "AUTO_APPROVED":
                auto_count += 1
            else:
                continue
                
            row_dict = {col: "" for col in AMAZON_TEMPLATE_COLUMNS}
            row_dict['Product'] = "Sponsored Products"
            row_dict['Entity'] = "Keyword"
            
            if final_action == "Pause":
                row_dict['Operation'] = "Update"
                row_dict['State'] = "Paused"
            else:
                row_dict['Operation'] = "Update"
                row_dict['Bid'] = final_bid
                
            row_dict['Campaign Name'] = kw.get('Campaign Name', '')
            row_dict['Campaign ID'] = kw.get('Campaign ID', '')
            row_dict['Ad Group ID'] = kw.get('Ad Group ID', '')
            row_dict['Keyword ID'] = kw_id
            row_dict['Keyword Text'] = kw.get('Keyword Text', '')
            row_dict['Match Type'] = kw.get('Match Type', '')
            
            upload_rows.append(row_dict)
            
    if not upload_rows:
        print("  🤷‍♂️ Không có bất kỳ thay đổi nào được duyệt để upload.")
        return
        
    df_out = pd.DataFrame(upload_rows, columns=AMAZON_TEMPLATE_COLUMNS)
    current_date = datetime.now().strftime("%d%m%Y")
    bulk_out = os.path.join(phase5_output_dir, f"Amazon_Upload_Ready_{current_date}.xlsx")
    
    try:
        with pd.ExcelWriter(bulk_out, engine='openpyxl') as writer:
            df_out.to_excel(writer, index=False, sheet_name='Sponsored Products Campaigns')
        print(f"\n  ✅ TỔNG KẾT:")
        print(f"    - Máy tự động duyệt (Auto): {auto_count} keywords")
        print(f"    - Con người duyệt (Human): {human_count} keywords")
        print(f"    - Bị từ chối/bỏ qua (Rejected): {rejected_count} keywords")
        print(f"  🚀 File Upload cuối cùng đã sẵn sàng tại: {bulk_out}")
    except Exception as e:
        print(f"❌ Lỗi khi xuất Excel: {e}")
        
if __name__ == "__main__":
    main()
