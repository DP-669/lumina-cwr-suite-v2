from dataclasses import dataclass
from typing import List, Dict

@dataclass
class FieldDef:
    name: str 
    start: int        # LITERAL MANUAL POSITION (1-Based)
    length: int
    data_type: str = "alphanumeric" 
    pad_char: str = " "
    is_constant: bool = False

@dataclass
class RecordDef:
    type: str
    length: int
    fields: List[FieldDef]

CWR_SCHEMA: Dict[str, RecordDef] = {
    "HDR": RecordDef("HDR", 108, [
        FieldDef("HDR", 1, 3, is_constant=True),
        FieldDef("01", 4, 2, is_constant=True),
        FieldDef("sender_ipi_short", 6, 9, data_type="numeric"),
        FieldDef("sender_name", 15, 45, data_type="alphanumeric"),
        FieldDef("01.10", 60, 5, is_constant=True),
        FieldDef("creation_date", 65, 8), 
        FieldDef("creation_time", 73, 6),
        FieldDef("transmission_date", 79, 8), 
        FieldDef("2.200", 102, 5, is_constant=True)
    ]),
    "GRH": RecordDef("GRH", 112, [
        FieldDef("GRH", 1, 3, is_constant=True),
        FieldDef("NWR", 4, 3, is_constant=True),
        FieldDef("00001", 7, 5, is_constant=True),
        FieldDef("02.20", 12, 5, is_constant=True),
        FieldDef("0000000000", 17, 10, is_constant=True)
    ]),
    "NWR": RecordDef("NWR", 182, [
        FieldDef("NWR", 1, 3, is_constant=True),
        FieldDef("t_seq", 4, 8, data_type="numeric"),
        FieldDef("00000000", 12, 8, is_constant=True),
        FieldDef("title", 20, 60, data_type="alphanumeric"),
        FieldDef("  ", 80, 2, is_constant=True),
        FieldDef("work_id", 82, 14, data_type="alphanumeric"),
        FieldDef("iswc", 96, 11, data_type="alphanumeric"),
        FieldDef("00000000", 107, 8, is_constant=True),
        FieldDef("UNC", 127, 3, is_constant=True),
        FieldDef("duration", 130, 6, data_type="numeric"),
        FieldDef("Y", 136, 1, is_constant=True),
        FieldDef("ORI", 143, 3, is_constant=True)
    ]),
    "SPU": RecordDef("SPU", 182, [
        FieldDef("SPU", 1, 3, is_constant=True),
        FieldDef("t_seq", 4, 8, data_type="numeric"),
        FieldDef("rec_seq", 12, 8, data_type="numeric"),
        FieldDef("chain_id", 20, 2, data_type="numeric"),
        FieldDef("pub_id", 22, 9, data_type="alphanumeric"),
        FieldDef("pub_name", 31, 45, data_type="alphanumeric"),
        FieldDef("role", 77, 2, data_type="alphanumeric"),
        FieldDef("ipi", 88, 11, data_type="alphanumeric"),
        FieldDef("pr_soc", 113, 3, data_type="alphanumeric"),
        FieldDef("pr_share", 116, 5, data_type="numeric"),
        FieldDef("mr_soc", 121, 3, data_type="alphanumeric"),
        FieldDef("mr_share", 124, 5, data_type="numeric"),
        FieldDef("sr_soc", 129, 3, data_type="alphanumeric"),
        FieldDef("sr_share", 132, 5, data_type="numeric"),
        FieldDef("N", 138, 1, is_constant=True)
    ]),
    "SPT": RecordDef("SPT", 182, [
        FieldDef("SPT", 1, 3, is_constant=True),
        FieldDef("t_seq", 4, 8, data_type="numeric"),
        FieldDef("rec_seq", 12, 8, data_type="numeric"),
        FieldDef("pub_id", 20, 9, data_type="alphanumeric"),
        FieldDef("pr_share", 35, 5, data_type="numeric"),
        FieldDef("mr_share", 40, 5, data_type="numeric"),
        FieldDef("sr_share", 45, 5, data_type="numeric"),
        FieldDef("I", 50, 1, is_constant=True),
        FieldDef("territory", 51, 4, data_type="alphanumeric"),
        FieldDef("001", 56, 3, is_constant=True)
    ]),
    "SWR": RecordDef("SWR", 182, [
        FieldDef("SWR", 1, 3, is_constant=True),
        FieldDef("t_seq", 4, 8, data_type="numeric"),
        FieldDef("rec_seq", 12, 8, data_type="numeric"),
        FieldDef("writer_id", 20, 9, data_type="alphanumeric"),
        FieldDef("last_name", 29, 45, data_type="alphanumeric"),
        FieldDef("first_name", 74, 30, data_type="alphanumeric"),
        FieldDef("C ", 105, 2, is_constant=True),
        FieldDef("ipi", 116, 11, data_type="alphanumeric"),
        FieldDef("pr_soc", 127, 3, data_type="alphanumeric"),
        FieldDef("pr_share", 130, 5, data_type="numeric"),
        FieldDef("mr_soc", 135, 3, data_type="alphanumeric"),
        FieldDef("mr_share", 138, 5, data_type="numeric"),
        FieldDef("sr_soc", 143, 3, data_type="alphanumeric"),
        FieldDef("sr_share", 146, 5, data_type="numeric"),
        FieldDef("N", 152, 1, is_constant=True)
    ]),
    "SWT": RecordDef("SWT", 182, [
        FieldDef("SWT", 1, 3, is_constant=True),
        FieldDef("t_seq", 4, 8, data_type="numeric"),
        FieldDef("rec_seq", 12, 8, data_type="numeric"),
        FieldDef("writer_id", 20, 9, data_type="alphanumeric"),
        FieldDef("pr_share", 29, 5, data_type="numeric"),
        FieldDef("mr_share", 34, 5, data_type="numeric"),
        FieldDef("sr_share", 39, 5, data_type="numeric"),
        FieldDef("I", 44, 1, is_constant=True),
        FieldDef("2136", 45, 4, is_constant=True),
        FieldDef("001", 50, 3, is_constant=True)
    ]),
    "PWR": RecordDef("PWR", 112, [
        FieldDef("PWR", 1, 3, is_constant=True),
        FieldDef("t_seq", 4, 8, data_type="numeric"),
        FieldDef("rec_seq", 12, 8, data_type="numeric"),
        FieldDef("pub_id", 20, 9, data_type="alphanumeric"),
        FieldDef("pub_name", 29, 45, data_type="alphanumeric"),
        FieldDef("agreement", 74, 14, data_type="alphanumeric"),
        FieldDef("writer_id", 102, 9, data_type="alphanumeric"),
        FieldDef("chain_id", 111, 2, data_type="numeric")
    ]),
    "REC": RecordDef("REC", 508, [
        FieldDef("REC", 1, 3, is_constant=True),
        FieldDef("t_seq", 4, 8, data_type="numeric"),
        FieldDef("rec_seq", 12, 8, data_type="numeric"),
        FieldDef("cd_id", 219, 15, data_type="alphanumeric"),
        FieldDef("isrc", 250, 12, data_type="alphanumeric"),
        FieldDef("source", 263, 1, data_type="alphanumeric"),
        FieldDef("Y", 507, 1, is_constant=True), 
        FieldDef("label", 446, 60, data_type="alphanumeric")
    ]),
    "ORN": RecordDef("ORN", 160, [
        FieldDef("ORN", 1, 3, is_constant=True),
        FieldDef("t_seq", 4, 8, data_type="numeric"),
        FieldDef("rec_seq", 12, 8, data_type="numeric"),
        FieldDef("LIB", 20, 3, is_constant=True),
        FieldDef("library", 23, 60, data_type="alphanumeric"),
        FieldDef("cd_id", 83, 15, data_type="alphanumeric"),
        FieldDef("cut_number", 98, 4, data_type="numeric"), 
        FieldDef("label", 102, 60, data_type="alphanumeric") 
    ]),
    "GRT": RecordDef("GRT", 24, [
        FieldDef("GRT", 1, 3, is_constant=True),
        FieldDef("00001", 4, 5, is_constant=True),
        FieldDef("t_count", 9, 8, data_type="numeric"),
        FieldDef("r_count", 17, 8, data_type="numeric")
    ]),
    "TRL": RecordDef("TRL", 24, [
        FieldDef("TRL", 1, 3, is_constant=True),
        FieldDef("00001", 4, 5, is_constant=True),
        FieldDef("t_count", 9, 8, data_type="numeric"),
        FieldDef("r_count", 17, 8, data_type="numeric")
    ])
}
