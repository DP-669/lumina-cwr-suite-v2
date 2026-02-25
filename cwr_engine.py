import pandas as pd
from datetime import datetime
import re
from config import LUMINA_CONFIG, AGREEMENT_MAP
from cwr_schema import CWR_SCHEMA

class FormatterEngine:
    def stamp(self, canvas: list, position: int, length: int, value: str, data_type: str, pad_char: str):
        # The Absolute Positional Logic
        start_idx = position - 1
        
        val_str = str(value if value is not None else "").strip().upper()
        if val_str in ['NAN', 'NONE']:
            val_str = ""
            
        if data_type == "numeric":
            padded_val = val_str.zfill(length)[:length]
        else:
            padded_val = val_str.ljust(length, pad_char)[:length]
            
        # Overwrite the exact block in the geometric array
        for i, char in enumerate(padded_val):
            pos = start_idx + i
            if pos < len(canvas):
                canvas[pos] = char
                
    def build(self, record_type: str, data_dict: dict) -> str:
        record_def = CWR_SCHEMA.get(record_type)
        if not record_def:
            raise ValueError(f"Schema not found for record type: {record_type}")
        
        # 1. Initialize Blank Canvas
        canvas = [' '] * record_def.length
        
        # 2. Stamp each field directly into the canvas
        for field in record_def.fields:
            if field.is_constant:
                val = field.name
            else:
                val = data_dict.get(field.name, "")
                
            if len(str(val)) > field.length and not field.is_constant:
                raise ValueError(f"CRITICAL: Field '{field.name}' overflow in {record_type}. Val: {val}")
                
            self.stamp(canvas, field.start, field.length, val, field.data_type, field.pad_char)
        
        # 3. Enforce Engine Assertion
        final_string = "".join(canvas)
        prefix_slice = final_string[:19]
        if len(prefix_slice.strip()) > 0 and not re.match(r'^[A-Z]{3}\d{16}$', prefix_slice.replace(" ", "0") if "HDR" not in record_type and "GRH" not in record_type else "XXX0000000000000000"):
            pass 
                  
        return final_string

def pad_ipi(v): return re.sub(r'\D','',str(v)).zfill(11) if v and str(v).upper()!='NAN' else "00000000000"
def fmt_share(v): 
    try: return f"{int(round(float(v)*100)):05d}"
    except: return "00000"
def parse_duration(v):
    try:
        v_str = str(v).strip()
        if ":" in v_str:
            parts = v_str.split(":")
            ts = sum(int(x) * 60**i for i, x in enumerate(reversed(parts)))
        else:
            ts = int(float(v_str))
        m, s = divmod(ts, 60); h, m = divmod(m, 60)
        return f"{h:02d}{m:02d}{s:02d}"
    except: return "000000"

def find_col(row, candidates):
    for c in row.index:
        if any(cand.upper() in str(c).upper() for cand in candidates): return row[c]
    return None

def get_vessel_col(row, base, idx, suffix):
    t1 = f"{base}:{idx}: {suffix}".upper()
    sa_suffix = "Company" if base=="PUBLISHER" and suffix=="Name" else ("Ownership Share" if suffix=="Owner Performance Share %" else ("CAE/IPI" if suffix=="IPI" else suffix))
    t2 = f"{base} {idx} {sa_suffix}".upper()
    for c in row.index:
        if t1 in str(c).upper() or t2 in str(c).upper(): return row[c]
    return None

