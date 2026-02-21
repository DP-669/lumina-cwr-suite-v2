import pandas as pd
from cwr_engine import generate_cwr_content

data = {
    'TRACK: Title': ['Valid Title'],
    'TRACK: Number': [1],
    'CODE: ISWC': ['T-123.456.789-0'],
    'TRACK: Duration': ['3:45'],
    'PUBLISHER:1: Name': ['LUMINA PUBLISHING UK'],
    'PUBLISHER:1: Owner Performance Share %': [100],
    'PUBLISHER:1: IPI': ['12345678901'],
    'WRITER:1: Last Name': ['SMITH'],
    'WRITER:1: Owner Performance Share %': [100],
    'WRITER:1: IPI': ['12345678901'],
    'ALBUM: Code': ['RC055'],
    'LIBRARY: Name': ['LUMINA']
}
df = pd.DataFrame(data)
test_map = {'LUMINA PUBLISHING UK': '4316161'}

try:
    cwr, warnings = generate_cwr_content(df, agreement_map=test_map)
    lines = cwr.replace('\r\n', '\n').split('\n')
    lines = [l for l in lines if l.strip()]
    
    errors = []
    
    spu_lines = [l for l in lines if l.startswith('SPU')]
    for i, l in enumerate(spu_lines):
        if len(l) != 166:
            errors.append(f"SPU line {i} length is {len(l)}, expected 166")
        if '10000 N' not in l and i == 0:
            errors.append(f"SPU line {i} is missing '10000 N' with correct spacing: {l}")
            
    rec_lines = [l for l in lines if l.startswith('REC')]
    for i, l in enumerate(rec_lines):
        if len(l) != 508:
            errors.append(f"REC line {i} length is {len(l)}, expected 508")
    
    pwr_lines = [l for l in lines if l.startswith('PWR')]
    for i, l in enumerate(pwr_lines):
        if '4316161' not in l:
            errors.append(f"PWR line {i} is missing '4316161': {l}")
    
    if errors:
        for err in errors: print(err)
        exit(1)
    
    print("SUCCESS: Valid data processed into exactly sized lines (SPU=166, REC=508).")
    print("PROVEN: '10000 N' correctly spaced in SPU row.")
    print("PROVEN: '4316161' is present in the PWR row.")
    for l in spu_lines: print(l)
    for l in pwr_lines: print(l)
    exit(0)
except Exception as e:
    print(f"FAILED on valid data: {e}")
    exit(1)
