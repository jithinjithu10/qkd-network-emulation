"""
config.py

FINAL CONFIG (IITR ↔ IITJ READY)
"""

# =================================================
# NODE CONFIGURATION
# =================================================

NODE_ID = "IITR"        # Change to IITJ on client
NODE_ROLE = "SERVER"   # SERVER (IITR) / CLIENT (IITJ)

# =================================================
# SYSTEM MODE (VERY IMPORTANT)
# =================================================

# "SYNC"  → deterministic demo mode
# "ETSI"  → real API + inter-KMS mode

SYSTEM_MODE = "SYNC"

# =================================================
# SYNC CONFIGURATION (QKD EMULATION)
# =================================================

SYNC_SEED = "QKD_SHARED_SEED_2026"
SYNC_KEY_INDEX = 0

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

# =================================================
# SESSION CONFIGURATION
# =================================================

SESSION_TIMEOUT_SECONDS = 600

# =================================================
# AUTHENTICATION CONFIGURATION
# =================================================

AUTH_ENABLED = True

AUTH_TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"

NODE_SHARED_SECRET = "INTERKMS_SHARED_SECRET_2026"

# =================================================
# INTER-KMS NETWORK CONFIGURATION
# =================================================

INTERKMS_TIMEOUT_SECONDS = 5
INTERKMS_MAX_RETRIES = 3
INTERKMS_SYNC_INTERVAL = 10

# =================================================
# PEER NODES ( VERY IMPORTANT)
# =================================================

# IITR (SERVER) → no peers needed
# IITJ (CLIENT) → must connect to IITR

PEER_NODES = {
    "IITR": "http://<IITR_IP>:8001"
}

# Example:
# "http://10.13.2.132:8001"

# =================================================
# CRYPTOGRAPHY CONFIGURATION
# =================================================

ENCRYPTION_ALGORITHM = "AES-256"
AES_BLOCK_SIZE = 16

# =================================================
# APPLICATION DEMO CONFIGURATION
# =================================================

DEMO_MESSAGE = "Hello from QKD Secure Channel"

# =================================================
# OBSERVABILITY
# =================================================

ENABLE_DEBUG_LOGS = True

# =================================================
# STRESS TEST CONFIGURATION
# =================================================

ENABLE_STRESS_TEST = False
STRESS_REQUEST_RATE = 50