import re
from cwr_schema import CWR_SCHEMA

class CWRValidator:
    def process_file(self, content):
        lines = [l for l in content.replace('\r\n', '\n').split('\n') if len(l.strip()) > 3]
        report = []
        
        for i, line in enumerate(lines):
            l_num = i + 1
            rec_type = line[0:3]
            
            if rec_type not in CWR_SCHEMA:
                continue
                
            schema = CWR_SCHEMA[rec_type]
            
            if len(line) != schema.length:
                report.append({"level": "CRITICAL", "line": l_num, "message": f"[{rec_type}] Length Error. Expected {schema.length}, got {len(line)}."})
                return report, {}

            for field in schema.fields:
                if field.is_constant:
                    start_idx = field.start - 1
                    actual = line[start_idx : start_idx + field.length]
                    if actual != field.name:
                        report.append({
                            "level": "CRITICAL", 
                            "line": l_num, 
                            "message": f"[{rec_type}] Geometry Fail at Position {field.start}. Expected '{field.name}', found '{actual}'"
                        })
                        return report, {}

            if re.search(r'(?<!\w)NAN(?!\w)', line):
                report.append({"level": "CRITICAL", "line": l_num, "message": f"[{rec_type}] Syntax Fail: 'NAN' detected."})
                return report, {}

        return report, {"lines": len(lines)}
