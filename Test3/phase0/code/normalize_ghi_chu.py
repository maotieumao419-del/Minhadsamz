# =============================================================================
# Phase 0: Chuẩn hóa dữ liệu từ trường "Ghi chú" (Notes)
# Input: Các file JSON từ phase_bo_sung/output (trừ Listing.json, Portfolio_ID.json)
# Output: Các file JSON chuẩn hóa với 3 trường mới: Match Type, Bid, Placement
# =============================================================================

import json
import os
import re
import glob


# --- Hàm xử lý loại bỏ ký tự xuống dòng \n trong toàn bộ chuỗi ---
def strip_newlines(text):
    """Thay thế tất cả ký tự xuống dòng \\n bằng khoảng trắng, rồi loại bỏ khoảng trắng thừa."""
    if isinstance(text, str):
        # Thay thế \n bằng khoảng trắng (không phải chuỗi rỗng) để tránh dính các token
        # Ví dụ: "0.6\n30T" → "0.6 30T" thay vì "0.630T"
        return text.replace("\n", " ").strip()
    # Nếu không phải chuỗi (ví dụ None), trả về nguyên bản
    return text


# --- Hàm trích xuất Match Type từ ghi chú ---
def extract_match_type(ghi_chu):
    """
    Tìm match type (exact, phrase, broad) trong chuỗi ghi chú.
    Tìm kiếm không phân biệt hoa/thường.
    Trả về chuỗi viết thường: 'exact', 'phrase', hoặc 'broad'.
    Nếu không tìm thấy, trả về None.
    """
    # Chuyển ghi chú thành chữ thường để so sánh
    lower = ghi_chu.lower()

    # Kiểm tra lần lượt từng match type
    if "exact" in lower:
        return "exact"
    elif "phrase" in lower:
        return "phrase"
    elif "broad" in lower:
        return "broad"

    # Không tìm thấy match type nào
    return None


# --- Hàm trích xuất Bid (giá thầu) từ ghi chú ---
def extract_bid(ghi_chu, match_type):
    """
    Tìm giá trị Bid (số thập phân) trong ghi chú.
    
    Chiến lược tìm kiếm:
    1. Tìm số ngay sau từ match_type (ví dụ: "exact 0.6" → 0.6)
    2. Nếu không tìm thấy theo cách 1, tìm số ngay sau từ "bid"
    3. Nếu vẫn không, tìm số thập phân đầu tiên trong chuỗi
    
    Trả về giá trị float hoặc None nếu không tìm thấy.
    """
    # Cách 1: Tìm số ngay sau match_type
    # Pattern: match_type + (có thể có dấu phẩy, gạch dưới, khoảng trắng) + số thập phân
    if match_type:
        pattern = re.compile(
            rf'{match_type}[_,\s]*(\d+\.?\d*)',
            re.IGNORECASE  # Không phân biệt hoa/thường
        )
        m = pattern.search(ghi_chu)
        if m:
            return float(m.group(1))

    # Cách 2: Tìm số ngay sau từ "bid"
    bid_pattern = re.compile(r'bid\s*(\d+\.?\d*)', re.IGNORECASE)
    m = bid_pattern.search(ghi_chu)
    if m:
        return float(m.group(1))

    # Cách 3: Tìm số thập phân đầu tiên (dạng 0.xx) trong chuỗi
    fallback = re.compile(r'(\d+\.\d+)')
    m = fallback.search(ghi_chu)
    if m:
        return float(m.group(1))

    # Không tìm thấy Bid
    return None


# --- Hàm trích xuất và chuẩn hóa Placement ---
def extract_placement(ghi_chu):
    """
    Trích xuất và chuẩn hóa Placement từ ghi chú.
    
    Các trường hợp có thể gặp:
    - "30TRP" hoặc "30TPR"    → "30T30R30P" (tất cả T, R, P cùng giá trị)
    - "30trp" hoặc "30tpr"    → "30T30R30P" (chữ thường cũng nhận)
    - "30T, 30R, 30P"         → "30T30R30P" (đã tách sẵn từng chỉ số)
    - "50T"                   → "50T0R0P"   (thiếu R và P → mặc định 0)
    - "30T, 30R"              → "30T30R0P"  (thiếu P → mặc định 0)
    
    Trả về chuỗi dạng "XXT YYR ZZP" hoặc None nếu không tìm thấy.
    """

    # --- Trường hợp 1: Tách riêng từng chỉ số T, R, P ---
    # Tìm tất cả các cặp (số + T/R/P) trong chuỗi, ví dụ: "30T, 30R, 30P"
    individual = re.findall(r'(\d+)\s*([TtRrPp])\b', ghi_chu)

    if individual:
        # Khởi tạo giá trị mặc định cho T, R, P là 0
        t_val = 0
        r_val = 0
        p_val = 0

        # Duyệt qua từng cặp (số, chữ cái) tìm được
        for val, letter in individual:
            letter_upper = letter.upper()
            if letter_upper == 'T':
                t_val = int(val)
            elif letter_upper == 'R':
                r_val = int(val)
            elif letter_upper == 'P':
                p_val = int(val)

        return f"{t_val}T{r_val}R{p_val}P"

    # --- Trường hợp 2: Dạng gộp "30TRP" hoặc "30TPR" ---
    # Pattern: số + (TRP hoặc TPR), không phân biệt hoa/thường
    combined = re.search(r'(\d+)\s*(TRP|TPR|trp|tpr)', ghi_chu, re.IGNORECASE)
    if combined:
        val = int(combined.group(1))
        # Tất cả T, R, P đều cùng giá trị
        return f"{val}T{val}R{val}P"

    # --- Không tìm thấy Placement ---
    return None


