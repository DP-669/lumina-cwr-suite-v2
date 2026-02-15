import streamlit as st
import pandas as pd
from datetime import datetime
import io
import zipfile
import os
from config import LOCAL_DRIVE_PATH

try:
    from cwr_engine import generate_cwr_content
    from cwr_validator import CWRValidator
except ImportError as e:
    st.error(f"SYSTEM ERROR: Component missing. {e}")
    st.stop()

st.set_page_config(page_title="Lumina CWR Suite", layout="centered")

# Sidebar
with st.sidebar:
    st.title("Lumina CWR Suite")
    page = st.radio("Navigation", ["Generator", "Validator"])

if page == "Generator":
    st.title("CWR 2.2 Generator")
    st.markdown("Select a metadata file to process. The output will be synchronized to your Drive.")
    
    # File Sequence Logic
    # Hidden or minimal sequence input if needed, defaulting to 1 for now or keeping it subtle
    seq = st.number_input("File Sequence", min_value=1, value=1, label_visibility="collapsed")
    
    filename = f"CW{datetime.now().strftime('%y')}{seq:04d}LUM_319.V22"
    
    # Logic to determine input source
    # If LOCAL_DRIVE_PATH is set in config, prefer that. Else fallback to uploader.
    
    file = None
    local_output_folder = None
    input_folder = None
    
    if LOCAL_DRIVE_PATH and os.path.exists(LOCAL_DRIVE_PATH):
        input_folder = os.path.join(LOCAL_DRIVE_PATH, "INPUT_CSVS")
        output_folder = os.path.join(LOCAL_DRIVE_PATH, "OUTPUT_V22")
        
        # Ensure folders exist silently
        if not os.path.exists(input_folder): os.makedirs(input_folder, exist_ok=True)
        if not os.path.exists(output_folder): os.makedirs(output_folder, exist_ok=True)
        
        local_output_folder = output_folder
        
        files = [f for f in os.listdir(input_folder) if f.lower().endswith('.csv') and not f.startswith('.')]
        
        if files:
            selected_file_name = st.selectbox("Select File from Drive", files)
            if selected_file_name:
                file_path = os.path.join(input_folder, selected_file_name)
                file = open(file_path, "rb")
        else:
            st.warning(f"No CSV files found in 'INPUT_CSVS'. Please add files to your Drive folder.")
            
    else:
        # Fallback if config is not set correctly
        st.info("Local Drive Path not configured or not found. Using manual upload.")
        file = st.file_uploader("Upload Metadata CSV")

    if file:
        try:
            # Read CSV
            df_preview = pd.read_csv(file, header=None, nrows=20)
            h_idx = -1
            MARKERS = ["TRACK: TITLE", "SOURCEAUDIO ID", "TITLE", "LIBRARY: NAME"]
            for i, row in df_preview.iterrows():
                row_str = row.astype(str).str.cat(sep=" ").upper()
                if any(m in row_str for m in MARKERS):
                    h_idx = i; break
            
            if h_idx == -1:
                st.error("Error: Schema not recognized.")
            else:
                file.seek(0)
                df = pd.read_csv(file, header=h_idx)
                
                # Main Process Button
                if st.button("Process & Sync", type="primary"):
                    cwr = generate_cwr_content(df)
                    
                    # 1. Save to Local Output Folder (Sync)
                    if local_output_folder:
                        out_path = os.path.join(local_output_folder, filename)
                        with open(out_path, "w") as f:
                            f.write(cwr)
                        st.success(f"Success! Saved {filename} to Drive.")
                    else:
                        st.warning("Drive sync unavailable. File generated only.")

                    # 2. Systematic Local Save (Backup)
                    if os.path.exists("."):
                        with open("LATEST_TEST.V22", "w") as f:
                            f.write(cwr)

                    # 3. Download Option (Safe Mode)
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w") as zf: zf.writestr(filename, cwr)
                    st.download_button(
                        label="Download ZIP",
                        data=buf.getvalue(),
                        file_name=f"{filename}.zip",
                        mime="application/zip"
                    )
                    
        except Exception as e:
            st.error(f"Processing Error: {e}")

elif page == "Validator":
    st.header("CWR Validator")
    val_file = st.file_uploader("Upload .V21/.V22 File")
    if val_file:
        content = val_file.getvalue().decode("latin-1")
        if st.button("Run Inspection", type="primary"):
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
