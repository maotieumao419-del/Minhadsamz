import os
import re
import json
import glob
import sys
import pandas as pd
from datetime import datetime
import warnings

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Tắt cảnh báo từ thư viện openpyxl khi làm việc với Excel
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# =============================================================================
# CẤU HÌNH ĐƯỜNG DẪN (PATHS)
# =============================================================================
# Thư mục chứa các file JSON đầu vào (tự động đọc toàn bộ kết quả của Phase 3)
INPUT_DIR = r"f:\Minhpython\Test3\phase3\output"

# File Listing.json dùng để tra cứu Portfolio ID tương ứng với từng SKU
LISTING_JSON = r"f:\Minhpython\Test3\phase_bo_sung\output\Listing.json"

# Thư mục xuất các file Excel Bulk Operations
OUTPUT_DIR = r"f:\Minhpython\Test3\phase4\output"

# =============================================================================
# CÀI ĐẶT MẶC ĐỊNH (SETTINGS)
# =============================================================================
DEFAULT_BUDGET = 5.0 # Ngân sách hàng ngày mặc định
DATE_SUFFIX = datetime.now().strftime("%Y%m%d") # Định dạng ngày YYYYMMDD để điền vào Start Date

# Danh sách đầy đủ các tiêu đề cột theo mẫu Template Bulk Operations của Amazon
AMAZON_TEMPLATE_COLUMNS = [
    "Product", "Entity", "Operation", "Campaign Id", "Ad Group Id", "Portfolio Id",
    "Ad Id", "Keyword Id", "Product Targeting Id", "Campaign Name", "Ad Group Name",
    "Start Date", "End Date", "Targeting Type", "State", "Daily Budget", "SKU", "ASIN",
    "Eligibility Status", "Reasons for Ineligibility", "Ad Group Default Bid",
    "Bid", "Keyword Text", "Match Type", "Bidding Strategy", "Placement", "Percentage",
    "Product Targeting Expression"
]

# =============================================================================
# CÁC HÀM TIỆN ÍCH (UTILITY FUNCTIONS)
# =============================================================================

