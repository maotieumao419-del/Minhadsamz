# =============================================================================
# Phase 0: Chuẩn hóa + Tách dữ liệu Sponsored Products Campaigns theo Entity
# Input:  Sponsored_Products_Campaigns.json từ phase_bo_sung/output
# Output: Các file JSON riêng biệt theo Entity, đã chuẩn hóa tại phase0/output
#
# Công việc:
#   1. Xóa 10 cột rác (6 cột trùng lặp Informational + 4 cột rỗng 100%)
#   2. Ép kiểu dữ liệu an toàn (ID → String, Bid → Float, Clicks → Int)
#   3. Tách riêng từng loại Entity ra file JSON riêng
#   4. Mỗi file chỉ giữ lại các cột CÓ Ý NGHĨA cho Entity đó
# =============================================================================

import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


# --- Danh sách 10 cột cần XÓA (trùng lặp / rỗng 100%) ---
COLUMNS_TO_REMOVE = {
    "Campaign Name (Informational only)",
    "Ad Group Name (Informational only)",
    "Campaign State (Informational only)",
    "Ad Group State (Informational only)",
    "Ad Group Default Bid (Informational only)",
    "Resolved Product Targeting Expression (Informational only)",
    "End Date",
    "Native Language Keyword",
    "Native Language Locale",
    "Reason for Ineligibility (Informational only)",
}


# --- Định nghĩa cột giữ lại + kiểu dữ liệu cho từng Entity ---
ENTITY_SCHEMA = {
    "Campaign": {
        "keep_cols": [
            "Campaign ID", "Campaign Name", "State", "Daily Budget",
            "Bidding Strategy", "Portfolio ID", "Start Date", "Targeting Type",
            "Portfolio Name (Informational only)",
            "Impressions", "Clicks", "Spend", "Sales", "Orders", "Units",
            "Click-through Rate", "Conversion Rate", "ACOS", "CPC", "ROAS"
        ],
        "output_file": "campaigns.json"
    },

    "Keyword": {
        "keep_cols": [
            "Campaign ID", "Ad Group ID", "Keyword ID",
            "Keyword Text", "Match Type", "Bid", "State",
            "Impressions", "Clicks", "Spend", "Sales", "Orders", "Units",
            "Click-through Rate", "Conversion Rate", "ACOS", "CPC", "ROAS"
        ],
        "output_file": "keywords.json"
    },

    "Product Targeting": {
        "keep_cols": [
            "Campaign ID", "Ad Group ID", "Product Targeting ID",
            "Product Targeting Expression", "Bid", "State",
            "Impressions", "Clicks", "Spend", "Sales", "Orders", "Units",
            "Click-through Rate", "Conversion Rate", "ACOS", "CPC", "ROAS"
        ],
        "output_file": "product_targeting.json"
    },

    "Bidding Adjustment": {
        "keep_cols": [
            "Campaign ID", "Placement", "Percentage"
        ],
        "output_file": "bidding_adjustments.json"
    },

    "Product Ad": {
        "keep_cols": [
            "Campaign ID", "Ad Group ID", "Ad ID", "SKU", "State",
            "ASIN (Informational only)", "Eligibility Status (Informational only)"
        ],
        "output_file": "product_ads.json"
    },

    "Ad Group": {
        "keep_cols": [
            "Campaign ID", "Ad Group ID", "Ad Group Name",
            "Ad Group Default Bid", "State"
        ],
        "output_file": "ad_groups.json"
    }
}


# --- Quy tắc ép kiểu theo tên cột ---
FLOAT_COLUMNS = {
    "Daily Budget", "Ad Group Default Bid", "Bid", "Percentage",
    "Shopper Cohort Percentage",
    "Click-through Rate", "Spend", "Sales",
    "Conversion Rate", "ACOS", "CPC", "ROAS",
}

INT_COLUMNS = {
    "Impressions", "Clicks", "Orders", "Units",
}


def safe_str(val):
    """Chuyển giá trị sang String sạch. Xử lý None, NaN, số float dạng ID."""
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("none", "nan"):
        return ""
    try:
        f = float(s)
        if f == int(f) and "." in s:
            return str(int(f))
    except (ValueError, TypeError):
        pass
    return s


