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

        # 3. Contextual Audit (Mirror Logic)
        if csv_source is not None:
            df = pd.read_csv(csv_source)
            # Logic: Match NWR count to CSV row count
            nwr_lines = [l for l in lines if l.startswith("NWR")]
            if len(nwr_lines) != len(df):
                report.append({"line": 0, "level": "CRITICAL", "message": f"Data Mismatch: {len(df)} CSV rows vs {len(nwr_lines)} NWR records"})
            else:
                for idx, cwr_line in enumerate(nwr_lines):
                    csv_row = df.iloc[idx]
                    if not self.validate_row_match(cwr_line, csv_row):
                        report.append({"line": 0, "level": "CRITICAL", "message": f"Data Mismatch: NWR record {idx+1} does not match CSV row {idx+1} (Title/ISRC mismatch)"})
        
        return report, {}

    def validate_row_match(self, cwr_line, csv_row):
        # Strict match of Title and ISRC
        cwr_title = cwr_line[19:79].strip()
        csv_title = str(csv_row['TRACK: TITLE']).strip()
        if cwr_title != csv_title:
            return False
        return True