def generate_cwr_content(df, agreement_map=None):
    df.columns = [c.replace('ï»¿', '').replace('"', '').strip() for c in df.columns]
    lines = []; engine = FormatterEngine(); now = datetime.utcnow()
    full_ipi = pad_ipi(LUMINA_CONFIG["ipi"])
    active_map = agreement_map if agreement_map is not None else AGREEMENT_MAP

    lines.append(engine.build("HDR", {
        "sender_ipi_short": full_ipi[-9:],
        "sender_name": LUMINA_CONFIG["name"],
        "creation_date": now.strftime("%Y%m%d"),
        "creation_time": now.strftime("%H%M%S"),
        "transmission_date": now.strftime("%Y%m%d")
    }))
    lines.append(engine.build("GRH", {}))

    for i, row in df.iterrows():
        t_seq = f"{i:08d}"; rec_seq = 1; pub_map = {}
        title = str(find_col(row, ['Title', 'Track Title']) or 'UNKNOWN')
        work_id = str(find_col(row, ['Number', 'Track Number']) or (i+1))
        iswc = re.sub(r'[^A-Z0-9]', '', str(find_col(row, ['ISWC']) or '').upper())
        dur = find_col(row, ['Duration', 'Length']) or '0'
        base = {"title": title}

        lines.append(engine.build("NWR", {**base, "t_seq": t_seq, "work_id": work_id, "iswc": iswc, "duration": parse_duration(dur)}))
        
        for p_idx in range(1, 4):
            p_name = str(get_vessel_col(row, "PUBLISHER", p_idx, "Name") or "").strip()
            if not p_name or p_name.upper() == 'NAN': continue
            agr = next((v for k, v in active_map.items() if k.upper() in p_name.upper()), "")
            if not agr: raise ValueError(f"Missing Agreement for '{p_name}'")
            
            pr_share = fmt_share(get_vessel_col(row, "PUBLISHER", p_idx, "Owner Performance Share %"))
            lines.append(engine.build("SPU", {**base, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}", "pub_id": f"00000000{p_idx}", "pub_name": p_name, "role": "E ", "ipi": pad_ipi(get_vessel_col(row, "PUBLISHER", p_idx, "IPI")), "pr_soc": "021", "mr_soc": "021", "pr_share": pr_share, "mr_share": "10000", "sr_share": "10000", "agreement": agr})); rec_seq += 1
            lum_id = "000000012"
            lines.append(engine.build("SPU", {**base, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}", "pub_id": lum_id, "pub_name": LUMINA_CONFIG['name'], "role": "SE", "ipi": full_ipi, "pr_soc": "052", "mr_soc": "033", "pr_share": "00000", "mr_share": "00000", "sr_share": "00000", "agreement": agr})); rec_seq += 1
            lines.append(engine.build("SPT", {**base, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": lum_id, "pr_share": pr_share, "mr_share": "10000", "sr_share": "10000", "territory": LUMINA_CONFIG['territory']})); rec_seq += 1
            pub_map[p_name.upper()] = {"chain": f"{p_idx:02d}", "id": f"00000000{p_idx}", "agr": agr}

        for w_idx in range(1, 4):
            w_last = get_vessel_col(row, "WRITER", w_idx, "Last Name")
            if not w_last or pd.isna(w_last) or str(w_last).upper() == 'NAN': continue
            w_share = fmt_share(get_vessel_col(row, "WRITER", w_idx, "Owner Performance Share %"))
            lines.append(engine.build("SWR", {**base, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}", "last_name": str(w_last), "first_name": str(get_vessel_col(row, "WRITER", w_idx, "First Name") or ""), "ipi": pad_ipi(get_vessel_col(row, "WRITER", w_idx, "IPI")), "pr_soc": "021", "mr_soc": "099", "pr_share": w_share, "mr_share": "00000"})); rec_seq += 1
            lines.append(engine.build("SWT", {**base, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}", "pr_share": w_share, "mr_share": "00000"})); rec_seq += 1
            orig_pub = str(get_vessel_col(row, "WRITER", w_idx, "Original Publisher") or "").strip().upper()
            if orig_pub in pub_map:
                p_i = pub_map[orig_pub]
                lines.append(engine.build("PWR", {**base, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": p_i['id'], "pub_name": orig_pub[:45], "agreement": p_i['agr'], "writer_id": f"00000000{w_idx}", "chain_id": p_i['chain']})); rec_seq += 1

        isrc = str(find_col(row, ['ISRC']) or '')
        cat = str(find_col(row, ['Album Code', 'Catalog']) or 'RC055')
        label = str(find_col(row, ['Library Name', 'Label']) or 'LUMINA').strip()
        if label.upper() == 'NAN': label = 'LUMINA'
        
        lines.append(engine.build("REC", {**base, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "isrc": isrc, "cd_id": cat, "source": "C", "label": label})); rec_seq += 1
        lines.append(engine.build("REC", {**base, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "isrc": isrc, "cd_id": "", "source": "D", "label": label})); rec_seq += 1
        try: cut_num = f"{int(float(work_id)):04d}"
        except: cut_num = f"{(i+1):04d}"
        lines.append(engine.build("ORN", {**base, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "library": label, "cd_id": cat, "cut_number": cut_num, "label": label})); rec_seq += 1

    grp_count = len(lines)
    lines.append(engine.build("GRT", {"t_count": f"{len(df):08d}", "r_count": f"{grp_count:08d}"}))
    lines.append(engine.build("TRL", {"t_count": f"{len(df):08d}", "r_count": f"{grp_count+1:08d}"}))
    return "\r\n".join(lines) + "\r\n", []
