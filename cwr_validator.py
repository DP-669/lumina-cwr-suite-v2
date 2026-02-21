import re

class CWRValidator:
    EXPECTED_SPU_LEN = 166
    EXPECTED_REC_LEN = 508

    # Independent Clean Room Rule Dictionary
    RULES = {
        "HDR": {
            "length": 108,
            "fields": [
                ("Version", 103, 108, r"^2\.200$")
            ]
        },
        "GRH": {
            "length": 26,
            "fields": [
                ("Transaction Type", 3, 6, r"^NWR$"),
                ("Version", 11, 16, r"^02\.20$")
            ]
        },
        "NWR": {
            "length": 145,
            "fields": [
                ("Origin", 142, 145, r"^ORI$")
            ]
        },
        "SPU": {
            "length": 166,
            "fields": [
                ("Publisher Sequence", 11, 19, r"^\d{8}$"),
                ("SR Share & Refusal", 131, 138, r"^\d{5} N$"),
                ("Agreement Type", 164, 166, r"^PG$")
            ]
        },
        "SPT": {
            "length": 58,
            "fields": []
        },
        "SWR": {
            "length": 152,
            "fields": [
                ("IPI", 115, 126, r"^(\d{11}|\s{11})$")
            ]
        },
        "SWT": {
            "length": 52,
            "fields": []
        },
        "PWR": {
            "length": 112,
            "fields": [
                ("Submitter Agreement Number", 73, 87, r"^(?!\s*$).+") # Lumina Rule: NEVER blank
            ]
        },
        "REC": {
            "length": 508,
            "fields": [
                ("Source", 262, 263, r"^[CD]$"),
                ("Label", 445, 505, r"^(?!\s*$).+")
            ]
        },
        "ORN": {
            "length": 160,
            "fields": [
                ("Cut Number", 96, 100, r"^\d{4}$")
            ]
        },
        "GRT": {
            "length": 24,
            "fields": []
        },
        "TRL": {
            "length": 24,
            "fields": []
        }
    }

    def process_file(self, content, expected_catalog=None):
        lines = content.replace('\r\n', '\n').split('\n')
        lines = [l for l in lines if len(l.strip()) > 0]
        report = []
        stats = {"lines_read": len(lines), "transactions": 0}
        
        curr_work = None
        has_w = False
        has_p = False
        rec_sources = set()
        TRANS_TAGS = ["REV", "NWR"]

        for i, line in enumerate(lines):
            l_num = i + 1
            if len(line) < 3: continue
            rec = line[0:3]
            
            # --- 1. Clean Room Dictionary Audit ---
            if rec in self.RULES:
                rule = self.RULES[rec]
                
                # Length Audit
                if len(line) != rule["length"]:
                    report.append({"level": "CRITICAL", "line": l_num, "message": f"HALT: [{rec}] Length Fail at Line {l_num}. Expected {rule['length']} chars, got {len(line)}.", "content": line})
                    return report, stats
                
                # Micro-Column Inspection
                for field_name, start, end, pattern in rule["fields"]:
                    segment = line[start:end]
                    if not re.match(pattern, segment):
                        report.append({
                            "level": "CRITICAL", 
                            "line": l_num, 
                            "message": f"HALT: [{rec}] Micro-Inspection Fail at Line {l_num}, Column Index [{start}:{end}]. Field '{field_name}' invalid. Found: '{segment}'", 
                            "content": line
                        })
                        return report, stats

            # --- 2. Dynamic Rules & Transaction Integrity ---
            if rec == "REC" and expected_catalog:
                label_val = line[445:505].strip()
                norm_label = label_val.upper().replace(" ", "")
                norm_cat = expected_catalog.upper().replace(" ", "")
                if norm_label != norm_cat:
                    report.append({"level": "CRITICAL", "line": l_num, "message": f"HALT: [{rec}] Label Mismatch at Line {l_num}: Found '{label_val}', expected '{expected_catalog}'.", "content": line})
                    return report, stats
                    
            if rec in TRANS_TAGS or rec == "GRT" or rec == "TRL":
                if curr_work:
                    if not has_w: 
                        report.append({"level": "CRITICAL", "line": l_num-1, "message": f"HALT: [{rec}] WORK '{curr_work}' HAS NO WRITERS.", "content": ""})
                        return report, stats
                    if not has_p: 
                        report.append({"level": "CRITICAL", "line": l_num-1, "message": f"HALT: [{rec}] WORK '{curr_work}' HAS NO PUBLISHERS.", "content": ""})
                        return report, stats
                    if "C" not in rec_sources or "D" not in rec_sources:
                        report.append({"level": "CRITICAL", "line": l_num-1, "message": f"HALT: [{rec}] WORK '{curr_work}' IS MISSING DUAL REC RECORDS ('C' AND 'D').", "content": ""})
                        return report, stats
                if rec in TRANS_TAGS:
                    curr_work = line[19:79].strip() 
                    has_w = False
                    has_p = False
                    rec_sources = set()
                    stats["transactions"] += 1
            
            if rec == "SWR": has_w = True
            if rec == "SPU": has_p = True
            if rec == "REC": rec_sources.add(line[262:263])

            line_check = line
            if rec in TRANS_TAGS:
                line_check = line[:19] + (" " * 60) + line[79:]
            
            if re.search(r'(?<!\w)NAN(?!\w)', line_check):
                report.append({"level": "CRITICAL", "line": l_num, "message": f"HALT: [{rec}] Syntax Fail: Standalone 'NAN' found in data field at Line {l_num}.", "content": line})
                return report, stats
            
        return report, stats
