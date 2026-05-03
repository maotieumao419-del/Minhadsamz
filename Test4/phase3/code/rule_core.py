import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def load_rules(base_dir):
    rule_path = os.path.join(base_dir, "Rule_Engine.json")
    engine = load_json(rule_path)
    return engine.get("rules", [])

def get_effective_thresholds(rule, phase):
    conditions = rule.get("base_conditions", {}).copy()
    overrides = rule.get("phase_overrides", {}).get(phase, {})
    for k, v in overrides.items():
        conditions[k] = v
    return conditions

def check_conditions(kw, conditions):
    if not conditions:
        return False
        
    clicks = kw.get("Clicks", 0)
    orders = kw.get("Orders", 0)
    impressions = kw.get("Impressions", 0)
    acos = kw.get("ACOS", 0.0)

    if acos is None or acos == "":
        acos = 0.0
    
    if "clicks_min" in conditions and clicks < conditions["clicks_min"]: return False
    if "clicks_max" in conditions and clicks > conditions["clicks_max"]: return False
    
    if "orders_min" in conditions and orders < conditions["orders_min"]: return False
    if "orders_max" in conditions and orders > conditions["orders_max"]: return False
    
    if "impressions_min" in conditions and impressions < conditions["impressions_min"]: return False
    if "impressions_max" in conditions and impressions > conditions["impressions_max"]: return False
    
    if "acos_min" in conditions and acos < conditions["acos_min"]: return False
    if "acos_max" in conditions and acos > conditions["acos_max"]: return False
    
    return True

def apply_action(kw, rule):
    action_type = rule["action_type"]
    action_value = rule.get("action_value", 0)
    
    current_bid = kw.get("Bid", 0)
    if not current_bid or current_bid == "":
        current_bid = 0.75 
    current_bid = float(current_bid)
    
    sugg_action = ""
    sugg_bid = current_bid
    
    if action_type == "Pause":
        sugg_action = "Pause"
    elif action_type == "Decrease_Bid_Percentage":
        sugg_action = "Update Bid"
        sugg_bid = current_bid * (1 - action_value)
    elif action_type == "Increase_Bid_Percentage":
        sugg_action = "Update Bid"
        sugg_bid = current_bid * (1 + action_value)
    elif action_type == "Increase_Bid_Absolute":
        sugg_action = "Update Bid"
        sugg_bid = current_bid + action_value
        
    sugg_bid = round(sugg_bid, 2)
    return sugg_action, sugg_bid

def process_file(input_path, output_path, rules, phase_name):
    if not os.path.exists(input_path):
        print(f"  ⏭ Không tìm thấy file: {input_path}")
        return
        
    keywords = load_json(input_path)
    if not keywords:
        print(f"  ⏭ File rỗng: {os.path.basename(input_path)}")
        return
        
    print(f"  ▶ Đang xử lý {len(keywords)} keywords cho phase: {phase_name}...")
    actioned_count = 0
    
    for kw in keywords:
        match_type = kw.get("Match Type", "").lower()
        
        triggered_rule = None
        sugg_action = ""
        sugg_bid = ""
        rule_name = ""
        
        for rule in rules:
            allowed_matches = rule.get("match_types", [])
            if allowed_matches and match_type not in allowed_matches:
                continue
                
            conditions = get_effective_thresholds(rule, phase_name)
            
            if check_conditions(kw, conditions):
                triggered_rule = rule
                break 
                
        if triggered_rule:
            rule_name = triggered_rule["rule_name"]
            sugg_action, sugg_bid = apply_action(kw, triggered_rule)
            
            # Load Guardrails
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(output_path))))
            engine = load_json(os.path.join(base_dir, "Rule_Engine.json"))
            phase_limits = engine.get("phase_guardrails", {}).get(phase_name, {})
            max_cpc = phase_limits.get("max_cpc", 99.0)
            min_cpc = phase_limits.get("min_cpc", 0.0)
            
            approval_status = "AUTO_APPROVED"
            review_reason = ""
            
            if sugg_action == "Update Bid":
                if sugg_bid > max_cpc:
                    sugg_bid = max_cpc
                    approval_status = "REQUIRES_REVIEW"
                    review_reason = f"Hit Max CPC (${max_cpc}) Limit"
                elif sugg_bid < min_cpc:
                    sugg_bid = min_cpc
                    approval_status = "REQUIRES_REVIEW"
                    review_reason = f"Hit Min CPC (${min_cpc}) Limit"
            
            if sugg_action == "Pause" and kw.get("Impressions", 0) > 5000:
                approval_status = "REQUIRES_REVIEW"
                review_reason = "Attempt to pause high-traffic keyword (>5000 Imps)"
                
            actioned_count += 1
            
        kw["Suggested Action"] = sugg_action
        kw["Suggested Bid"] = sugg_bid
        kw["Action Reason"] = rule_name
        if sugg_action:
            kw["Approval Status"] = approval_status
            kw["Review Reason"] = review_reason
        else:
            kw["Approval Status"] = ""
            kw["Review Reason"] = ""
            
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(keywords, f, indent=4, ensure_ascii=False)
        
    print(f"  ✅ Đã quét xong. Có {actioned_count} keywords cần xử lý. Đã lưu ra {os.path.basename(output_path)}")
