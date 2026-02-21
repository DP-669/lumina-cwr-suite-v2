import pandas as pd
from datetime import datetime
import re
from config import LUMINA_CONFIG, AGREEMENT_MAP
from cwr_schema import CWR_SCHEMA

class FormatterEngine:
    def build(self, record_type: str, data_dict: dict) -> str:
        record_def = CWR_SCHEMA.get(record_type)
        if not record_def:
            raise ValueError(f"Schema not found for record type: {record_type}")
        
        # Initialize buffer with spaces for the exact record length
        buffer = [' '] * record_def.length
        
        for field in record_def.fields:
            if field.is_constant:
                val = field.name
            else:
                val = data_dict.get(field.name, "")
                
            val_str = str(val if val is not None else "").strip().upper()
            if val_str in ['NAN', 'NONE']:
                val_str = ""
                
            # Data Integrity Firewall: Check length BEFORE padding
            if len(val_str) > field.length:
                track_info = data_dict.get('title', 'Unknown Track')
                raise ValueError(
                    f"CRITICAL: Data truncation prevented. "
                    f"Track '{track_info}' - Field '{field.name}' in {record_type} "
                    f"exceeds max length of {field.length}. Value was: '{val_str}' "
                    f"(Length: {len(val_str)}). Automation halted."
                )
                
            # Apply padding based on data_type
            if field.data_type == "numeric":
                padded_val = val_str.rjust(field.length, field.pad_char)
            else:
                padded_val = val_str.ljust(field.length, field.pad_char)
                
            # Place into buffer at exact absolute position
            for i, char in enumerate(padded_val):
                pos = field.start + i
                if pos < record_def.length:
                    buffer[pos] = char
                    
        return "".join(buffer)

def pad_ipi(v): return re.sub(r'\D','',str(v)).zfill(11) if v and str(v).upper()!='NAN' else "00000000000"
def fmt_share(v): 
    try: return f"{int(round(float(v)*100)):05d}"
    except: return "00000"
def parse_duration(v):
    try:
        v = str(v).strip()
        if ":" in v: m,s = map(int, v.split(":")); h=0
        else: ts=int(float(v)); m,s=divmod(ts,60); h,m=divmod(m,60)
        return f"{h:02d}{m:02d}{s:02d}"
    except: return "000000"
def find_col(row, candidates):
    for c in candidates:
        uc = c.upper()
        for idx in row.index:
            if uc in str(idx).upper(): return row[idx]
    return None
def get_vessel_col(row, base, idx, suffix):
    t1 = f"{base}:{idx}: {suffix}".upper()
    sa_suffix = suffix
    if base == "PUBLISHER" and suffix == "Name": sa_suffix = "Company"
    if suffix == "Owner Performance Share %": sa_suffix = "Ownership Share"
    if suffix == "IPI": sa_suffix = "CAE/IPI"
    t2 = f"{base} {idx} {sa_suffix}".upper()
    for c in row.index:
        sc = str(c).upper()
        if t1 in sc: return row[c]
        if t2 in sc: return row[c]
    return None

