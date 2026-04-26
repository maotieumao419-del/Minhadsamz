import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

input_dir = r'f:\Minhpython\Test3\phase3\output'
files = [f for f in os.listdir(input_dir) if f.endswith('.json')]

total_skip = 0
total_all = 0

for fname in sorted(files):
    fpath = os.path.join(input_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sku_name = os.path.splitext(fname)[0]
    print(f'\n{"="*60}')
    print(f'SKU: {sku_name} ({len(data)} campaigns)')
    print(f'{"="*60}')
    
    skip_count = 0
    total_all += len(data)
    
    for i, item in enumerate(data):
        keyword_text = str(item.get('Target', '')).strip()
        note_str = str(item.get('Ghi chú', '')).strip()
        
        reasons = []
        if not keyword_text:
            reasons.append('Target rỗng')
        if not note_str:
            reasons.append('Ghi chú rỗng')
        
        if not reasons:
            # Check match type
            m = re.search(r'\b(exact|phrase|broad)\b', note_str, re.IGNORECASE)
            if not m:
                reasons.append(f'Không tìm thấy Match Type trong Ghi chú: "{note_str}"')
            # Check placement
            p = re.search(r'(\d+)\s*(?:TRP|TPR|T(?![A-Z])|%)', note_str, re.IGNORECASE)
            if not p:
                reasons.append(f'Không tìm thấy Placement% trong Ghi chú: "{note_str}"')
        
        if reasons:
            skip_count += 1
            campaign_name = item.get('Campaign Name', 'N/A')
            stt = item.get('STT', '?')
            print(f'  [{stt}] BỎ QUA - Campaign: {campaign_name}')
            print(f'       Target  : "{keyword_text}"')
            print(f'       Ghi chú : "{note_str}"')
            for r in reasons:
                print(f'       Lý do   : {r}')
            print()
    
    total_skip += skip_count
    print(f'  >> Tổng bỏ qua trong file này: {skip_count}/{len(data)}')

print(f'\n{"="*60}')
print(f'TỔNG KẾT: {total_skip} campaigns bị bỏ qua / {total_all} tổng cộng')
print(f'{"="*60}')
