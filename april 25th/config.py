# config.py
# Purpose:
# Central configuration for QKD KMS system.
# Controls:
# - Node identity (IITR / IITJ)
# - Network configuration
# - Inter-KMS communication
# - Security parameters

# =================================================
# NODE CONFIGURATION
# =================================================

# IMPORTANT: CHANGE THIS
# Set node identity depending on where this file is running
# IITR machine → "IITR"
# IITJ machine → "IITJ"
NODE_ID = "IITR"

# IMPORTANT: CHANGE THIS
# IITR typically acts as SERVER (key generator)
# IITJ acts as CLIENT (pulls keys)
NODE_ROLE = "SERVER"   # SERVER / CLIENT


# =================================================
# SYSTEM MODE
# =================================================

# "SYNC"  → local testing (no network)
# "ETSI"  → real deployment (USE THIS)
SYSTEM_MODE = "ETSI"

# Enable inter-KMS synchronization
SYNC_ENABLED = True


# =================================================
# SYNC CONFIGURATION
# =================================================

# IMPORTANT: CHANGE ONLY IF BOTH SIDES AGREE
SYNC_SEED = "QKD_SHARED_SEED_2026"


# =================================================
# SERVER CONFIGURATION
# =================================================

# IMPORTANT: DO NOT CHANGE
# 0.0.0.0 allows external access (required for public IP)
HOST = "0.0.0.0"

# IMPORTANT: CHANGE THIS BASED ON NODE
# IITR → 8000
# IITJ → 8001
PORT = 8000


# =================================================
# KEY CONFIGURATION
# =================================================

KEY_SIZE = 256
DEFAULT_TTL_SECONDS = 300
INITIAL_KEY_POOL_SIZE = 20
MAX_BUFFER_SIZE = 1000

# IMPORTANT: must match buffers.py
MAX_BYTES_PER_KEY = 32


# =================================================
# AUTHENTICATION CONFIGURATION
# =================================================

AUTH_ENABLED = True

# IMPORTANT: MUST MATCH ON BOTH IITR & IITJ
AUTH_TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"

# IMPORTANT: MUST MATCH ON BOTH IITR & IITJ
NODE_SHARED_SECRET = "INTERKMS_SHARED_SECRET_2026"


# =================================================
# INTER-KMS NETWORK CONFIGURATION
# =================================================

INTERKMS_TIMEOUT_SECONDS = 5
INTERKMS_MAX_RETRIES = 3
INTERKMS_SYNC_INTERVAL = 10


# =================================================
# PEER CONFIGURATION (VERY IMPORTANT)
# =================================================

# IMPORTANT: CHANGE THESE FOR REAL DEPLOYMENT

# IITR PUBLIC IP (you provided)
IITR_IP = "103.37.201.5"

# IMPORTANT: CHANGE THIS
# Replace with IITJ public IP (ask your partner)
IITJ_IP = "<IITJ_PUBLIC_IP>"


# Build full URLs
PEER_NODES = {
    "IITR": f"http://{IITR_IP}:8000",
    "IITJ": f"http://{IITJ_IP}:8001"
}


# Get peer dynamically
def get_peer_url():
    """
    Returns the opposite node URL:
    IITR → IITJ
    IITJ → IITR
    """
    if NODE_ID == "IITR":
        return PEER_NODES["IITJ"]
    else:
        return PEER_NODES["IITR"]


# =================================================
# CRYPTOGRAPHY CONFIGURATION
# =================================================

ENCRYPTION_ALGORITHM = "AES-256-GCM"
AES_BLOCK_SIZE = 16


# =================================================
# APPLICATION DEMO
# =================================================

DEMO_MESSAGE = "Hello from QKD Secure Channel"


# =================================================
# OBSERVABILITY
# =================================================

ENABLE_DEBUG_LOGS = True


# =================================================
# STRESS TEST
# =================================================

ENABLE_STRESS_TEST = False
STRESS_REQUEST_RATE = 50