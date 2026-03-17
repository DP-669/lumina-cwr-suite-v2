import pandas as pd
from datetime import datetime
import re
from config import LUMINA_CONFIG, AGREEMENT_MAP
from cwr_schema import CWR_SCHEMA

class FormatterEngine:
    def stamp(self, canvas: list, position: int, length: int, value: str, data_type: str, pad_char: str, field_name: str, data_dict: dict):
        start_idx = position - 1
        val_str = str(value if value is not None else "").strip().upper()
        if val_str in ['NAN', 'NONE']: val_str = ""
        
        # Data Integrity Firewall: Check length BEFORE padding
        if len(val_str) > length:
            track_info = data_dict.get('title', 'Unknown Track')
            raise ValueError(
                f"CRITICAL: Data truncation prevented. Track '{track_info}' - Field '{field_name}' "
                f"exceeds max length of {length}. Automation halted."
            )
            
        if data_type == "numeric":
            padded_val = val_str.zfill(length)[:length]
        else:
            padded_val = val_str.ljust(length, pad_char)[:length]
        for i, char in enumerate(padded_val):
            pos = start_idx + i
            if pos < len(canvas): canvas[pos] = char

    def build(self, record_type: str, data_dict: dict) -> str:
        record_def = CWR_SCHEMA.get(record_type)
        if not record_def: raise ValueError(f"Schema not found for: {record_type}")
        canvas = [' '] * record_def.length
        for field in record_def.fields:
            val = field.name if field.is_constant else data_dict.get(field.name, "")
            self.stamp(canvas, field.start, field.length, val, field.data_type, field.pad_char, field.name, data_dict)
        return "".join(canvas)

def fmt_share(v): 
    try: return f"{int(round(float(v)*100)):05d}"
    except: return "00000"

def pad_ipi(v):
    return re.sub(r'\D', '', str(v)).zfill(11) if v and str(v).upper() != 'NAN' else "00000000000"

