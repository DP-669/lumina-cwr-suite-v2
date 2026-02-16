# ==============================================================================
# LUMINA BUSINESS SCHEMA
# ==============================================================================
# These are global business settings. 
# Private data (Agreement Maps) has been moved to Streamlit Secrets.

LUMINA_CONFIG = {
    "name": "LUMINA PUBLISHING UK",
    "ipi": "01254514077",
    "territory": "0826"
}

# AGREEMENT_MAP is intentionally left empty here.
# The app will look for this in Streamlit Secrets when running on the web,
# or you can temporarily add them back here if doing deep offline testing.
AGREEMENT_MAP = {}

# ==============================================================================
# LOCAL CONFIGURATION
# ==============================================================================
# The physical path to your Google Drive folder for automatic file syncing
LOCAL_DRIVE_PATH = "/Users/damirprice/Library/CloudStorage/GoogleDrive-luminapub67@gmail.com/My Drive/Lumina_CWR_Processing"