# --- Hàm xử lý chuẩn hóa một bản ghi (record) duy nhất ---
def normalize_record(record):
    """
    Chuẩn hóa một bản ghi JSON:
    1. Loại bỏ \\n trong tất cả các trường chuỗi
    2. Phân tích trường "Ghi chú" → tách ra Match Type, Bid, Placement
    3. Thêm 3 trường mới vào bản ghi
    """
    # Bước 1: Loại bỏ \n trong mọi trường có giá trị chuỗi
    cleaned = {}
    for key, value in record.items():
        cleaned[key] = strip_newlines(value)

    # Bước 2: Lấy giá trị "Ghi chú" đã làm sạch
    ghi_chu = cleaned.get("Ghi chú")

    # Nếu không có ghi chú (None hoặc rỗng), trả về bản ghi với giá trị mặc định
    if not ghi_chu:
        cleaned["Match Type"] = None
        cleaned["Bid"] = None
        cleaned["Placement"] = None
        return cleaned

    # Bước 3: Trích xuất Match Type
    match_type = extract_match_type(ghi_chu)
    cleaned["Match Type"] = match_type

    # Bước 4: Trích xuất Bid (dựa vào match_type để tìm chính xác hơn)
    bid = extract_bid(ghi_chu, match_type)
    cleaned["Bid"] = bid

    # Bước 5: Trích xuất và chuẩn hóa Placement
    placement = extract_placement(ghi_chu)
    cleaned["Placement"] = placement

    return cleaned


# --- Hàm xử lý toàn bộ một file JSON ---
def process_file(input_path, output_path):
    """
    Đọc file JSON input, chuẩn hóa từng bản ghi, ghi kết quả ra file output.
    
    Args:
        input_path: Đường dẫn file JSON đầu vào
        output_path: Đường dẫn file JSON đầu ra
    """
    # Đọc file JSON đầu vào với encoding UTF-8
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # In thông tin file đang xử lý
    print(f"  📄 Đang xử lý: {os.path.basename(input_path)} ({len(data)} bản ghi)")

    # Chuẩn hóa từng bản ghi trong danh sách
    normalized = []
    for record in data:
        normalized.append(normalize_record(record))

    # Ghi kết quả ra file JSON đầu ra (đảm bảo Unicode và indent đẹp)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=4)

    print(f"  ✅ Đã lưu: {os.path.basename(output_path)}")

    return normalized


# --- Hàm chính: Điều phối toàn bộ quy trình ---
def main():
    """
    Quy trình chính:
    1. Xác định thư mục input (phase_bo_sung/output) và output (phase0/output)
    2. Liệt kê tất cả file JSON, loại trừ Listing.json và Portfolio_ID.json
    3. Xử lý từng file và lưu kết quả
    4. In thống kê tổng hợp
    """
    # Xác định thư mục gốc của project (Test3)
    # Từ phase0/code/ → lùi 2 cấp để về Test3/
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Thư mục input: lấy output của phase_bo_sung
    input_dir = os.path.join(base_dir, "phase_bo_sung", "output")

    # Thư mục output: lưu vào phase0/output
    output_dir = os.path.join(base_dir, "phase0", "output")

    # Tạo thư mục output nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)

    # Danh sách các file cần bỏ qua (không xử lý)
    skip_files = {"Listing.json", "Portfolio_ID.json"}

    # Tìm tất cả file .json trong thư mục input
    json_files = glob.glob(os.path.join(input_dir, "*.json"))

    # Lọc bỏ các file trong danh sách skip
    json_files = [
        f for f in json_files
        if os.path.basename(f) not in skip_files
    ]

    # Kiểm tra xem có file nào để xử lý không
    if not json_files:
        print("⚠️  Không tìm thấy file JSON nào để xử lý!")
        return

    print(f"🚀 Phase 0: Chuẩn hóa dữ liệu Ghi chú")
    print(f"   Input:  {input_dir}")
    print(f"   Output: {output_dir}")
    print(f"   Số file cần xử lý: {len(json_files)}")
    print(f"   Bỏ qua: {', '.join(skip_files)}")
    print("-" * 60)

    # Biến đếm tổng số bản ghi đã xử lý
    total_records = 0

    # Xử lý từng file JSON
    for file_path in sorted(json_files):
        # Tạo đường dẫn output (cùng tên file)
        output_path = os.path.join(output_dir, os.path.basename(file_path))

        # Xử lý file và nhận kết quả
        result = process_file(file_path, output_path)

        # Cộng dồn số bản ghi
        total_records += len(result)

    # In thống kê tổng hợp
    print("-" * 60)
    print(f"🎉 Hoàn thành! Tổng cộng: {len(json_files)} file, {total_records} bản ghi")


# --- Entry point: Chạy hàm main khi script được thực thi trực tiếp ---
if __name__ == "__main__":
    main()
