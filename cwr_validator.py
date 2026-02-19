import re

class CWRValidator:
    def process_file(self, content):
        lines = content.replace('\r\n', '\n').split('\n')
        lines = [l for l in lines if len(l.strip()) > 0]
        report = []
        stats = {"lines_read": len(lines), "transactions": 0}
        
        curr_work = None
        has_w = False
        has_p = False
        TRANS_TAGS = ["REV", "NWR"]

        for i, line in enumerate(lines):
            l_num = i + 1
            if len(line) < 3: continue
            rec = line[0:3]
            
            if rec == "HDR":
                # Version Audit: Ensure file version is strictly 2.200 (Pos 103-108)
                ver = line[103:108]
                if ver != "2.200":
                    report.append({"level": "ERROR", "line": l_num, "message": f"Version Mismatch: Expected '2.200', found '{ver}'.", "content": line})

            if rec in TRANS_TAGS or rec == "GRT" or rec == "TRL":
                if curr_work:
                    if not has_w: report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{curr_work}' HAS NO WRITERS.", "content": ""})
                    if not has_p: report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{curr_work}' HAS NO PUBLISHERS.", "content": ""})
                if rec in TRANS_TAGS:
                    curr_work = line[19:79].strip() 
                    has_w = False
                    has_p = False
                    stats["transactions"] += 1
            
            if rec == "SWR": has_w = True
            if rec == "SPU": 
                has_p = True
                # Length Audit: strict 166 chars
                if len(line) != 166:
                    report.append({"level": "CRITICAL", "line": l_num, "message": f"Length Fail: SPU record is {len(line)} chars (expected 166).", "content": line})

                # Agreement Audit: Warnings for blank/zero Agreement Num (Pos 151, 14 chars)
                # Slices are 0-indexed: Pos 151 is index 150
                agr = line[150:164].strip()
                if not agr or agr == "00000000000000":
                    report.append({"level": "WARNING", "line": l_num, "message": "Agreement Audit: Society Assigned Agreement Number is missing or zero.", "content": line})
                
                # Agreement Type Audit: Must be 'PG' at Pos 165
                agr_type = line[164:166]
                if agr_type != "PG":
                     report.append({"level": "ERROR", "line": l_num, "message": f"Syntax Fail: Expected 'PG' at Pos 165, found '{agr_type}'.", "content": line})

            if rec == "ORN":
                # Numeric Audit: Critical Error if Cut Number (Pos 96, 4 chars) is non-numeric
                cut = line[96:100]
                if not cut.isdigit():
                     report.append({"level": "CRITICAL", "line": l_num, "message": f"Numeric Audit: Cut Number '{cut}' contains non-numeric characters.", "content": line})

            if rec == "REC":
                # Length Audit: strict 508 chars (Unified Source of Truth)
                if len(line) != 508:
                     report.append({"level": "CRITICAL", "line": l_num, "message": f"Length Fail: REC record is {len(line)} chars (expected 508).", "content": line})

            line_check = line
            if rec in TRANS_TAGS:
                line_check = line[:19] + (" " * 60) + line[79:]
            
            if re.search(r'(?<!\w)NAN(?!\w)', line_check):
                report.append({"level": "ERROR", "line": l_num, "message": "Syntax Fail: Standalone 'NAN' found in data field.", "content": line})
            if rec in TRANS_TAGS:
                if len(line) < 145 or line[142:145] != "ORI":
                    report.append({"level": "ERROR", "line": l_num, "message": f"Alignment Fail: '{rec}' missing 'ORI' at pos 142.", "content": line})
            if rec == "SWR":
                ipi = line[115:126].strip()
                if ipi != "" and not re.match(r'^\d{11}$', ipi):
                    report.append({"level": "ERROR", "line": l_num, "message": f"Padding Fail: IPI '{ipi}' is not 11 digits.", "content": line})

        return report, stats
