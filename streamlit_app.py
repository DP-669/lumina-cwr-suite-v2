import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import config
import io
import zipfile
import json

try:
    from cwr_engine import generate_cwr_content
    from cwr_validator import CWRValidator
except ImportError as e:
    st.error(f"SYSTEM ERROR: Component missing. {e}")
    st.stop() 

# --- 1. DYNAMIC CONFIGURATION & SECRETS ---
if "LUMINA_CONFIG" in st.secrets:
    LUMINA_CONFIG = st.secrets["LUMINA_CONFIG"]
    AGREEMENT_MAP = st.secrets["AGREEMENT_MAP"]
else:
    LUMINA_CONFIG = config.LUMINA_CONFIG
    AGREEMENT_MAP = config.AGREEMENT_MAP

# --- 2. DEFAULT UI SETUP & CSS ---
st.set_page_config(page_title="Lumina CWR Suite", layout="centered", initial_sidebar_state="collapsed")

# Apple-Centric Custom Styling
st.markdown("""
<style>
    /* Global Background and Fonts */
    .stApp {
        background-color: #FAFAFA;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Center the Main Title */
    .main-title {
        text-align: center;
        font-weight: 700;
        font-size: 3rem;
        color: #1A1A1A;
        margin-bottom: 0px;
        padding-top: 2rem;
    }
    
    /* Subheaders and Validators */
    .sub-title {
        text-align: center;
        font-weight: 500;
        font-size: 1.5rem;
        color: #8C8C8C; /* 65% Gray */
        margin-top: -10px;
        margin-bottom: 30px;
    }
    
    /* Tame the File Uploader */
    .stFileUploader {
        margin: 0 auto;
        max-width: 400px;
    }
    
    /* Colorize the Upload Cloud Icon (Streamlit internal classes) */
    .st-emotion-cache-1gula1e {
        color: #FF9500 !important; /* Apple Orange */
    }

    /* Style the 'Run Inspection' button to pop and pulse */
    .run-btn-container button {
        background-color: #007AFF !important; /* Apple Blue */
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        margin: 0 auto !important;
        display: block !important;
        animation: pulse 2s infinite;
        transition: transform 0.2s ease;
    }
    .run-btn-container button:hover {
        transform: scale(1.05);
        background-color: #005BB5 !important;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 122, 255, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 122, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 122, 255, 0); }
    }
    
    /* Centered Metrics */
    div[data-testid="metric-container"] {
        text-align: center;
    }

    /* Container for Streamlit Tabs */
    div[data-testid="stTabs"] > div[role="tablist"] {
        display: flex;
        justify-content: space-between;
        width: 100%;
        gap: 2rem;
    }
    
    /* Custom Styling for the Tabs */
    button[data-baseweb="tab"] {
        flex: 1 !important;
        height: 60px !important;
        border-radius: 12px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        transition: transform 0.2s ease !important;
        margin: 0 !important;
    }
    button[data-baseweb="tab"]:hover {
        transform: scale(1.05) !important;
    }
    button[data-baseweb="tab"] div[data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: white !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Tab 1: Generate (Vibrant Orange) */
    button[data-baseweb="tab"]:nth-of-type(1) {
        background-color: #FF9500 !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(255, 149, 0, 0.3) !important;
    }
    
    /* Tab 2: Validate (Lush Green) */
    button[data-baseweb="tab"]:nth-of-type(2) {
        background-color: #34C759 !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3) !important;
    }
    
    /* Hide the annoying bottom border line from Streamlit Tabs */
    div[data-testid="stTabs"] > div[role="tablist"] > div {
        display: none !important;
    }

    /* Hide the top header bar and generic Streamlit menu */
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Centered Logo and Title Spacer
st.markdown("<div style='margin-bottom: -1rem;'></div>", unsafe_allow_html=True)
if os.path.exists("lumina_logo.png"):
    _, col_logo, _ = st.columns([1, 2, 1])
    with col_logo:
        st.image("lumina_logo.png", use_container_width=True)

st.markdown("<h1 class='main-title'>Lumina CWR Suite</h1>", unsafe_allow_html=True)

# --- 3. SEQUENCE VAULT LOGIC ---
SEQ_FILE = "cwr_sequence_log.json"
current_year = datetime.now().year

if not os.path.exists(SEQ_FILE):
    with open(SEQ_FILE, 'w') as f:
        json.dump({"year": current_year, "history": []}, f)

with open(SEQ_FILE, 'r') as f:
    seq_data = json.load(f)

if current_year > seq_data.get("year", 0):
    seq_data["year"] = current_year
    seq_data["history"] = []
    with open(SEQ_FILE, 'w') as f:
        json.dump(seq_data, f)

history = seq_data.get("history", [])
next_sequence = max([item["sequence"] for item in history] + [0]) + 1

# --- 4. NAVIGATION TABS ---
st.write("") # Spacer
tab_gen, tab_val = st.tabs(["⚡ Generator", "🛡️ Validator"])

# --- 5. TASK: GENERATOR ---
with tab_gen:
    st.markdown("<h2 class='sub-title'>CWR 2.2 Generator</h2>", unsafe_allow_html=True)
    
    col_left, col_mid, col_right = st.columns([1.5, 1, 1], gap="large")

    with col_mid:
        st.subheader("Sequence Logic")
        st.write("")
        cwr_sequence = st.number_input("Next Sequence Override", min_value=1, max_value=9999, value=int(next_sequence), step=1)
        
        with st.expander("Log Accepted Registration"):
            uploaded_v22 = st.file_uploader("Upload accepted .V22", type=["V22", "cwr"], key="logger_uploader")
            if uploaded_v22:
                filename_up = uploaded_v22.name
                try:
                    seq_str = filename_up[4:8]
                    extracted_seq = int(seq_str)
                except ValueError:
                    extracted_seq = 0
                    
                content = uploaded_v22.getvalue().decode("latin-1")
                lines = content.replace('\r\n', '\n').split('\n')
                library_name = "UNKNOWN"
                album_code = "UNKNOWN"
                for line in lines:
                    if line.startswith("ORN") and len(line) >= 96:
                        library_name = line[22:82].strip()
                        album_code = line[82:96].strip()
                        break
                
                new_label = f"{extracted_seq:04d} {album_code} {library_name}".strip()
                st.write(f"Detected: **{new_label}**")
                
                if st.button("Mark as Officially Accepted"):
                    if not any(item["sequence"] == extracted_seq for item in history):
                        seq_data["history"].append({"sequence": extracted_seq, "label": new_label})
                        with open(SEQ_FILE, 'w') as f:
                            json.dump(seq_data, f)
                        st.success("Logged successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("Sequence already logged.")
        st.caption(f"Operator Session Active")

    with col_right:
        st.subheader("Accepted Ledger")
        st.caption("Sequence History")
        
        # Move the Ledger display into a scrollable container
        ledger_container = st.container(height=260)
        with ledger_container:
            if history:
                for item in reversed(history): # Show newest first
                    st.markdown(f"- **{item['sequence']:04d}** {item['label'].split(' ', 1)[-1]}")
            else:
                st.markdown("- *No accepted records yet*")

    with col_left:
        # Check for local files
        local_files = []
        input_dir = ""
        if hasattr(config, 'LOCAL_DRIVE_PATH') and os.path.exists(config.LOCAL_DRIVE_PATH):
            input_dir = os.path.join(config.LOCAL_DRIVE_PATH, "INPUT_CSVS")
            if os.path.exists(input_dir):
                local_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

        if local_files:
            selected_file = st.selectbox("Select CSV from Google Drive (Local Sync)", local_files)
            if st.button("Process & Auto-Sync"):
                try:
                    with st.status("Running V22 Engine...", expanded=True) as status:
                        st.write("Fetching IDs from Secure Vault...")
                        # 1. Read CSV
                        csv_path = os.path.join(input_dir, selected_file)
                        df_preview = pd.read_csv(csv_path, header=None, nrows=20)
                        h_idx = -1
                        MARKERS = ["TRACK: TITLE", "SOURCEAUDIO ID", "TITLE", "LIBRARY: NAME"]
                        for i, row in df_preview.iterrows():
                            row_str = row.astype(str).str.cat(sep=" ").upper()
                            if any(m in row_str for m in MARKERS):
                                h_idx = i; break
                
                        if h_idx == -1:
                            status.update(label="Error: Schema not recognized", state="error")
                            st.error("Schema not recognized.")
                            st.stop()

                        st.write("Running Pre-Flight Data Gatekeeper...")
                        df = pd.read_csv(csv_path, header=h_idx)
                        
                        # Apply Gatekeeper Checks
                        for i, row in df.iterrows():
                            # Work Title (60 chars)
                            title_val = str(pd.Series([row[c] for c in df.columns if str(c).upper() in ['TRACK: TITLE', 'TITLE', 'TRACK TITLE']]).dropna().iloc[0] if len([row[c] for c in df.columns if str(c).upper() in ['TRACK: TITLE', 'TITLE', 'TRACK TITLE']]) > 0 else '').strip()
                            if len(title_val) > 60:
                                st.error(f"CRITICAL: Change the Work Title ('{title_val}'). It exceeds 60 characters.")
                                st.stop()
                                
                            # ISRC (12 chars strictly)
                            isrc = str(pd.Series([row[c] for c in df.columns if str(c).upper() in ['CODE: ISRC', 'ISRC']]).dropna().iloc[0] if len([row[c] for c in df.columns if str(c).upper() in ['CODE: ISRC', 'ISRC']]) > 0 else '').strip()
                            if isrc and len(isrc) != 12:
                                st.error(f"CRITICAL: Change the ISRC ('{isrc}'). It must be exactly 12 characters.")
                                st.stop()
                                
                            # Label / Library (60 chars)
                            label_val = str(pd.Series([row[c] for c in df.columns if str(c).upper() in ['LIBRARY NAME', 'LABEL', 'LIBRARY: NAME']]).dropna().iloc[0] if len([row[c] for c in df.columns if str(c).upper() in ['LIBRARY NAME', 'LABEL', 'LIBRARY: NAME']]) > 0 else '').strip()
                            if len(label_val) > 60:
                                st.error(f"CRITICAL: Change the Label Name ('{label_val}'). It exceeds 60 characters.")
                                st.stop()

                        st.write("Generating HDR/GRH/NWR Records...")
                        # Generate CWR with Map & Warnings
                        cwr, warnings = generate_cwr_content(df, agreement_map=AGREEMENT_MAP)
                        
                        if warnings:
                            for w in warnings:
                                st.warning(w)
                        
                        # Generate Strict Filename (CW[YY][NNNN]LUM_319.V22)
                        yr = str(current_year)[-2:]
                        filename = f"CW{yr}{int(cwr_sequence):04d}LUM_319.V22"
                        
                        # --- PRE-FLIGHT CHECKLIST ---
                        st.write("Running Mandatory Pre-Flight Checks...")
                        
                        # CHECK 1: Filename compliance
                        if not (filename.startswith("CW") and "LUM_" in filename and filename.endswith(".V22")):
                            raise ValueError(f"PRE-FLIGHT FAIL: Invalid filename format '{filename}'")
                        
                        cwr_lines = cwr.replace('\r\n', '\n').split('\n')
                        hdr_line = cwr_lines[0] if cwr_lines else ""
                        
                        # CHECK 2: HDR Submitter LUM and Version 2.200
                        if "LUM" not in hdr_line or "2.200" not in hdr_line:
                            raise ValueError("PRE-FLIGHT FAIL: HDR record does not contain Submitter LUM and/or Version 2.200")
                            
                        # CHECK 3: Symmetry Group exactly 182 characters
                        for l in cwr_lines:
                            rec_type = l[:3]
                            if rec_type in ["NWR", "SWR", "SWT", "SPU", "SPT", "REV"]:
                                if len(l) != 182:
                                    raise ValueError(f"PRE-FLIGHT FAIL: {rec_type} record length must be exactly 182 characters. Found: {len(l)}")
                            
                        # CHECK 4: Dual REC records ('C' and 'D')
                        import re
                        rec_lines = [l for l in cwr_lines if l.startswith("REC")]
                        c_sources = len([l for l in rec_lines if len(l) > 262 and l[262] == 'C'])
                        d_sources = len([l for l in rec_lines if len(l) > 262 and l[262] == 'D'])
                        # Assuming 1 C and 1 D per NWR
                        if c_sources == 0 or d_sources == 0 or c_sources != d_sources:
                            raise ValueError("PRE-FLIGHT FAIL: Works are missing Dual REC records (Source C and D mismatch)")
                        
                        st.write(f"Syncing {filename} to Google Drive...")
                        
                        # Sync Logic
                        output_path = os.path.join(config.LOCAL_DRIVE_PATH, "OUTPUT_V22")
                        if not os.path.exists(output_path):
                            os.makedirs(output_path, exist_ok=True)
                        
                        final_path = os.path.join(output_path, filename)
                        
                        # Timeout Logic
                        start_time = time.time()
                        with open(final_path, "w") as f:
                            f.write(cwr)
                            
                        # Verify
                        if not os.path.exists(final_path):
                            raise Exception("File verified as missing after write.")
                        
                        elapsed = time.time() - start_time
                        if elapsed > 15:
                             raise TimeoutError("Write operation took too long.")

                        status.update(label="Sync Successful!", state="complete")
                        st.success(f"Success! File synced to OUTPUT_V22: {filename}")
                        
                        # Download Fallback
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                            zip_file.writestr(filename, cwr)

                        st.download_button(
                            label="Download CWR Archive (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"{filename}.zip",
                            mime="application/zip"
                        )
                except Exception as e:
                    st.error(f"FATAL ERROR: {e}")
        else:
            uploaded_file = st.file_uploader("Upload CSV file manually", type="csv")
            if uploaded_file:
                if st.button("Generate & Download"):
                    try:
                        with st.status("Generating CWR File...", expanded=True) as s:
                            st.write("Reading Agreement Vault...")
                            df_preview = pd.read_csv(uploaded_file, header=None, nrows=20)
                            h_idx = -1
                            MARKERS = ["TRACK: TITLE", "SOURCEAUDIO ID", "TITLE", "LIBRARY: NAME"]
                            for i, row in df_preview.iterrows():
                                row_str = row.astype(str).str.cat(sep=" ").upper()
                                if any(m in row_str for m in MARKERS):
                                    h_idx = i; break
                    
                            if h_idx == -1:
                                s.update(label="Error: Schema not recognized", state="error")
                                st.error("Schema not recognized.")
                                st.stop()

                            st.write("Running Pre-Flight Data Gatekeeper...")
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, header=h_idx)
                            
                            # Apply Gatekeeper Checks
                            for i, row in df.iterrows():
                                # Work Title (60 chars)
                                title_val = str(pd.Series([row[c] for c in df.columns if str(c).upper() in ['TRACK: TITLE', 'TITLE', 'TRACK TITLE']]).dropna().iloc[0] if len([row[c] for c in df.columns if str(c).upper() in ['TRACK: TITLE', 'TITLE', 'TRACK TITLE']]) > 0 else '').strip()
                                if len(title_val) > 60:
                                    st.error(f"CRITICAL: Change the Work Title ('{title_val}'). It exceeds 60 characters.")
                                    st.stop()
                                    
                                # ISRC (12 chars strictly)
                                isrc = str(pd.Series([row[c] for c in df.columns if str(c).upper() in ['CODE: ISRC', 'ISRC']]).dropna().iloc[0] if len([row[c] for c in df.columns if str(c).upper() in ['CODE: ISRC', 'ISRC']]) > 0 else '').strip()
                                if isrc and len(isrc) != 12:
                                    st.error(f"CRITICAL: Change the ISRC ('{isrc}'). It must be exactly 12 characters.")
                                    st.stop()
                                    
                                # Label / Library (60 chars)
                                label_val = str(pd.Series([row[c] for c in df.columns if str(c).upper() in ['LIBRARY NAME', 'LABEL', 'LIBRARY: NAME']]).dropna().iloc[0] if len([row[c] for c in df.columns if str(c).upper() in ['LIBRARY NAME', 'LABEL', 'LIBRARY: NAME']]) > 0 else '').strip()
                                if len(label_val) > 60:
                                    st.error(f"CRITICAL: Change the Label Name ('{label_val}'). It exceeds 60 characters.")
                                    st.stop()

                            st.write("Aligning Record Positions...")
                            
                            # Generate CWR with Map & Warnings
                            cwr, warnings = generate_cwr_content(df, agreement_map=AGREEMENT_MAP)
                            
                            if warnings:
                                for w in warnings:
                                    st.warning(w)
                            
                            s.update(label="Conversion Complete!", state="complete")
                            
                            # Generate Strict Filename (CW[YY][NNNN]LUM_319.V22)
                            yr = str(current_year)[-2:]
                            filename = f"CW{yr}{int(cwr_sequence):04d}LUM_319.V22"
                            
                            # --- PRE-FLIGHT CHECKLIST ---
                            st.write("Running Mandatory Pre-Flight Checks...")
                            
                            # CHECK 1: Filename compliance
                            if not (filename.startswith("CW") and "LUM_" in filename and filename.endswith(".V22")):
                                raise ValueError(f"PRE-FLIGHT FAIL: Invalid filename format '{filename}'")
                            
                            cwr_lines = cwr.replace('\r\n', '\n').split('\n')
                            hdr_line = cwr_lines[0] if cwr_lines else ""
                            
                            # CHECK 2: HDR Submitter LUM and Version 2.200
                            if "LUM" not in hdr_line or "2.200" not in hdr_line:
                                raise ValueError("PRE-FLIGHT FAIL: HDR record does not contain Submitter LUM and/or Version 2.200")
                                
                            # CHECK 3: Symmetry Group exactly 182 characters
                            for l in cwr_lines:
                                rec_type = l[:3]
                                if rec_type in ["NWR", "SWR", "SWT", "SPU", "SPT", "REV"]:
                                    if len(l) != 182:
                                        raise ValueError(f"PRE-FLIGHT FAIL: {rec_type} record length must be exactly 182 characters. Found: {len(l)}")
                                
                            # CHECK 4: Dual REC records ('C' and 'D')
                            rec_lines = [l for l in cwr_lines if l.startswith("REC")]
                            c_sources = len([l for l in rec_lines if len(l) > 262 and l[262] == 'C'])
                            d_sources = len([l for l in rec_lines if len(l) > 262 and l[262] == 'D'])
                            if c_sources == 0 or d_sources == 0 or c_sources != d_sources:
                                raise ValueError("PRE-FLIGHT FAIL: Works are missing Dual REC records (Source C and D mismatch)")
                                
                            st.success("CWR 2.2 File Ready")
                            
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                                zip_file.writestr(filename, cwr)

                            st.download_button(
                                label="Download CWR Archive (ZIP)",
                                data=zip_buffer.getvalue(),
                                file_name=f"{filename}.zip",
                                mime="application/zip"
                            )
                    except Exception as e:
                        st.error(f"FATAL ERROR: {e}")

# --- 6. TASK: VALIDATOR ---
with tab_val:
    st.markdown("<h2 class='sub-title'>CWR 2.2 Validator</h2>", unsafe_allow_html=True)
    
    # Center the file uploader in a smaller column
    col_v_space1, col_v_main, col_v_space2 = st.columns([1, 2, 1])
    
    with col_v_main:
        v22_file = st.file_uploader("Upload .V22 file", type=["V22", "cwr"], label_visibility="collapsed")
        
        if v22_file:
            content = v22_file.getvalue().decode("latin-1")
            st.markdown("<div class='run-btn-container'>", unsafe_allow_html=True)
            run_inspection = st.button("Run Inspection", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            if run_inspection:
                rep, stats = CWRValidator().process_file(content)
                transaction_count = len([l for l in content.splitlines() if l.startswith('NWR')])
                
                st.write("---")
                
                # Center Metrics & Display
                st.metric("Transactions", transaction_count)
                
                if not rep and transaction_count > 0: 
                    st.success("Syntax Valid.")
                elif transaction_count == 0:
                    st.warning("No transactions found.")
                else: 
                    st.error(f"Found {len(rep)} issues.")
                    
                    criticals = [i for i in rep if i['level'] in ['CRITICAL', 'ERROR']]
                    warnings = [i for i in rep if i['level'] == 'WARNING']
                    
                    if criticals:
                        st.markdown("### 🔴 Critical Errors (Must Fix)")
                        for item in criticals:
                            st.error(f"**Line {item['line']}**: {item['message']}")
                    
                    if warnings:
                        st.markdown("### 🟡 Warnings (Review)")
                        for item in warnings:
                            st.warning(f"**Line {item['line']}**: {item['message']}")
                            
                    if not criticals and not warnings:
                        st.success("File is fully compliant!")