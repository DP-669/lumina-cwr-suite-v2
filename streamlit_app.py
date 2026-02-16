import streamlit as st
import pandas as pd
import os
from datetime import datetime
import config  # Still used locally

# --- DYNAMIC CONFIGURATION LOADER ---
# Checks if we are on the web (Streamlit Cloud) or local Mac
if "LUMINA_CONFIG" in st.secrets:
    # Use the Secure Vault (Web)
    LUMINA_CONFIG = st.secrets["LUMINA_CONFIG"]
    AGREEMENT_MAP = st.secrets["AGREEMENT_MAP"]
else:
    # Use local config.py (Mac)
    LUMINA_CONFIG = config.LUMINA_CONFIG
    AGREEMENT_MAP = config.AGREEMENT_MAP

# --- APP INTERFACE ---
st.set_page_config(page_title="Lumina CWR Suite", layout="wide")

st.title("Lumina CWR v2.2 Engine")
st.sidebar.title("Navigation")
mode = st.sidebar.radio("Go to", ["Generator", "Validator"])

if mode == "Generator":
    st.header("CWR Generation")
    
    # 1. File Selection
    # If local path is set in config, try to list files automatically
    local_files = []
    input_dir = ""
    if hasattr(config, 'LOCAL_DRIVE_PATH') and os.path.exists(config.LOCAL_DRIVE_PATH):
        input_dir = os.path.join(config.LOCAL_DRIVE_PATH, "INPUT_CSVS")
        if os.path.exists(input_dir):
            local_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

    if local_files:
        selected_file = st.selectbox("Select CSV from Google Drive folder:", local_files)
        csv_path = os.path.join(input_dir, selected_file)
        if st.button("Process Selected File"):
            # Logic for CWR 2.2 Processing
            st.success(f"Processing {selected_file}...")
            # (Conversion logic here)
            st.info("Syncing to Google Drive...")
    else:
        uploaded_file = st.file_uploader("Upload CSV file manually", type="csv")
        if uploaded_file:
            st.success("File uploaded! Ready for processing.")
            if st.button("Process & Download"):
                st.info("Generating CWR 2.2 file...")
                # Download button appears here after processing

elif mode == "Validator":
    st.header("CWR Validator")
    st.write("Upload a .V22 file to check alignment and syntax.")
    v22_file = st.file_uploader("Select CWR File", type=["V22", "cwr"])

st.markdown("---")
st.caption(f"Lumina CWR Suite | Connected as: {LUMINA_CONFIG['name']}")