def build_sku_portfolio_map_from_json(listing_file: str) -> dict[str, str]:
    """
    Đọc file Listing.json và tạo một từ điển (dictionary) để tra cứu:
    Kết quả: { 'SKU_NAME': 'PORTFOLIO_ID' }
    """
    if not os.path.exists(listing_file):
        print(f"[WARN] Không tìm thấy file Listing tại: {listing_file}")
        return {}
    
    try:
        with open(listing_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        mapping = {}
        for item in data:
            # Loại bỏ ký tự xuống dòng (\n) trong SKU nếu có và cắt khoảng trắng thừa
            sku = str(item.get("SKU", "")).replace("\n", "").strip()
            pid = str(item.get("Portfolio Id", "")).strip()
            # Chỉ lưu nếu có SKU và Portfolio ID hợp lệ
            if sku and pid and pid.lower() != "nan" and pid.lower() != "none":
                mapping[sku] = pid
        return mapping
    except Exception as e:
        print(f"[ERROR] Lỗi đọc file Listing.json: {e}")
        return {}

def parse_placement_trp(placement_str: str) -> tuple[int, int, int]:
    """
    Phân tích chuỗi Placement đã chuẩn hóa từ Phase 0 (ví dụ: "30T20R10P")
    thành 3 giá trị riêng biệt cho Top, Rest of Search, và Product Page.
    
    Trả về tuple (T, R, P) dạng int.
    Nếu không parse được, trả về (0, 0, 0).
    """
    if not placement_str:
        return (0, 0, 0)
    
    # Tìm từng giá trị T, R, P trong chuỗi dạng "30T20R10P"
    t_match = re.search(r'(\d+)T', placement_str)
    r_match = re.search(r'(\d+)R', placement_str)
    p_match = re.search(r'(\d+)P', placement_str)
    
    t_val = int(t_match.group(1)) if t_match else 0
    r_val = int(r_match.group(1)) if r_match else 0
    p_val = int(p_match.group(1)) if p_match else 0
    
    return (t_val, r_val, p_val)

def build_7_row_block(
    campaign_name: str, target_sku: str, keyword_text: str, match_type: str,
    base_bid: float, pct_top: int, pct_rest: int, pct_product: int, portfolio_id: str,
    default_budget: float = DEFAULT_BUDGET, date_suffix: str = DATE_SUFFIX
) -> list[dict]:
    """
    Tạo một khối gồm 7 dòng dữ liệu chuẩn Amazon cho mỗi từ khóa:
    1. Campaign, 2-4. Bidding Adjustments (Top/Product/Rest), 5. Ad Group, 6. Product Ad, 7. Keyword
    """
    ad_group_id_str = campaign_name # Sử dụng tên Campaign làm ID cho Ad Group
    ad_group_name_str = keyword_text # Sử dụng từ khóa làm tên cho Ad Group

    def base_row() -> dict:
        """Tạo cấu trúc một dòng trống với các thông tin cố định ban đầu"""
        r = {col: "" for col in AMAZON_TEMPLATE_COLUMNS}
        r["Product"] = "Sponsored Products"
        r["Operation"] = "Create"
        r["Campaign Id"] = campaign_name
        r["State"] = "enabled"
        return r

    # Dòng 1: Thực thể Campaign (Chiến dịch)
    r1 = base_row()
    r1["Entity"] = "Campaign"
    r1["Campaign Name"] = campaign_name
    r1["Start Date"] = date_suffix
    r1["Portfolio Id"] = portfolio_id
    r1["Targeting Type"] = "MANUAL"
    r1["Daily Budget"] = default_budget
    r1["Bidding Strategy"] = "Dynamic bids - down only"

    # Dòng 2, 3, 4: Các dòng điều chỉnh giá thầu theo vị trí hiển thị (Bidding Adjustments)
    # Mỗi vị trí nhận giá trị % riêng biệt từ Placement đã chuẩn hóa (ví dụ: 30T20R10P)
    r2 = base_row()
    r2["Entity"] = "Bidding Adjustment"
    r2["Placement"] = "placement top"
    r2["Percentage"] = pct_top          # Giá trị T (Top of Search)

    r3 = base_row()
    r3["Entity"] = "Bidding Adjustment"
    r3["Placement"] = "placementProductPage"
    r3["Percentage"] = pct_product      # Giá trị P (Product Page)

    r4 = base_row()
    r4["Entity"] = "Bidding Adjustment"
    r4["Placement"] = "placementRestOfSearch"
    r4["Percentage"] = pct_rest         # Giá trị R (Rest of Search)

    # Dòng 5: Thực thể Ad Group (Nhóm quảng cáo)
    r5 = base_row()
    r5["Entity"] = "Ad Group"
    r5["Ad Group Id"] = ad_group_id_str
    r5["Ad Group Name"] = ad_group_name_str
    r5["Ad Group Default Bid"] = base_bid

    # Dòng 6: Thực thể Product Ad (Quảng cáo sản phẩm - gắn SKU vào nhóm)
    r6 = base_row()
    r6["Entity"] = "Product Ad"
    r6["Ad Group Id"] = ad_group_id_str
    r6["SKU"] = target_sku

    # Dòng 7: Thực thể Keyword (Từ khóa thực tế)
    r7 = base_row()
    r7["Entity"] = "Keyword"
    r7["Ad Group Id"] = ad_group_id_str
    r7["Keyword Text"] = keyword_text
    r7["Match Type"] = match_type
    r7["Bid"] = base_bid

    return [r1, r2, r3, r4, r5, r6, r7]

def export_excel(target_sku: str, rows: list[dict], output_dir: str):
    """Xuất danh sách các dòng dữ liệu ra file Excel với định dạng chuyên nghiệp"""
    os.makedirs(output_dir, exist_ok=True)
    # Loại bỏ các ký tự đặc biệt trong SKU để đặt tên file an toàn
    safe_sku = re.sub(r'[^\w\-]', '_', str(target_sku).strip()) or "UNKNOWN_SKU"
    filename = f"Bulk_Create_{safe_sku}.xlsx"
    out_path = os.path.join(output_dir, filename)

    # Chuyển đổi list các dictionary thành DataFrame của Pandas
    df_out = pd.DataFrame(rows, columns=AMAZON_TEMPLATE_COLUMNS).fillna("")

    # Sử dụng engine xlsxwriter để có quyền kiểm soát định dạng cột tốt hơn
    with pd.ExcelWriter(out_path, engine='xlsxwriter') as writer:
        sheet_name = 'Sponsored Products Campaigns' # Tên sheet bắt buộc của Amazon
        df_out.to_excel(writer, index=False, sheet_name=sheet_name)
        
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        # Định dạng quan trọng: ép tất cả các cột về định dạng Text (@) để tránh Excel tự đổi số (như Portfolio Id)
        text_fmt = workbook.add_format({'num_format': '@'})
        for col_idx in range(len(AMAZON_TEMPLATE_COLUMNS)):
            worksheet.set_column(col_idx, col_idx, 20, text_fmt)

    n_campaigns = len(rows) // 7
    print(f"\n[OK] Da xuat thanh cong: {out_path}")
    print(f"     SKU: {target_sku} | {n_campaigns} campaigns | {len(rows)} dong")

# =============================================================================
# QUY TRÌNH CHẠY CHÍNH (MAIN PIPELINE)
# =============================================================================
def main():
    print("=========================================================")
    print("  PHASE 4 - JSON TO BULK TEMPLATE EXPORT")
    print("=========================================================")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Xóa file Excel cũ trong output để tránh file cũ từ lần chạy trước
    old_xlsx = glob.glob(os.path.join(OUTPUT_DIR, "*.xlsx"))
    if old_xlsx:
        for old_f in old_xlsx:
            os.remove(old_f)
        print(f"🧹 Đã xóa {len(old_xlsx)} file Excel cũ trong Phase 4 Output.")
    
    json_files = glob.glob(os.path.join(INPUT_DIR, "*.json"))

    if not json_files:
        print(f"[ERROR] Không có file JSON nào trong: {INPUT_DIR}")
        return

    print(f"Bắt đầu xử lý {len(json_files)} file JSON...\n")

    # Xây dựng bảng tra cứu Portfolio ID một lần duy nhất
    sku_portfolio_map = build_sku_portfolio_map_from_json(LISTING_JSON)

    total_success = 0
    total_skipped = 0
    all_skipped_details = []  # Thu thập chi tiết tất cả campaigns bị bỏ qua

    for file_path in json_files:
        target_sku = os.path.splitext(os.path.basename(file_path))[0]
        print(f"➜ Đang xử lý SKU: {target_sku}")

        portfolio_id = sku_portfolio_map.get(target_sku, "")
        if not portfolio_id:
            print(f"   [WARN] Không tìm thấy Portfolio ID cho SKU '{target_sku}'. Gán mặc định.")
            portfolio_id = "NO_PORTFOLIO"
        else:
            print(f"   [OK] Portfolio ID: {portfolio_id}")

        # Đọc dữ liệu JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"   [ERROR] Lỗi đọc file JSON: {e}")
            continue

        all_rows = []
        skip_count = 0
        success_count = 0
        skipped_details = []  # Lưu chi tiết các campaign bị bỏ qua trong file này

        for item in data:
            campaign_name = str(item.get("Campaign Name", "")).strip()
            keyword_text = str(item.get("Target", "")).strip()
            stt = item.get("STT", "?")

            # --- Đọc dữ liệu đã chuẩn hóa từ Phase 0 ---
            match_type = item.get("Match Type")          # exact / phrase / broad
            base_bid = item.get("Bid")                    # Giá trị float (ví dụ: 0.6)
            placement_str = item.get("Placement")         # Chuỗi dạng "30T20R10P"

            # --- CHẨN ĐOÁN LỖI CHI TIẾT ---
            skip_reasons = []

            if not keyword_text:
                skip_reasons.append("Target rỗng")
            if not match_type:
                skip_reasons.append("Match Type rỗng (không có exact/phrase/broad)")
            if base_bid is None:
                skip_reasons.append("Bid rỗng (không tìm thấy giá thầu)")
            if not placement_str:
                skip_reasons.append("Placement rỗng (không có thông tin T/R/P)")

            # Nếu có lỗi → bỏ qua và ghi nhận
            if skip_reasons:
                skip_count += 1
                note_str = str(item.get("Ghi chú", "")).strip()
                detail = {
                    "SKU": target_sku, "STT": stt,
                    "Campaign": campaign_name,
                    "Target": keyword_text,
                    "Ghi chú": note_str,
                    "Lý do": skip_reasons
                }
                skipped_details.append(detail)
                # In cảnh báo ngay tại chỗ
                print(f"   [SKIP] STT {stt} | Lý do: {'; '.join(skip_reasons)}")
                continue

            # Phân tích Placement thành 3 giá trị riêng: T (Top), R (Rest), P (Product)
            pct_top, pct_rest, pct_product = parse_placement_trp(placement_str)

            block = build_7_row_block(
                campaign_name=campaign_name,
                target_sku=target_sku,
                keyword_text=keyword_text,
                match_type=match_type,
                base_bid=float(base_bid),
                pct_top=pct_top,
                pct_rest=pct_rest,
                pct_product=pct_product,
                portfolio_id=portfolio_id
            )
            all_rows.extend(block)
            success_count += 1

        if all_rows:
            export_excel(target_sku, all_rows, OUTPUT_DIR)
            total_success += success_count
        else:
            print("   [WARN] Không có dữ liệu hợp lệ để xuất Excel.")
        
        total_skipped += skip_count
        all_skipped_details.extend(skipped_details)

    # --- BẢNG TỔNG KẾT ---
    print("\n---------------------------------------------------------")
    print(f"Tổng files đã xử lý      : {len(json_files)}")
    print(f"Tổng campaigns thành công: {total_success}")
    print(f"Tổng campaigns bỏ qua    : {total_skipped}")

    # In chi tiết tất cả campaigns bị bỏ qua
    if all_skipped_details:
        print(f"\n{'='*65}")
        print(f" CHI TIẾT {total_skipped} CAMPAIGNS BỊ BỎ QUA")
        print(f"{'='*65}")
        current_sku = ""
        for d in all_skipped_details:
            if d["SKU"] != current_sku:
                current_sku = d["SKU"]
                sku_count = sum(1 for x in all_skipped_details if x["SKU"] == current_sku)
                print(f"\n  ▸ SKU: {current_sku} ({sku_count} campaigns bị bỏ qua)")
                print(f"  {'─'*60}")
            print(f"    [{d['STT']}] {d['Campaign'][:70]}")
            print(f"        Target : \"{d['Target'][:60]}\"")
            print(f"        Ghi chú: \"{d['Ghi chú'][:60]}{'...' if len(d['Ghi chú']) > 60 else ''}\"")
            for reason in d["Lý do"]:
                print(f"        ✘ {reason}")

    print(f"\n{'='*65}")

if __name__ == "__main__":
    main()
