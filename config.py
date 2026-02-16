# ==============================================================================
# LUMINA BUSINESS SCHEMA
# ==============================================================================
# Global business settings. 
# Private Data (Agreement Maps) now lives in Streamlit Secrets for Web safety.

LUMINA_CONFIG = {
    "name": "LUMINA PUBLISHING UK",
    "ipi": "01254514077",
    "territory": "0826"
}

# The app pulls the real map from Streamlit Secrets when on the web.
# If you ever do offline testing, you can list them here, but keep this file 
# empty when pushing to GitHub to maintain privacy.
AGREEMENT_MAP = {}

# ==============================================================================
# LOCAL CONFIGURATION
# ==============================================================================
# Physical path for your Mac Studio's Local-Sync
LOCAL_DRIVE_PATH = "/Users/damirprice/Library/CloudStorage/GoogleDrive-luminapub67@gmail.com/My Drive/Lumina_CWR_Processing"