def safe_float(val):
    """Chuyển giá trị sang Float an toàn."""
    if val is None:
        return 0.0
    s = str(val).strip()
    if s.lower() in ("none", "nan", ""):
        return 0.0
    try:
        return round(float(s), 4)
    except (ValueError, TypeError):
        return 0.0


def safe_int(val):
    """Chuyển giá trị sang Integer an toàn."""
    if val is None:
        return 0
    s = str(val).strip()
    if s.lower() in ("none", "nan", ""):
        return 0
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def cast_value(col, val):
    """Ép kiểu giá trị dựa trên tên cột."""
    if col in FLOAT_COLUMNS:
        return safe_float(val)
    elif col in INT_COLUMNS:
        return safe_int(val)
    else:
        return safe_str(val)


def normalize_and_trim(record, keep_cols):
    """Chuẩn hóa bản ghi: chỉ giữ cột cần thiết + ép kiểu."""
    cleaned = {}
    for col in keep_cols:
        raw_val = record.get(col)
        cleaned[col] = cast_value(col, raw_val)
    return cleaned


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_file = os.path.join(base_dir, "phase_bo_sung", "output", "Sponsored_Products_Campaigns.json")
    output_dir = os.path.join(base_dir, "phase0", "output")

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  PHASE 0: Chuẩn hóa + Tách Entity")
    print("=" * 60)
    print(f"  Input:  {input_file}")
    print(f"  Output: {output_dir}")
    print()

    if not os.path.exists(input_file):
        print(f"❌ Không tìm thấy file: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        all_records = json.load(f)

    original_cols = len(all_records[0]) if all_records else 0
    print(f"  Đầu vào: {len(all_records)} dòng, {original_cols} cột")
    print(f"  Xóa {len(COLUMNS_TO_REMOVE)} cột rác (trùng lặp / rỗng 100%)")
    print("-" * 60)

    # 1. Phân loại (Bucketize) bản ghi theo Entity
    # Dữ liệu từ file gộp chứa tất cả các loại (Campaign, Keyword, Bidding Adjustment...)
    # Ở đây chúng ta duyệt qua từng dòng và thả chúng vào các "xô" (buckets) riêng biệt dựa trên cột 'Entity'.
    entity_buckets = {}
    skipped = 0

    for record in all_records:
        entity = str(record.get("Entity", "")).strip()
        if entity in ENTITY_SCHEMA:
            if entity not in entity_buckets:
                entity_buckets[entity] = []
            entity_buckets[entity].append(record)
        else:
            # Bỏ qua các Entity không nằm trong thiết kế (ví dụ: Negative Keyword)
            skipped += 1

    # 2. Chuẩn hóa và xuất từng Entity ra các file riêng
    # Quá trình này giúp gọt bỏ các cột không thuộc về Entity đó (Trim the fat)
    # Đồng thời ép kiểu dữ liệu an toàn cho từng cột để tránh lỗi định dạng sau này.
    for entity_name, schema in ENTITY_SCHEMA.items():
        records = entity_buckets.get(entity_name, [])
        if not records:
            print(f"  ⏭ Bỏ qua: {entity_name} (0 dòng)")
            continue

        keep_cols = schema["keep_cols"]
        
        # Áp dụng hàm normalize_and_trim cho từng bản ghi trong bucket
        normalized = [normalize_and_trim(r, keep_cols) for r in records]

        # Xuất dữ liệu đã chuẩn hóa ra file JSON tương ứng (ví dụ: campaigns.json, keywords.json)
        output_path = os.path.join(output_dir, schema["output_file"])
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=4, ensure_ascii=False)

        print(f"  ✅ {entity_name:25s} → {schema['output_file']:30s} "
              f"({len(normalized):>4} dòng, {len(keep_cols)} cột)")

    if skipped > 0:
        print(f"\n  ⚠ Bỏ qua {skipped} dòng (Negative Keyword, Campaign Negative Keyword)")

    print("-" * 60)
    print("🎉 Phase 0 hoàn thành!")


if __name__ == "__main__":
    main()
