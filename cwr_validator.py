import pandas as pd
import io

class CWRValidator:
    def process_file(self, cwr_content: str, csv_content: bytes = None) -> tuple:
        rep = []
        stats = {"transactions": 0}
        
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
            elif record_type == 'REC':
                rec_records.append({"line_num": line_num, "content": line})
            
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
