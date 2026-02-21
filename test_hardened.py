import pandas as pd
from cwr_engine import generate_cwr_content
from cwr_validator import CWRValidator

# Generate a flawless CWR record
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
    'WRITER:1: Original Publisher': ['LUMINA PUBLISHING UK'],
    'ALBUM: Code': ['RC055'],
    'LIBRARY: Name': ['LUMINA']
}
df = pd.DataFrame(data)
test_map = {'LUMINA PUBLISHING UK': '4316161'}

cwr, _ = generate_cwr_content(df, agreement_map=test_map)

# 1. Test Flawless
validator = CWRValidator()
report, stats = validator.process_file(cwr, expected_catalog="LUMINA")
if len(report) == 0:
    print("SUCCESS: Flawless CWR passed Hardened Validator without errors.")
else:
    print("FAILED: Flawless CWR threw an error:")
    print(report[0])
    exit(1)

# 2. Test Flawed SPU Spacing
flawed_cwr = cwr.replace('   10000 N            4316161       PG', '   10000N             4316161       PG')
report, stats = validator.process_file(flawed_cwr, expected_catalog="LUMINA")
if len(report) > 0 and 'Column Index [131:138]' in report[0]['message']:
    print("SUCCESS: Validator successfully halted on flawed SPU spacing.")
else:
    print("FAILED: Validator missed flawed SPU spacing.")
    exit(1)

# 3. Test Flawed PWR Blank Agreement
flawed_cwr2 = cwr.replace('4316161       ', '              ')
report, stats = validator.process_file(flawed_cwr2, expected_catalog="LUMINA")
if len(report) > 0 and 'Column Index [73:87]' in report[0]['message']:
    print("SUCCESS: Validator successfully halted on blank PWR agreement number.")
else:
    print("FAILED: Validator missed blank PWR agreement.")
    exit(1)
