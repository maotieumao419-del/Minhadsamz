import os
import glob
import json
import pandas as pd
from data_prep import process_data
from sheet_overview import build_overview_sheet
from sheet_campaigns import build_campaigns_sheet
from sheet_keywords import build_keywords_sheet
from sheet_search_terms import build_search_terms_sheet
from data_time_series import process_time_series
from charts import add_sparkline_sheet, draw_campaign_sparklines
from sheet_deep_dive import build_deep_dive_sheet

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

def load_configs():
    with open(os.path.join(CONFIG_DIR, "Rule_Engine.json"), "r", encoding="utf-8") as f:
        rules = json.load(f)
    with open(os.path.join(CONFIG_DIR, "Season_Calendar.json"), "r", encoding="utf-8") as f:
        calendar = json.load(f)
    return rules, calendar

def main():
    print("Bat dau tao Dashboard...")
    rules, calendar = load_configs()
    
    import sys
    DB_DIR = os.path.join(os.path.dirname(BASE_DIR), "database", "code")
    sys.path.append(DB_DIR)
    from db_manager import ingest_bulk_to_db
    DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "database", "amazon_ads_history.db")
    
    input_files = glob.glob(os.path.join(INPUT_DIR, "*.xlsx"))
    meta_path = os.path.join(INPUT_DIR, "phase0_input_meta.json")
    
    days_duration = 14 # Default
    start_date = None
    end_date = None
    file_path = None
    
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            if meta.get("days_duration"):
                days_duration = meta["days_duration"]
            start_date = meta.get("start_date")
            end_date = meta.get("end_date")
            expected_file = os.path.join(INPUT_DIR, meta.get("filename", ""))
            if os.path.exists(expected_file):
                file_path = expected_file
                
    if not file_path:
        if not input_files:
            print("Khong tim thay file .xlsx nao trong thu muc input/")
            return
        file_path = input_files[0]
    
    print(f"Dang doc file: {os.path.basename(file_path)} (Khoang thoi gian: {days_duration} ngay)")
    
    # 1. Process Data
    df_camp, df_kw, df_st, today = process_data(file_path, calendar)
    
    # 1.5 Ingest Bulk Data vào Database (chia đều số liệu ra các ngày)
    if start_date and end_date:
        ingest_bulk_to_db(DB_PATH, df_camp, start_date, end_date, days_duration)
        from datetime import datetime
        today = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    df_ts, df_ts_agg = process_time_series(df_camp, today=today, days=days_duration)

    # 2. Setup Excel Writer
    out_file = os.path.join(OUTPUT_DIR, f"Amazon_Ads_Dashboard_{today.strftime('%Y%m%d_%H%M%S')}.xlsx")
    writer = pd.ExcelWriter(out_file, engine='xlsxwriter')
    workbook = writer.book

    # 3. Build Sheets
    df_ts_agg_saved = add_sparkline_sheet(workbook, writer, df_ts_agg)
    build_overview_sheet(workbook, writer, df_camp, df_kw, today)
    df_camp_out = build_campaigns_sheet(writer, df_camp)
    build_keywords_sheet(writer, df_kw)
    build_search_terms_sheet(writer, df_st)
    
    build_deep_dive_sheet(workbook, writer, df_ts, df_camp_out)
    
    # Kích hoạt sheet OVERVIEW để khi mở file sẽ thấy nó đầu tiên
    writer.sheets['📊 OVERVIEW'].activate()
    
    # 4. Draw Charts
    draw_campaign_sparklines(workbook, writer, df_camp_out, df_ts_agg_saved)

    # 5. Save
    writer.close()
    print(f"Da tao thanh cong Dashboard: {out_file}")

if __name__ == "__main__":
    main()
