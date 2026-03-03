# LOCKED_ARCHITECTURE

This document serves as the absolute, single source of truth for the Lumina CWR Suite geometry, schema mapping, and validation logic. **No fuzzy logic, guessing, or silent fallbacks are permitted.**

If any file in the suite drifts from this specification, the Agent must immediately say: **"AGENT: RE-ALIGN TO LOCKED_ARCHITECTURE.md"** and rewrite the affected files to match this specification exactly.

## 1. The Immutable `cwr_schema.py`

The 182-character geometry must be strictly enforced.

*   `NWR`, `SPU`, `SWR`, `SPT`, and `SWT` must exactly equal 182 characters.
*   **SPU Suffixes:** SPU records must explicitly map:
    *   `agreement` to Position 141 (Length 14).
    *   `P` to Position 161 (Length 1).
    *   `G` to Position 162 (Length 1).
    *   `4316161` to Position 163 (Length 7).
*   **REC Source:** The REC record `source` field must be at Position 263 with a length of `2`.

## 2. The Zero-Guess `cwr_engine.py`

*   **Header Normalization:** The engine must strictly format headers to uppercase and strip whitespace. It must map `WORK TITLE` to `TRACK: TITLE` if the Harvest CSV format is detected.
*   **Strict Mapping:** Data extraction must exclusively use exact keys: `row['TRACK: TITLE']`, `row['CODE: ISRC']`, `row['ALBUM: CODE']`, `row['LIBRARY: NAME']`.
*   **KeyError Halt:** If any REQUIRED column is missing, the engine MUST halt and throw a `KeyError`. No fuzzy `find_col` logic is allowed.
*   **Single REC Source:** The engine will generate exactly one `REC` record per work with the `source` strictly set to `"CD"`. The dual "C" and "D" logic is permanently abolished.

## 3. The Mirror Audit `cwr_validator.py`

The validator acts as a Contextual Truth Checker, not just a syntax evaluator.

*   **Geometry Audit:** The validator will explicitly halt and flag a `CRITICAL` error if any `NWR`, `SWR`, `SWT`, `SPU`, or `SPT` record length does not exactly equal 182 characters.
*   **CD Source Lock:** It will verify that the source field at Position 262:264 of every `REC` record is exactly `'CD'`.
*   **Header Target:** The validator MUST perform the same header normalization and metadata-skipping logic as the engine to find the true DataFrame headers.
*   **Zero-Truncation Match:** It will verify that the count of generated `NWR` records exactly matches the count of CSV rows. It will then cross-check the title of each `NWR` line against the source CSV `['TRACK: TITLE']`.
*   **Truncation Rule:** The CWR limit for Titles is 60 characters. If the source CSV title exceeds 60 characters, it triggers a `CRITICAL_MISMATCH` because silent truncations are prohibited.

## 4. The Gatekeeper `streamlit_app.py`

*   **Single-Source Audit:** The `PRE-FLIGHT` check must verify that the count of `'CD'` source `REC` records equals the exact count of `NWR` records.
*   **Required Checks:** The `streamlit_app.py` must validate `TRACK: TITLE`, `CODE: ISRC`, `ALBUM: CODE`, and `LIBRARY: NAME` prior to execution.
*   **Mirror Audit UI:** The Validator tab must accept an optional `csv_source` file to activate the Contextual Mirror Audit in `cwr_validator.py`.
