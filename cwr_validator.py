import pandas as pd
import io

class CWRValidator:
    def process_file(self, cwr_content: str, csv_content: bytes = None, filename: str = None) -> tuple:
        rep = []
        stats = {"transactions": 0}
        
        # --- 0. FILENAME AUDIT ---
        if filename:
            import re
            pattern = r"^CW\d{2}\d{4}LUM_319\.V22$"
            if not re.match(pattern, filename):
                rep.append({
                    "level": "CRITICAL",
                    "line": 0,
                    "message": f"FILENAME REJECTION: '{filename}' does not match mandatory CWR 2.2 pattern CW[YY][NNNN]LUM_319.V22",
                    "content": ""
                })
        
        # Strip newlines but preserve exact trailing space geometry per line
        lines = [line.strip('\r\n') for line in cwr_content.split('\n') if line.strip('\r\n')]
        
        nwr_records = []
        rec_records = []
        
        # --- 1. GEOMETRY AND SYNTAX AUDIT ---
        strict_182_records = ['NWR', 'SPU', 'SWR', 'SPT', 'SWT']
        
        for i, line in enumerate(lines):
            line_num = i + 1
            record_type = line[0:3]
            
            if record_type == 'NWR':
                stats["transactions"] += 1
                nwr_records.append({"line_num": line_num, "content": line})
                if len(line) >= 144 and line[141:144] != 'ORI':
                    rep.append({
                        "level": "CRITICAL",
                        "line": line_num,
                        "message": "ORI Anchor point shifted. Must be at Position 142.",
                        "content": line[130:150]
                    })
            elif record_type == 'REC':
                rec_records.append({"line_num": line_num, "content": line})
            elif record_type == 'SPU':
                pg_idx = line.find('PG')
                if pg_idx != -1 and pg_idx != 160:
                    rep.append({
                        "level": "CRITICAL",
                        "line": line_num,
                        "message": f"SPU GEOMETRY FAIL: 'PG' string found at index {pg_idx} (Pos {pg_idx+1}). MUST be exactly at Index 160 (Position 161).",
                        "content": line[140:175]
                    })
            
            # Geometry Audit
            if record_type in strict_182_records:
                if len(line) != 182:
                    rep.append({
                        "level": "CRITICAL",
                        "line": line_num,
                        "message": f"GEOMETRY FAIL: {record_type} record length is {len(line)}, MUST be exactly 182 characters.",
                        "content": f"Length: {len(line)} | Preview: {line[:50]}..."
                    })
            
            # CD Source Lock Audit
            if record_type == 'REC':
                if len(line) < 264:
                    rep.append({
                        "level": "CRITICAL",
                        "line": line_num,
                        "message": f"REC GEOMETRY FAIL: REC record length is {len(line)}, cannot inspect Position 263.",
                        "content": line[:50] + "..."
                    })
                else:
                    source_val = line[262:264]
                    if source_val != 'CD':
                        rep.append({
                            "level": "CRITICAL",
                            "line": line_num,
                            "message": f"CRITICAL: REC Source must be 'CD'. Found '{source_val}' at pos 263.",
                            "content": line[250:270]
                        })
                        
        # --- 1.5. PR SHARE AUDIT (WRITER TOTAL = 10000) ---
        swr_shares = {}
        for line in lines:
            if len(line) < 11:
                continue
            rec_type = line[0:3]
            if rec_type == 'NWR':
                swr_shares[line[3:11]] = 0
            elif rec_type == 'SWR':
                t_seq = line[3:11]
                if t_seq in swr_shares:
                    try:
                        swr_shares[t_seq] += int(line[129:134].strip() or 0)
                    except ValueError:
                        pass
        
        for t_seq, total_share in swr_shares.items():
            if total_share != 10000:
                rep.append({
                    "level": "CRITICAL",
                    "line": 0,
                    "message": f"PR SHARE FAIL: Work with seq '{t_seq}' has Writer PR shares summing to {total_share}. MUST be exactly 10000 (no 0.5 multiplier).",
                    "content": ""
                })
                        
        # --- 2. MIRROR AUDIT (CONTEXTUAL TRUTH CHECK) ---
        if csv_content:
            try:
                df = pd.read_csv(io.BytesIO(csv_content))
                
                # Header Target Match
                df.columns = [str(c).replace('ï»¿', '').replace('"', '').strip().upper() for c in df.columns]
                
                if 'TRACK: TITLE' not in df.columns:
                    rep.append({
                        "level": "CRITICAL",
                        "line": 0,
                        "message": "MIRROR AUDIT FAIL: CSV missing required 'TRACK: TITLE' column.",
                        "content": "Headers: " + ", ".join(df.columns)
                    })
                else:
                    csv_titles = df['TRACK: TITLE'].astype(str).str.strip().tolist()
                    
                    # Zero-Truncation Match: Count Verification
                    if len(nwr_records) != len(csv_titles):
                        rep.append({
                            "level": "CRITICAL",
                            "line": 0,
                            "message": f"MIRROR AUDIT FAIL: NWR generation count ({len(nwr_records)}) does not match source CSV row count ({len(csv_titles)}).",
                            "content": ""
                        })
                        
                    # Truncation Rule Verification
                    for idx, csv_title in enumerate(csv_titles):
                        if len(csv_title) > 60:
                            rep.append({
                                "level": "CRITICAL",
                                "line": idx + 1,
                                "message": f"CRITICAL_MISMATCH: CSV Title '{csv_title}' exceeds 60 characters. File contains illegal silent truncation.",
                                "content": f"Title Length: {len(csv_title)}"
                            })
            except Exception as e:
                rep.append({
                    "level": "ERROR",
                    "line": 0,
                    "message": f"MIRROR AUDIT FAIL: Could not parse CSV source - {str(e)}",
                    "content": ""
                })

        return rep, stats
