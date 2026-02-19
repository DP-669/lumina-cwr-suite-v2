
import pandas as pd
import sys
import os
from datetime import datetime

# Ensure we can import from local directory
sys.path.append(os.getcwd())

from cwr_engine import generate_cwr_content, Blueprints
from cwr_validator import CWRValidator

def run_transparency_test():
    input_csv = "INPUT_CSVS/EPP060_Metadata.csv"
    output_dir = "OUTPUT_CWR"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "EPP060_GoldStandard.V22")

    print(f"Reading {input_csv}...")
    try:
        df = pd.read_csv(input_csv, encoding='latin1')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Agreement Map (Same Publisher Verified)
    agreement_map = {}
    agreement_map["PASHALINA PUBLISHING COMPANY"] = "4316161"
    
    print(f"Agreement Map: {len(agreement_map)} entries.")

    print("Generating CWR Content...")
    try:
        content, warnings = generate_cwr_content(df, agreement_map)
    except Exception as e:
        print(f"CRITICAL ERROR in Engine: {e}")
        return

    print(f"Writing parsed content to {output_file}...")
    with open(output_file, 'w', encoding='latin1') as f:
        f.write(content)

    print("\n--- VALIDATING OUTPUT ---")
    validator = CWRValidator()
    report, stats = validator.process_file(content)
    
    critical_errors = [r for r in report if r['level'] == 'CRITICAL']
    print(f"Critical Errors: {len(critical_errors)}")

    print("\n--- AUDIT CHECKS ---")
    
    # 0. HDR Timestamp Check
    hdr_line = [line for line in content.splitlines() if line.startswith("HDR")][0]
    file_time_str = hdr_line[74:80] # HHMMSS
    now = datetime.now()
    print(f"HDR Timestamp: {file_time_str}")
    # Simple check: same hour/minute? (Allowing execution time diff)
    now_hm = now.strftime("%H%M")
    file_hm = file_time_str[:4]
    if now_hm == file_hm or int(now_hm) - int(file_hm) <= 1:
         print("PASS: Timestamp is current.")
    else:
         print(f"WARNING: Timestamp {file_time_str} vs Now {now_hm}??")

    # 1. REC Record Layout
    rec_lines = [line for line in content.splitlines() if line.startswith("REC")]
    if rec_lines:
        first_rec = rec_lines[0]
        print(f"Sample REC Length: {len(first_rec)}")
        if len(first_rec) == 508: print("PASS: REC Length is 508.")
        else: print(f"FAIL: REC Length is {len(first_rec)}")
        
        # Label Check (Dynamic)
        label_check = first_rec[446:506].strip()
        print(f"REC Label: '{label_check}'")
        
        target_label = "EKONOMIC PROPAGANDA"
        if label_check == target_label:
             print(f"PASS: Label matches '{target_label}' exactly.")
        else:
             print(f"FAIL: Label is '{label_check}', expected '{target_label}'")

    # 2. SPU Layout & Math
    spu_lines = [line for line in content.splitlines() if line.startswith("SPU")]
    if spu_lines:
        first_spu = spu_lines[0]
        print(f"Sample SPU Length: {len(first_spu)}")
        
        if len(first_spu) == 166: print("PASS: SPU Length is 166.")
        else: print(f"FAIL: SPU Length is {len(first_spu)}")

        # Check Agreement Position 151 (Index 150)
        agr = first_spu[150:164]
        print(f"Agreement at Pos 151: '{agr}'")
        if agr.strip() == "4316161": print("PASS: Agreement ID match.")
        
        gap_content = first_spu[137:150]
        if gap_content == " " * 13:
             print("PASS: Gap is exactly 13 spaces.")
        else:
             print(f"FAIL: Gap content is '{gap_content}' (Len: {len(gap_content)})")

if __name__ == "__main__":
    run_transparency_test()