def generate_cwr_content(df, agreement_map=None):
    df.columns = [str(c).strip().upper() for c in df.columns]
    REQUIRED = ['TRACK: TITLE', 'CODE: ISRC', 'ALBUM: CODE', 'LIBRARY: NAME']

    for col in REQUIRED:
        if col not in df.columns: raise KeyError(f"MANDATORY COLUMN MISSING: {col}")

    lines = []
    engine = FormatterEngine()
    now = datetime.utcnow()
    full_ipi = str(LUMINA_CONFIG.get("ipi", "00000000000")).zfill(11)
    active_map = agreement_map if agreement_map is not None else AGREEMENT_MAP

    # HDR/GRH
    lines.append(engine.build("HDR", {"sender_ipi_short": full_ipi[-9:], "sender_name": LUMINA_CONFIG.get("name", "LUMINA"), "creation_date": now.strftime("%Y%m%d"), "creation_time": now.strftime("%H%M%S"), "transmission_date": now.strftime("%Y%m%d")}))
    lines.append(engine.build("GRH", {}))

    for i, row in df.iterrows():
        t_seq = f"{i:08d}"
        rec_seq = 1
        pub_map = {}
        
        work_data = {"title": row['TRACK: TITLE'], "t_seq": t_seq, "work_id": f"{i+1:014d}", "isrc": row['CODE: ISRC']}
        lines.append(engine.build("NWR", work_data))
        
        # Publisher Loop
        for p_idx in range(1, 4):
            p_name = str(row.get(f"PUBLISHER:{p_idx}: NAME", "")).strip()
            if not p_name or p_name.upper() in ['NAN', 'NONE']: continue
            
            agr = next((v for k, v in active_map.items() if k.upper() in p_name.upper()), "")
            if not agr: raise KeyError(f"Missing Agreement for '{p_name}'")
            
            pr_share = fmt_share(row.get(f"PUBLISHER:{p_idx}: OWNER PERFORMANCE SHARE %", "0"))
            p_ipi = pad_ipi(row.get(f"PUBLISHER:{p_idx}: IPI", "00000000000"))
            p_pr_soc = str(row.get(f"PUBLISHER:{p_idx}: PRO", "021")).split('.')[0].zfill(3)
            p_mr_soc = str(row.get(f"PUBLISHER:{p_idx}: MRO", "021")).split('.')[0].zfill(3)
            p_mr_soc = str(row.get(f"PUBLISHER:{p_idx}: MRO", "021")).split('.')[0].zfill(3)
            # DO NOT RE-INTRODUCE sr_soc OR sr_share HERE. SPU Share Block must be exactly 16 digits long.
            lines.append(engine.build("SPU", {
                **work_data, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}",
                "pub_id": f"00000000{p_idx}", "pub_name": p_name, "role": "E ", "ipi": p_ipi,
                "pr_soc": p_pr_soc if p_pr_soc != "000" and p_pr_soc.upper() != "NAN" else "021",
                "mr_soc": p_mr_soc if p_mr_soc != "000" and p_mr_soc.upper() != "NAN" else "021",
                # DO NOT RE-INTRODUCE sr_share INTO SPU RECORD
                "pr_share": pr_share, "mr_share": "10000", 
                "agreement_1": agr, "agreement_2": agr
            }))
            rec_seq += 1
            
            lum_id = "000000012"
            lines.append(engine.build("SPU", {
                **work_data, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}",
                "pub_id": lum_id, "pub_name": LUMINA_CONFIG.get('name', 'LUMINA'), "role": "SE", "ipi": full_ipi,
                "pr_soc": "052", "mr_soc": "033", 
                "pr_share": "00000", "mr_share": "00000",
                "agreement_1": agr, "agreement_2": agr
            }))
            rec_seq += 1
            
            lines.append(engine.build("SPT", {
                **work_data, "rec_seq": f"{rec_seq:08d}", "pub_id": lum_id,
                "pr_share": pr_share, "mr_share": "10000", "sr_share": "10000",
                "territory": LUMINA_CONFIG.get('territory', '2136')
            }))
            rec_seq += 1
            
            pub_map[p_name.upper()] = {"chain": f"{p_idx:02d}", "id": f"00000000{p_idx}", "agr": agr}

        # Writer Loop
        for w_idx in range(1, 4):
            w_last = str(row.get(f"WRITER:{w_idx}: LAST NAME", "")).strip()
            if not w_last or w_last.upper() in ['NAN', 'NONE']: continue
            w_first = str(row.get(f"WRITER:{w_idx}: FIRST NAME", "")).strip()
            
            w_share = fmt_share(row.get(f"WRITER:{w_idx}: OWNER PERFORMANCE SHARE %", "0"))
            w_ipi = pad_ipi(row.get(f"WRITER:{w_idx}: IPI", "00000000000"))
            w_pr_soc = str(row.get(f"WRITER:{w_idx}: PRO", "021")).split('.')[0].zfill(3)
            w_mr_soc = str(row.get(f"WRITER:{w_idx}: MRO", "099")).split('.')[0].zfill(3)
            w_sr_soc = str(row.get(f"WRITER:{w_idx}: SRO", "099")).split('.')[0].zfill(3)

            lines.append(engine.build("SWR", {
                **work_data, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}",
                "last_name": w_last, "first_name": "" if w_first.upper() in ["NAN", "NONE"] else w_first,
                "ipi": w_ipi,
                "pr_soc": w_pr_soc if w_pr_soc != "000" and w_pr_soc.upper() != "NAN" else "021",
                "mr_soc": w_mr_soc if w_mr_soc != "000" and w_mr_soc.upper() != "NAN" else "099",
                "sr_soc": w_sr_soc if w_sr_soc != "000" and w_sr_soc.upper() != "NAN" else "099",
                "pr_share": w_share, "mr_share": "00000", "sr_share": "00000"
            }))
            rec_seq += 1
            
            lines.append(engine.build("SWT", {
                **work_data, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}",
                "pr_share": w_share, "mr_share": "00000", "sr_share": "00000"
            }))
            rec_seq += 1
            
            orig_pub = str(row.get(f"WRITER:{w_idx}: ORIGINAL PUBLISHER", "")).strip().upper()
            if orig_pub not in ["", "NAN", "NONE"] and orig_pub in pub_map:
                p_i = pub_map[orig_pub]
                lines.append(engine.build("PWR", {
                    **work_data, "rec_seq": f"{rec_seq:08d}", "pub_id": p_i['id'],
                    "pub_name": orig_pub[:45], "agreement": p_i['agr'], "writer_id": f"00000000{w_idx}",
                    "chain_id": p_i['chain']
                }))
                rec_seq += 1

        label = str(row['LIBRARY: NAME'])
        cat = str(row['ALBUM: CODE'])
        lines.append(engine.build("REC", {**work_data, "rec_seq": f"{rec_seq:08d}", "cd_id": cat, "source": "CD", "label": label}))
        rec_seq += 1
        lines.append(engine.build("ORN", {**work_data, "rec_seq": f"{rec_seq:08d}", "library": label, "cd_id": cat, "cut_number": f"{i+1:04d}", "label": label}))
        
    grp_count = len(lines)
    lines.append(engine.build("GRT", {"t_count": f"{len(df):08d}", "r_count": f"{grp_count:08d}"}))
    lines.append(engine.build("TRL", {"t_count": f"{len(df):08d}", "r_count": f"{grp_count+1:08d}"}))
    return "\r\n".join(lines) + "\r\n", []
