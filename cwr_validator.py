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
            if rec == "SPU": has_p = True
            
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
