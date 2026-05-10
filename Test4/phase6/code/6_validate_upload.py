import os
import glob
import json
import pandas as pd
from datetime import datetime
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 30 cột tiêu chuẩn của Amazon (giống Phase 5)
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
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  ❌ Lỗi khi đọc file JSON {filepath}: {e}")
        return []

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    phase_bo_sung_dir = os.path.join(base_dir, "phase_bo_sung", "output")
    phase5_output_dir = os.path.join(base_dir, "phase5", "output")
    phase6_output_dir = os.path.join(base_dir, "phase6", "output")
    
    os.makedirs(phase6_output_dir, exist_ok=True)
    
    print("=" * 60)
    print("  PHASE 6: KIỂM DUYỆT VÀ XÁC THỰC ID (HẢI QUAN)")
    print("=" * 60)
    
    # 1. Tìm file upload mới nhất từ Phase 5
    upload_files = glob.glob(os.path.join(phase5_output_dir, "Amazon_Upload_Ready_*.xlsx"))
    if not upload_files:
        print("  ❌ Không tìm thấy file upload nào ở Phase 5.")
        return
    
    # Lấy file có ngày mới nhất (dựa vào tên hoặc thời gian tạo)
    latest_upload_file = max(upload_files, key=os.path.getctime)
    print(f"  🔍 Đang kiểm tra file: {os.path.basename(latest_upload_file)}")
    
    try:
        df_upload = pd.read_excel(latest_upload_file)
    except Exception as e:
        print(f"  ❌ Không thể đọc file Excel: {e}")
        return

    # 2. Xây dựng Bản đồ ID (Reference ID Maps) từ phase_bo_sung
    print("  📚 Đang nạp dữ liệu gốc để đối chiếu ID...")
    id_ref_map = {} # Key: (Entity, ID) -> {Parent IDs}
    
    # Các file cần quét ID
    json_targets = [
        "Sponsored_Products_Campaigns.json",
        "Sponsored_Brands_Campaigns.json",
        "SB_Multi_Ad_Group_Campaigns.json"
    ]
    
    for filename in json_targets:
        fpath = os.path.join(phase_bo_sung_dir, filename)
        if os.path.exists(fpath):
            data = load_json(fpath)
            for item in data:
                entity = item.get("Entity")
                camp_id = str(item.get("Campaign ID", "")).replace(".0", "")
                ag_id = str(item.get("Ad Group ID", "")).replace(".0", "")
                
                if entity == "Keyword":
                    kw_id = str(item.get("Keyword ID", "")).replace(".0", "")
                    if kw_id:
                        id_ref_map[("Keyword", kw_id)] = {"Campaign ID": camp_id, "Ad Group ID": ag_id}
                elif entity == "Product Targeting":
                    pt_id = str(item.get("Product Targeting ID", "")).replace(".0", "")
                    if pt_id:
                        id_ref_map[("Product Targeting", pt_id)] = {"Campaign ID": camp_id, "Ad Group ID": ag_id}
                elif entity == "Ad" or entity == "Product Ad":
                    ad_id = str(item.get("Ad ID", "")).replace(".0", "")
                    if ad_id:
                        id_ref_map[("Ad", ad_id)] = {"Campaign ID": camp_id, "Ad Group ID": ag_id}

    print(f"  ✅ Đã nạp {len(id_ref_map)} thực thể gốc.")

    # 3. Tiến hành Validation
    valid_rows = []
    error_rows = []
    
    # Kiểm tra Header
    missing_cols = [c for c in AMAZON_TEMPLATE_COLUMNS if c not in df_upload.columns]
    if missing_cols:
        print(f"  ⚠️ Cảnh báo: File thiếu các cột: {missing_cols}")

    for index, row in df_upload.iterrows():
        errors = []
        entity = str(row.get("Entity", ""))
        operation = str(row.get("Operation", ""))
        
        # Kiểm tra Operation
        if operation != "Update":
            errors.append(f"Operation '{operation}' không hợp lệ (phải là Update)")
            
        # Kiểm tra ID
        if entity == "Keyword":
            kw_id = str(row.get("Keyword ID", "")).replace(".0", "")
            if not kw_id:
                errors.append("Thiếu Keyword ID")
            elif ("Keyword", kw_id) not in id_ref_map:
                errors.append(f"Keyword ID {kw_id} không tồn tại trong dữ liệu gốc")
            else:
                ref = id_ref_map[("Keyword", kw_id)]
                if str(row.get("Campaign ID", "")).replace(".0", "") != ref["Campaign ID"]:
                    errors.append(f"Campaign ID không khớp với dữ liệu gốc")
                if str(row.get("Ad Group ID", "")).replace(".0", "") != ref["Ad Group ID"]:
                    errors.append(f"Ad Group ID không khớp với dữ liệu gốc")
        
        # Kiểm tra Bid (nếu có)
        bid = row.get("Bid")
        if pd.notna(bid) and bid != "":
            try:
                f_bid = float(bid)
                if f_bid < 0.02:
                    errors.append(f"Bid {f_bid} thấp hơn mức tối thiểu 0.02")
            except:
                errors.append(f"Bid '{bid}' không phải là số hợp lệ")
        
        # Phân loại row
        if errors:
            row_err = row.copy()
            row_err["Validation Errors"] = "; ".join(errors)
            error_rows.append(row_err)
        else:
            valid_rows.append(row)

    # 4. Xuất file kết quả
    current_date = datetime.now().strftime("%d%m%Y")
    
    # File sạch
    if valid_rows:
        df_valid = pd.DataFrame(valid_rows)
        # Đảm bảo đúng thứ tự cột
        df_valid = df_valid.reindex(columns=AMAZON_TEMPLATE_COLUMNS)
        valid_out = os.path.join(phase6_output_dir, f"Amazon_Upload_Verified_{current_date}.xlsx")
        df_valid.to_excel(valid_out, index=False, sheet_name='Sponsored Products Campaigns')
        print(f"  ✅ Đã xuất {len(valid_rows)} dòng hợp lệ tại: {os.path.basename(valid_out)}")
    else:
        print("  ⚠️ Không có dòng nào hợp lệ để xuất file upload.")

    # File lỗi
    if error_rows:
        df_error = pd.DataFrame(error_rows)
        error_out = os.path.join(phase6_output_dir, f"Validation_Errors_{current_date}.xlsx")
        df_error.to_excel(error_out, index=False)
        print(f"  ❌ Đã phát hiện {len(error_rows)} dòng lỗi. Chi tiết tại: {os.path.basename(error_out)}")
    else:
        print("  🎉 Tuyệt vời! Không phát hiện lỗi ID hay định dạng nào.")

    print("\n  🚀 Hoàn thành Phase 6.")

if __name__ == "__main__":
    main()
