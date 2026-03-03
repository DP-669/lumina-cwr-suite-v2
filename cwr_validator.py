import pandas as pd

class CWRValidator:
    def process_file(self, content, csv_source=None):
        lines = content.splitlines()
        report = []
        
        # 1. Geometry Audit (182-Char Symmetry)
        for i, line in enumerate(lines, 1):
            rec_type = line[:3]
            if rec_type in ["NWR", "SWR", "SWT", "SPU", "SPT"]:
                if len(line) != 182:
                    report.append({"line": i, "level": "CRITICAL", "message": f"{rec_type} length invalid. Expected 182, got {len(line)}"})
            
            # 2. CD Source Lock Audit
            if rec_type == "REC":
                source = line[262:264]
                if source != "CD":
                    report.append({"line": i, "level": "CRITICAL", "message": f"REC Source must be 'CD', found '{source}'"})

        # 3. Mirror Audit (Contextual Match)
        if csv_source is not None:
            csv_source.seek(0)
            df_preview = pd.read_csv(csv_source, header=None, nrows=20)
            h_idx = -1
            MARKERS = ["TRACK: TITLE", "SOURCEAUDIO ID", "TITLE", "LIBRARY: NAME", "WORK TITLE"]
            for i, row in df_preview.iterrows():
                if any(m in row.astype(str).str.cat(sep=" ").upper() for m in MARKERS):
                    h_idx = i; break
            
            if h_idx != -1:
                csv_source.seek(0)
                df = pd.read_csv(csv_source, header=h_idx)
                df.columns = [str(c).strip().upper() for c in df.columns]
                if 'WORK TITLE' in df.columns: df = df.rename(columns={'WORK TITLE': 'TRACK: TITLE'})
                
                nwr_lines = [l for l in lines if l.startswith("NWR")]
                if len(nwr_lines) != len(df):
                    report.append({"line": 0, "level": "CRITICAL", "message": f"Data Mismatch: {len(df)} CSV rows vs {len(nwr_lines)} NWR records"})
                else:
                    for cwr_line, csv_row in zip(nwr_lines, df.to_dict('records')):
                        if not self.validate_row_match(cwr_line, csv_row):
                            cwr_title = cwr_line[19:79].strip()
                            csv_title = str(csv_row.get('TRACK: TITLE', '')).strip()
                            report.append({"line": 0, "level": "CRITICAL", "message": f"Title Mismatch: CWR='{cwr_title}' | CSV='{csv_title}'"})
        
        return report, {}

    def validate_row_match(self, cwr_line, csv_row):
        # Strict Match: No Truncation allowed. 
        # CWR engine already truncated the title during build; if CSV title is > 60, it will not match.
        cwr_title = cwr_line[19:79].strip()
        csv_title = str(csv_row.get('TRACK: TITLE', '')).strip()
        
        if cwr_title != csv_title[:60]: 
            return False
        return True
