import os
import glob
import pandas as pd
import sys
import warnings

# Tắt cảnh báo từ thư viện openpyxl khi làm việc với Excel
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Đảm bảo console xuất được tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# CẤU HÌNH ĐƯỜNG DẪN (PATHS)
# =============================================================================
# Thư mục lấy dữ liệu (Kết quả từ Phase 4)
INPUT_DIR = r"f:\Minhpython\Test3\phase4\output"

# Thư mục xuất file báo cáo lỗi (Log) của Phase 5
OUTPUT_DIR = r"f:\Minhpython\Test3\phase5\output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================================
# KỊCH BẢN KIỂM TRA (VALIDATION RULES)
# =============================================================================
def validate_excel_file(file_path):
    """
    Kiểm tra một file Excel dựa trên các quy tắc cốt lõi.
    Trả về danh sách (errors, warnings).
    """
    errors = []
    warnings_list = []
    
    # 1. Cố gắng đọc file bằng Pandas (Ép toàn bộ về kiểu Text để tránh mất số)
    try:
        df = pd.read_excel(file_path, sheet_name='Sponsored Products Campaigns', dtype=str)
    except Exception as e:
        return [f"Lỗi không thể đọc file hoặc sai tên Sheet (Phải là 'Sponsored Products Campaigns'): {e}"], []

    num_rows = len(df)
    
    # --- RULE 2: KIỂM TRA CẤU TRÚC KHỐI (BLOCK INTEGRITY) ---
    # Phải chia hết cho 7 (do một keyword tạo ra 7 dòng: Camp, 3xBid, AdGroup, Product, Keyword)
    if num_rows % 7 != 0:
        errors.append(f"Cấu trúc số dòng không hợp lệ: Tổng số dòng là {num_rows} (không chia hết cho 7). Khả năng cao thuật toán Phase 4 bị lỗi hoặc thiếu dữ liệu đầu vào.")

    # Lọc ra các dòng có Entity quan trọng để check
    campaigns = df[df['Entity'] == 'Campaign']
    keywords = df[df['Entity'] == 'Keyword']

    # --- RULE 1: KIỂM TRA TRÙNG LẶP CAMPAIGN ID (DUPLICATE ID CHECK) ---
    # Chỉ tính trên các dòng tạo Campaign mới
    campaign_ids = campaigns['Campaign Id'].dropna().tolist()
    seen = set()
    duplicates = set()
    for cid in campaign_ids:
        if cid in seen:
            duplicates.add(cid)
        else:
            seen.add(cid)
            
    if duplicates:
        errors.append(f"Phát hiện Duplicate Campaign Id: {', '.join(duplicates)}. Lỗi này chắc chắn sẽ bị Amazon từ chối.")

    # --- RULE 3: TRƯỜNG DỮ LIỆU BẮT BUỘC (REQUIRED FIELDS) ---
    # 3.1. Kiểm tra ở dòng Keyword
    for idx, row in keywords.iterrows():
        # idx của Pandas bắt đầu từ 0. Header là dòng 1 trong Excel, nên dữ liệu thực tế bắt đầu từ dòng 2
        excel_row_num = idx + 2 
        
        # Check Bid
        bid = str(row.get('Bid', '')).strip()
        if not bid or bid.lower() == 'nan':
            errors.append(f"Dòng {excel_row_num}: Bid trống ở Entity Keyword.")
            
        # Check Keyword Text
        kw_text = str(row.get('Keyword Text', '')).strip()
        if not kw_text or kw_text.lower() == 'nan':
            errors.append(f"Dòng {excel_row_num}: Keyword Text bị bỏ trống.")
            
        # Check Match Type
        match_type = str(row.get('Match Type', '')).strip().lower()
        if match_type not in ['exact', 'phrase', 'broad']:
            errors.append(f"Dòng {excel_row_num}: Match Type '{match_type}' không hợp lệ (phải là exact/phrase/broad).")

    # 3.2. Kiểm tra ở dòng Campaign
    for idx, row in campaigns.iterrows():
        excel_row_num = idx + 2
        portfolio_id = str(row.get('Portfolio Id', '')).strip()
        if not portfolio_id or portfolio_id.lower() == 'nan' or portfolio_id == 'no_portfolio':
            warnings_list.append(f"Dòng {excel_row_num}: Không có Portfolio Id hợp lệ ({portfolio_id}). Chiến dịch vẫn sẽ được tạo nhưng không nằm trong danh mục (Folder) nào.")

    # --- RULE 4: GIỚI HẠN KÝ TỰ (LENGTH LIMITS) ---
    for idx, row in campaigns.iterrows():
        excel_row_num = idx + 2
        camp_name = str(row.get('Campaign Name', '')).strip()
        if len(camp_name) > 128:
            errors.append(f"Dòng {excel_row_num}: Campaign Name vượt quá 128 ký tự (độ dài hiện tại: {len(camp_name)}). Amazon sẽ từ chối.")

    return errors, warnings_list

