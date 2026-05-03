import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rule_core

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    rules = rule_core.load_rules(base_dir)
    
    input_file = os.path.join(base_dir, "phase2", "output", "evergreen", "launch_phase.json")
    output_file = os.path.join(base_dir, "phase3", "output", "evergreen", "launch_suggested.json")
    
    print("=" * 60)
    print("  ĐÁNH GIÁ RULE: LAUNCH PHASE")
    print("=" * 60)
    
    rule_core.process_file(input_file, output_file, rules, "launch_phase")
    print()

if __name__ == "__main__":
    main()