def generate_cwr_content(df, agreement_map=None):
    # Clean headers to remove BOM and quotes
    df.columns = [c.replace('ï»¿', '').replace('"', '').strip() for c in df.columns]
    
    lines = []; engine = FormatterEngine(); now = datetime.now()
    full_ipi = pad_ipi(LUMINA_CONFIG["ipi"])
    # Use passed map (from Secrets) or default to global import (likely empty in prod)
    active_map = agreement_map if agreement_map is not None else AGREEMENT_MAP
    warnings = []

    lines.append(engine.build("HDR", {"sender_ipi_short": full_ipi[-9:], "sender_name": LUMINA_CONFIG["name"], "date": now.strftime("%Y%m%d"), "time": now.strftime("%H%M%S")}))
    lines.append(engine.build("GRH", {}))
    t_count = 0
    for i, row in df.iterrows():
        t_count += 1; t_seq = f"{(t_count-1):08d}"; rec_seq = 1; pub_map = {}
        title_val = str(find_col(row, ['TRACK: Title', 'Title', 'Track Title']) or 'UNKNOWN')
        work_id = str(find_col(row, ['TRACK: Number', 'Track Number']) or (i+1))
        iswc_raw = str(find_col(row, ['CODE: ISWC', 'ISWC']) or '')
        iswc = re.sub(r'[^A-Z0-9]', '', iswc_raw.upper())
        dur_raw = find_col(row, ['TRACK: Duration', 'Length', 'Duration']) or '0'
        
        base_dict = {"title": title_val}
        
        lines.append(engine.build("NWR", {**base_dict, "t_seq": t_seq, "work_id": work_id, "iswc": iswc, "duration": parse_duration(dur_raw)}))
        for p_idx in range(1, 4):
             p_name = get_vessel_col(row, "PUBLISHER", p_idx, "Name")
             if not p_name or pd.isna(p_name) or str(p_name).upper() == 'NAN': continue
             p_name = str(p_name).strip(); agr = ""
             
             # Lookup logic with strict stripping
             for k, v in active_map.items():
                 if str(k).strip().upper() in p_name.upper(): 
                     agr = v; break
             
             if not agr:
                 raise ValueError(f"CRITICAL: Missing Agreement Number for Publisher '{p_name}'. Automation halted.")

             pr_share = fmt_share(get_vessel_col(row, "PUBLISHER", p_idx, "Owner Performance Share %"))
             lines.append(engine.build("SPU", {**base_dict, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}", "pub_id": f"00000000{p_idx}", "pub_name": p_name, "role": "E ", "ipi": pad_ipi(get_vessel_col(row, "PUBLISHER", p_idx, "IPI")), "pr_soc": "021", "mr_soc": "021", "sr_soc": "   ", "pr_share": pr_share, "mr_share": "10000", "sr_share": "10000", "agreement": agr}))
             rec_seq += 1
             lum_id = "000000012"
             lines.append(engine.build("SPU", {**base_dict, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}", "pub_id": lum_id, "pub_name": LUMINA_CONFIG['name'], "role": "SE", "ipi": full_ipi, "pr_soc": "052", "mr_soc": "033", "sr_soc": "033", "pr_share": "00000", "mr_share": "00000", "sr_share": "00000", "agreement": agr}))
             rec_seq += 1
             lines.append(engine.build("SPT", {**base_dict, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": lum_id, "pr_share": pr_share, "mr_share": "10000", "sr_share": "10000", "territory": LUMINA_CONFIG['territory']}))
             rec_seq += 1
             pub_map[p_name.upper()] = {"chain": f"{p_idx:02d}", "id": f"00000000{p_idx}", "agr": agr}
        for w_idx in range(1, 4):
            w_last = get_vessel_col(row, "WRITER", w_idx, "Last Name")
            if not w_last or pd.isna(w_last) or str(w_last).upper() == 'NAN': continue
            w_share = fmt_share(get_vessel_col(row, "WRITER", w_idx, "Owner Performance Share %"))
            lines.append(engine.build("SWR", {**base_dict, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}", "last_name": str(w_last), "first_name": str(get_vessel_col(row, "WRITER", w_idx, "First Name") or ""), "ipi": pad_ipi(get_vessel_col(row, "WRITER", w_idx, "IPI")), "pr_soc": "021", "mr_soc": "099", "sr_soc": "099", "pr_share": w_share, "mr_share": "00000", "sr_share": "00000"})); rec_seq += 1
            lines.append(engine.build("SWT", {**base_dict, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}", "pr_share": w_share, "mr_share": "00000", "sr_share": "00000"})); rec_seq += 1
            orig_pub = str(get_vessel_col(row, "WRITER", w_idx, "Original Publisher") or "").strip().upper()
            if orig_pub in pub_map:
                p_i = pub_map[orig_pub]
                lines.append(engine.build("PWR", {**base_dict, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": p_i['id'], "pub_name": orig_pub[:45], "agreement": p_i['agr'], "writer_id": f"00000000{w_idx}", "chain_id": p_i['chain']})); rec_seq += 1
        isrc = str(find_col(row, ['CODE: ISRC', 'ISRC']) or '')
        cd = str(find_col(row, ['ALBUM: Code', 'Album Code', 'Catalog']) or 'RC055')
        
        # Dynamic Label Lookup (Step 549)
        # 1. Try 'LIBRARY: Name'
        # 2. Try 'Label'
        # 3. Try 'Publisher' (first one found if any, though find_col usually takes list)
        # 4. Fallback: "LUMINA"
        label_val = str(find_col(row, ['LIBRARY: Name', 'Label']) or 'LUMINA').strip()
        # Ensure we don't carry over 'nan' string
        if label_val.upper() == 'NAN': label_val = "LUMINA"
        
        # Specific Normalization for known camelCase from Harvest
        if label_val.upper() == "REDCOLA": label_val = "RED COLA"

        # Dual REC Generation (Unified Source of Truth: Source C and D)
        # Source 'C' (Physical): Includes CD_ID
        lines.append(engine.build("REC", {**base_dict, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "isrc": isrc, "cd_id": cd, "source": "C", "label": label_val})); rec_seq += 1
        # Source 'D' (Digital): Blank CD_ID
        lines.append(engine.build("REC", {**base_dict, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "isrc": isrc, "cd_id": "              ", "source": "D", "label": label_val})); rec_seq += 1
        # Cut Number Logic: Scrub to strict 4-digit numeric (Use Track # if valid, else Seq)
        try: cut_num = f"{int(float(work_id)):04d}"
        except: cut_num = f"{(i+1):04d}"
        lines.append(engine.build("ORN", {**base_dict, "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "library": label_val, "cd_id": cd, "cut_number": cut_num, "label": label_val})); rec_seq += 1
    grp_count = len(lines)
    lines.append(engine.build("GRT", {"t_count": f"{t_count:08d}", "r_count": f"{grp_count:08d}"}))
    total_count = len(lines) + 1
    lines.append(engine.build("TRL", {"t_count": f"{t_count:08d}", "r_count": f"{total_count:08d}"}))
    return "\r\n".join(lines) + "\r\n", warnings