# =============================================================================
# QUY TRÌNH CHẠY CHÍNH (MAIN PROCESS)
# =============================================================================
def main():
    print("=========================================================")
    print("  PHASE 5 - EXCEL POST-FLIGHT VALIDATOR")
    print("=========================================================")
    
    excel_files = glob.glob(os.path.join(INPUT_DIR, "*.xlsx"))
    
    if not excel_files:
        print(f"[WARN] Không tìm thấy file Excel nào trong {INPUT_DIR} để kiểm tra.")
        return

    print(f"Bắt đầu kiểm tra {len(excel_files)} file Excel...\n")
    
    report_lines = []
    report_lines.append("="*60)
    report_lines.append(" BÁO CÁO KIỂM TRA LỖI EXCEL BULK OPERATIONS (PHASE 5)")
    report_lines.append("="*60 + "\n")
    
    total_files = len(excel_files)
    files_with_errors = 0
    files_with_warnings = 0
    
    for file_path in excel_files:
        filename = os.path.basename(file_path)
        print(f"➜ Đang quét: {filename}", end="")
        
        errors, warnings_list = validate_excel_file(file_path)
        
        if errors or warnings_list:
            if errors:
                print(" ❌ [LỖI]")
                files_with_errors += 1
            else:
                print(" ⚠️ [CẢNH BÁO]")
                files_with_warnings += 1
                
            report_lines.append(f"📄 File: {filename}")
            for err in errors:
                report_lines.append(f"   [LỖI] {err}")
            for wrn in warnings_list:
                report_lines.append(f"   [CẢNH BÁO] {wrn}")
            report_lines.append("-" * 40)
        else:
            print(" ✅ [PASS]")
            
    # Tổng kết in ra màn hình
    print("\n---------------------------------------------------------")
    print(f"Tổng số file đã check : {total_files}")
    print(f"File hoàn toàn hợp lệ : {total_files - files_with_errors - files_with_warnings} (Xanh 100%)")
    print(f"File có Cảnh báo      : {files_with_warnings}")
    print(f"File bị LỖI (Failed)  : {files_with_errors}")
    
    # Ghi báo cáo ra file text
    report_path = os.path.join(OUTPUT_DIR, "Validation_Report.txt")
    
    if files_with_errors == 0:
        report_lines.append("\n🎉 CHÚC MỪNG! TẤT CẢ CÁC FILE EXCEL ĐỀU HỢP LỆ VÀ SẴN SÀNG ĐỂ UPLOAD LÊN AMAZON.")
    else:
        report_lines.append(f"\n⚠️ TỔNG KẾT: CÓ {files_with_errors} FILE BỊ LỖI. VUI LÒNG KIỂM TRA LẠI DỮ LIỆU ĐẦU VÀO HOẶC CÁC PHASE TRƯỚC ĐÓ.")
        
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"\n Đã lưu chi tiết báo cáo tại: {report_path}")
    print("=========================================================")

if __name__ == "__main__":
    main()
