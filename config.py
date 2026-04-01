# config.py (FINAL - KMS SYNC READY)

# =================================================
# NODE CONFIGURATION
# =================================================

NODE_ID = "IITR"        # "IITR" or "IITJ"
NODE_ROLE = "SERVER"   # SERVER / CLIENT

# =================================================
# SYSTEM MODE
# =================================================

# "SYNC"  → local demo (same key generation)
# "ETSI"  → real KMS system (USE THIS)

SYSTEM_MODE = "ETSI"

# Enable inter-KMS synchronization
SYNC_ENABLED = True

# =================================================
# SYNC CONFIGURATION
# =================================================

SYNC_SEED = "QKD_SHARED_SEED_2026"

# NOTE:
# Sync index is handled in buffer (correct)

# =================================================
# SERVER CONFIGURATION
# =================================================

HOST = "0.0.0.0"
PORT = 8001

# =================================================
# KEY CONFIGURATION
# =================================================

KEY_SIZE = 256
DEFAULT_TTL_SECONDS = 300
INITIAL_KEY_POOL_SIZE = 20
MAX_BUFFER_SIZE = 1000

# IMPORTANT → must match buffers.py
MAX_BYTES_PER_KEY = 32

# =================================================
# AUTHENTICATION CONFIGURATION
# =================================================

AUTH_ENABLED = True
AUTH_TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"

# Used for IITR ↔ IITJ communication
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

# Define both nodes properly

PEER_NODES = {
    "IITR": "http://10.13.2.132:8000",
    "IITJ": "http://10.13.2.132:8001"
}

# Get peer dynamically
def get_peer_url():
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