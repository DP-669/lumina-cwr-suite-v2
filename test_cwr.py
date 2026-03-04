import pytest
import pandas as pd
from cwr_schema import CWR_SCHEMA
from cwr_validator import CWRValidator

def test_schema_geometry():
    """Verify that all symmetry-group schemas are strictly 182 characters long."""
    assert CWR_SCHEMA["NWR"].length == 182
    assert CWR_SCHEMA["SPU"].length == 182
    assert CWR_SCHEMA["SWR"].length == 182
    assert CWR_SCHEMA["SPT"].length == 182
    assert CWR_SCHEMA["SWT"].length == 182

def test_spu_suffixes():
    """Verify that SPU suffixes conform to exact physical positions required."""
    spu_fields = {f.name: f for f in CWR_SCHEMA["SPU"].fields}
    
    assert spu_fields["agreement"].start == 141
    assert spu_fields["agreement"].length == 14
    
    assert spu_fields["P"].start == 161
    assert spu_fields["P"].length == 1
    
    assert spu_fields["G"].start == 162
    assert spu_fields["G"].length == 1
    
    assert spu_fields["4316161"].start == 163
    assert spu_fields["4316161"].length == 7

def test_rec_source_lock():
    """Verify that REC record defines a single CD source at exact coordinates."""
    rec_fields = {f.name: f for f in CWR_SCHEMA["REC"].fields}
    assert rec_fields["source"].start == 263
    assert rec_fields["source"].length == 2

def test_zero_truncation_mirror_audit():
    """Verify the validator throws contextual mismatch on titles > 60 chars."""
    validator = CWRValidator()
    
    # Valid: 60 char title exactly matches length
    csv_valid = "TRACK: TITLE,ALBUM: CODE,CODE: ISRC,LIBRARY: NAME\n" + ("A" * 60) + ",ALB1,USX1,LIB1\n"
    cwr_nwr_valid = "NWR" + " " * 16 + ("A" * 60) + " " * (182 - 3 - 16 - 60)
    rep, _ = validator.process_file(cwr_nwr_valid, csv_content=csv_valid.encode('utf-8'))
    assert not any("CRITICAL_MISMATCH" in r["message"] for r in rep)
    
    # Invalid: 61 char title must explicitly fail CSV validation
    csv_invalid = "TRACK: TITLE,ALBUM: CODE,CODE: ISRC,LIBRARY: NAME\n" + ("A" * 61) + ",ALB1,USX1,LIB1\n"
    cwr_nwr_invalid = "NWR" + " " * 16 + ("A" * 60) + " " * (182 - 3 - 16 - 60)
    rep, _ = validator.process_file(cwr_nwr_invalid, csv_content=csv_invalid.encode('utf-8'))
    assert any("CRITICAL_MISMATCH" in r["message"] for r in rep)

def test_validator_cd_source():
    """Verify the validator flags mismatched REC sources."""
    validator = CWRValidator()
    
    # Correct format
    rec_line_cd = "REC" + " " * 259 + "CD" + " " * 243
    report, _ = validator.process_file(rec_line_cd)
    assert not any("REC Source must be 'CD'" in item['message'] for item in report)
    
    # Incorrect format
    rec_line_bad = "REC" + " " * 259 + "OT" + " " * 243
    report, _ = validator.process_file(rec_line_bad)
    assert any("REC Source must be 'CD'" in item['message'] for item in report)
