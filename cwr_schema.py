from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class FieldDef:
    name: str # Key in data_dict, or the constant value if is_constant=True
    start: int
    length: int
    data_type: str = "alphanumeric" # 'alphanumeric' (left aligned) or 'numeric' (right aligned)
    pad_char: str = " "
    is_constant: bool = False

@dataclass
class RecordDef:
    type: str
    length: int
    fields: List[FieldDef]

# Master Schema mapped by Record Type
CWR_SCHEMA: Dict[str, RecordDef] = {
    "HDR": RecordDef("HDR", 108, [
        FieldDef("HDR", 0, 3, is_constant=True),
        FieldDef("01", 3, 2, is_constant=True),
        FieldDef("sender_ipi_short", 5, 9, data_type="numeric", pad_char="0"),
        FieldDef("sender_name", 14, 45, data_type="alphanumeric", pad_char=" "),
        FieldDef("01.10", 61, 5, is_constant=True),
        FieldDef("date", 66, 8, is_constant=True), # Passed from dict as "date"
        FieldDef("time", 74, 6, is_constant=True),
        FieldDef("date", 80, 8, is_constant=True), 
        FieldDef("2.200", 103, 5, is_constant=True)
    ]),
    "GRH": RecordDef("GRH", 26, [
        FieldDef("GRH", 0, 3, is_constant=True),
        FieldDef("NWR", 3, 3, is_constant=True),
        FieldDef("00001", 6, 5, is_constant=True),
        FieldDef("02.20", 11, 5, is_constant=True),
        FieldDef("0000000000", 16, 10, is_constant=True)
    ]),
    "NWR": RecordDef("NWR", 145, [
        FieldDef("NWR", 0, 3, is_constant=True),
        FieldDef("t_seq", 3, 8, data_type="numeric", pad_char="0"),
        FieldDef("00000000", 11, 8, is_constant=True),
        FieldDef("title", 19, 60, data_type="alphanumeric", pad_char=" "),
        FieldDef("  ", 79, 2, is_constant=True),
        FieldDef("work_id", 81, 14, data_type="alphanumeric", pad_char=" "),
        FieldDef("iswc", 95, 11, data_type="alphanumeric", pad_char=" "),
        FieldDef("00000000", 106, 8, is_constant=True),
        FieldDef("UNC", 126, 3, is_constant=True),
        FieldDef("duration", 129, 6, data_type="numeric", pad_char="0"),
        FieldDef("Y", 135, 1, is_constant=True),
        FieldDef("ORI", 142, 3, is_constant=True)
    ]),
    "SPU": RecordDef("SPU", 166, [
        FieldDef("SPU", 0, 3, is_constant=True),
        FieldDef("t_seq", 3, 8, data_type="numeric", pad_char="0"),
        FieldDef("rec_seq", 11, 8, data_type="numeric", pad_char="0"),
        FieldDef("chain_id", 19, 2, data_type="numeric", pad_char="0"),
        FieldDef("pub_id", 21, 9, data_type="alphanumeric", pad_char=" "),
        FieldDef("pub_name", 30, 45, data_type="alphanumeric", pad_char=" "),
        FieldDef(" ", 75, 1, is_constant=True),
        FieldDef("role", 76, 2, data_type="alphanumeric", pad_char=" "),
        FieldDef("         ", 78, 9, is_constant=True),
        FieldDef("ipi", 87, 11, data_type="alphanumeric", pad_char=" "),
        FieldDef("              ", 98, 14, is_constant=True),
        FieldDef("pr_soc", 112, 3, data_type="alphanumeric", pad_char=" "),
        FieldDef("pr_share", 115, 5, data_type="numeric", pad_char="0"),
        FieldDef("mr_soc", 120, 3, data_type="alphanumeric", pad_char=" "),
        FieldDef("mr_share", 123, 5, data_type="numeric", pad_char="0"),
        FieldDef("sr_soc", 128, 3, data_type="alphanumeric", pad_char=" "),
        FieldDef("sr_share", 131, 5, data_type="numeric", pad_char="0"),
        FieldDef(" ", 136, 1, is_constant=True),
        FieldDef("N", 137, 1, is_constant=True),
        FieldDef("            ", 138, 12, is_constant=True),
        FieldDef("agreement", 150, 14, data_type="alphanumeric", pad_char=" "),
        FieldDef("PG", 164, 2, is_constant=True)
    ]),
    "SPT": RecordDef("SPT", 58, [
        FieldDef("SPT", 0, 3, is_constant=True),
        FieldDef("t_seq", 3, 8, data_type="numeric", pad_char="0"),
        FieldDef("rec_seq", 11, 8, data_type="numeric", pad_char="0"),
        FieldDef("pub_id", 19, 9, data_type="alphanumeric", pad_char=" "),
        FieldDef("pr_share", 34, 5, data_type="numeric", pad_char="0"),
        FieldDef("mr_share", 39, 5, data_type="numeric", pad_char="0"),
        FieldDef("sr_share", 44, 5, data_type="numeric", pad_char="0"),
        FieldDef("I", 49, 1, is_constant=True),
        FieldDef("territory", 50, 4, data_type="alphanumeric", pad_char=" "),
        FieldDef("001", 55, 3, is_constant=True)
    ]),
    "SWR": RecordDef("SWR", 152, [
        FieldDef("SWR", 0, 3, is_constant=True),
        FieldDef("t_seq", 3, 8, data_type="numeric", pad_char="0"),
        FieldDef("rec_seq", 11, 8, data_type="numeric", pad_char="0"),
        FieldDef("writer_id", 19, 9, data_type="alphanumeric", pad_char=" "),
        FieldDef("last_name", 28, 45, data_type="alphanumeric", pad_char=" "),
        FieldDef("first_name", 73, 30, data_type="alphanumeric", pad_char=" "),
        FieldDef("C ", 104, 2, is_constant=True),
        FieldDef("ipi", 115, 11, data_type="alphanumeric", pad_char=" "),
        FieldDef("pr_soc", 126, 3, data_type="alphanumeric", pad_char=" "),
        FieldDef("pr_share", 129, 5, data_type="numeric", pad_char="0"),
        FieldDef("mr_soc", 134, 3, data_type="alphanumeric", pad_char=" "),
        FieldDef("mr_share", 137, 5, data_type="numeric", pad_char="0"),
        FieldDef("sr_soc", 142, 3, data_type="alphanumeric", pad_char=" "),
        FieldDef("sr_share", 145, 5, data_type="numeric", pad_char="0"),
        FieldDef("N", 151, 1, is_constant=True)
    ]),
    "SWT": RecordDef("SWT", 52, [
        FieldDef("SWT", 0, 3, is_constant=True),
        FieldDef("t_seq", 3, 8, data_type="numeric", pad_char="0"),
        FieldDef("rec_seq", 11, 8, data_type="numeric", pad_char="0"),
        FieldDef("writer_id", 19, 9, data_type="alphanumeric", pad_char=" "),
        FieldDef("pr_share", 28, 5, data_type="numeric", pad_char="0"),
        FieldDef("mr_share", 33, 5, data_type="numeric", pad_char="0"),
        FieldDef("sr_share", 38, 5, data_type="numeric", pad_char="0"),
        FieldDef("I", 43, 1, is_constant=True),
        FieldDef("2136", 44, 4, is_constant=True),
        FieldDef("001", 49, 3, is_constant=True)
    ]),
    "PWR": RecordDef("PWR", 112, [
        FieldDef("PWR", 0, 3, is_constant=True),
        FieldDef("t_seq", 3, 8, data_type="numeric", pad_char="0"),
        FieldDef("rec_seq", 11, 8, data_type="numeric", pad_char="0"),
        FieldDef("pub_id", 19, 9, data_type="alphanumeric", pad_char=" "),
        FieldDef("pub_name", 28, 45, data_type="alphanumeric", pad_char=" "),
        FieldDef("agreement", 73, 14, data_type="alphanumeric", pad_char=" "),
        FieldDef("              ", 87, 14, is_constant=True),
        FieldDef("writer_id", 101, 9, data_type="alphanumeric", pad_char=" "),
        FieldDef("chain_id", 110, 2, data_type="numeric", pad_char="0")
    ]),
    "REC": RecordDef("REC", 508, [
        FieldDef("REC", 0, 3, is_constant=True),
        FieldDef("t_seq", 3, 8, data_type="numeric", pad_char="0"),
        FieldDef("rec_seq", 11, 8, data_type="numeric", pad_char="0"),
        FieldDef(" " * 199, 19, 199, is_constant=True),
        FieldDef("cd_id", 218, 14, data_type="alphanumeric", pad_char=" "),
        FieldDef(" " * 16, 232, 16, is_constant=True),
        FieldDef("isrc", 248, 12, data_type="alphanumeric", pad_char=" "),
        FieldDef("  ", 260, 2, is_constant=True),
        FieldDef("source", 262, 1, data_type="alphanumeric", pad_char=" "),
        FieldDef(" " * 182, 263, 182, is_constant=True),
        FieldDef("label", 445, 60, data_type="alphanumeric", pad_char=" "),
        FieldDef("   ", 505, 3, is_constant=True)
    ]),
    "ORN": RecordDef("ORN", 160, [
        FieldDef("ORN", 0, 3, is_constant=True),
        FieldDef("t_seq", 3, 8, data_type="numeric", pad_char="0"),
        FieldDef("rec_seq", 11, 8, data_type="numeric", pad_char="0"),
        FieldDef("LIB", 19, 3, is_constant=True),
        FieldDef("library", 22, 60, data_type="alphanumeric", pad_char=" "),
        FieldDef("cd_id", 82, 14, data_type="alphanumeric", pad_char=" "),
        FieldDef("cut_number", 96, 4, data_type="numeric", pad_char="0"),
        FieldDef("label", 100, 60, data_type="alphanumeric", pad_char=" ")
    ]),
    "GRT": RecordDef("GRT", 24, [
        FieldDef("GRT", 0, 3, is_constant=True),
        FieldDef("00001", 3, 5, is_constant=True),
        FieldDef("t_count", 8, 8, data_type="numeric", pad_char="0"),
        FieldDef("r_count", 16, 8, data_type="numeric", pad_char="0")
    ]),
    "TRL": RecordDef("TRL", 24, [
        FieldDef("TRL", 0, 3, is_constant=True),
        FieldDef("00001", 3, 5, is_constant=True),
        FieldDef("t_count", 8, 8, data_type="numeric", pad_char="0"),
        FieldDef("r_count", 16, 8, data_type="numeric", pad_char="0")
    ])
}
