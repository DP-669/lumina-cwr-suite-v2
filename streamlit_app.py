import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import config
import io
import zipfile

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

# --- 2. DEFAULT UI SETUP ---
st.set_page_config(page_title="Lumina CWR Suite", layout="wide")

st.title("Lumina CWR Suite")

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.header("Navigation")
    mode = st.radio(
        "Select Operation:",
        ["Generator", "Validator", "System Health"]
    )
    st.markdown("---")
    st.caption(f"Operator: {LUMINA_CONFIG['name']}")

# --- 4. TASK: GENERATOR ---
if mode == "Generator":
    st.header("CWR Generation (v2.2)")
    st.write("Convert CSV metadata into CWR format.")
    
    col1, col2 = st.columns([2, 1])

    with col1:
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

                        st.write("Generating HDR/GRH/NWR Records...")
                        df = pd.read_csv(csv_path, header=h_idx)
                        
                        # Generate CWR with Map & Warnings
                        cwr, warnings = generate_cwr_content(df, agreement_map=AGREEMENT_MAP)
                        
                        if warnings:
                            for w in warnings:
                                st.warning(w)
                        
                        # Generate Filename
                        seq = 1 
                        filename = f"CW{datetime.now().strftime('%y')}{seq:04d}LUM_319.V22"
                        
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
                        buf = io.BytesIO()
                        with zipfile.ZipFile(buf, "w") as zf: zf.writestr(filename, cwr)
                        st.download_button(
                            label="Download ZIP (Safe Mode)",
                            data=buf.getvalue(),
                            file_name=f"{filename}.zip",
                            mime="application/zip"
                        )
                except Exception as e:
                    st.error(f"Processing Failed: {e}")
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

                            st.write("Aligning Record Positions...")
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, header=h_idx)
                            
                            # Generate CWR with Map & Warnings
                            cwr, warnings = generate_cwr_content(df, agreement_map=AGREEMENT_MAP)
                            
                            if warnings:
                                for w in warnings:
                                    st.warning(w)
                            
                            s.update(label="Conversion Complete!", state="complete")
                            
                            # Generate Filename
                            seq = 1 
                            filename = f"CW{datetime.now().strftime('%y')}{seq:04d}LUM_319.V22"
                            
                            st.success("CWR 2.2 File Ready")
                            st.download_button("Download .V22", data=cwr, file_name=filename)
                    except Exception as e:
                        st.error(f"Processing Failed: {e}")

    with col2:
        st.info("""
        **Workflow Guide**
        1. Select source CSV.
        2. Validate agreement mapping.
        3. Submit to ICE Berlin.
        
        *Note: V2.20 logic is strictly enforced.*
        """)

# --- 5. TASK: VALIDATOR ---
elif mode == "Validator":
    st.header("CWR Validator")
    st.write("Check file alignment and record syntax.")
    v22_file = st.file_uploader("Upload .V22 file", type=["V22", "cwr"])
    if v22_file:
        content = v22_file.getvalue().decode("latin-1")
        if st.button("Run Inspection"):
            rep, stats = CWRValidator().process_file(content)
            st.metric("Transactions", stats["transactions"])
            if not rep and stats["transactions"] > 0: 
                st.success("Syntax Valid.")
            elif stats["transactions"] == 0:
                st.warning("No transactions found.")
            else: 
                col_err, col_list = st.columns([1, 2])
                with col_err: st.error(f"Found {len(rep)} issues.")
                with col_list:
                    for item in rep: st.write(f"Line {item['line']}: {item['message']}")

elif mode == "System Health":
    st.header("System Integrity")
    st.write(f"**Connected to Google Drive:** {'YES' if os.path.exists(config.LOCAL_DRIVE_PATH) else 'NO'}")
    st.write(f"**Vault Status:** {'SECURE CLOUD' if 'LUMINA_CONFIG' in st.secrets else 'LOCAL CONFIG'}")