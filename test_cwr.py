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
    
    # Valid: 60 char title exactly matches
    csv_row_valid = {'TRACK: TITLE': 'A' * 60}
    cwr_line_valid = ' ' * 19 + 'A' * 60 + ' ' * 100
    assert validator.validate_row_match(cwr_line_valid, csv_row_valid) == True
    
    # Invalid: 61 char title truncated in CWR to 60 must explicitly fail CSV validation
    csv_row_invalid = {'TRACK: TITLE': 'A' * 61}
    cwr_line_invalid = ' ' * 19 + 'A' * 60 + ' ' * 100
    assert validator.validate_row_match(cwr_line_invalid, csv_row_invalid) == False

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
