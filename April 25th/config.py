# config.py (FINAL STABLE VERSION)

# =================================================
# NODE CONFIGURATION
# =================================================

NODE_ID = "IITJ"
NODE_ROLE = "CLIENT" 


# =================================================
# SYSTEM MODE
# =================================================

SYSTEM_MODE = "ETSI"
SYNC_ENABLED = True


# =================================================
# SYNC CONFIGURATION
# =================================================

SYNC_SEED = "QKD_SHARED_SEED_2026"


# =================================================
# DEPLOYMENT MODE
# =================================================

# "LOCAL" → localhost testing
# "REMOTE" → IITR ↔ IITJ real deployment
DEPLOYMENT_MODE = "LOCAL"


# =================================================
# NETWORK CONFIGURATION
# =================================================

if DEPLOYMENT_MODE == "LOCAL":
    IITR_IP = "127.0.0.1"
    IITJ_IP = "127.0.0.1"
else:
    IITR_IP = "103.37.201.5"
    IITJ_IP = "<IITJ_PUBLIC_IP>"


# =================================================
# SERVER CONFIGURATION (AUTO-SET)
# =================================================

HOST = "0.0.0.0"

if NODE_ID == "IITR":
    PORT = 8000
    EXPECTED_ROLE = "SERVER"
else:
    PORT = 8001
    EXPECTED_ROLE = "CLIENT"


# =================================================
# VALIDATION (CRITICAL)
# =================================================

if NODE_ROLE != EXPECTED_ROLE:
    raise ValueError(
        f"Invalid NODE_ROLE for {NODE_ID}. Expected {EXPECTED_ROLE}, got {NODE_ROLE}"
    )


# =================================================
# PEER CONFIGURATION
# =================================================

PEER_NODES = {
    "IITR": f"http://{IITR_IP}:8000",
    "IITJ": f"http://{IITJ_IP}:8001"
}


def get_peer_url():
    """
    Returns peer node URL.
    IITR → IITJ
    IITJ → IITR
    """
    if NODE_ID == "IITR":
        return PEER_NODES["IITJ"]
    else:
        return PEER_NODES["IITR"]


# =================================================
# KEY CONFIGURATION
# =================================================

KEY_SIZE = 256
DEFAULT_TTL_SECONDS = 300
INITIAL_KEY_POOL_SIZE = 20
MAX_BUFFER_SIZE = 1000

MAX_BYTES_PER_KEY = 32


# =================================================
# AUTH CONFIGURATION
# =================================================

AUTH_ENABLED = True

# MUST MATCH on BOTH IITR & IITJ
AUTH_TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"

# MUST MATCH on BOTH IITR & IITJ
NODE_SHARED_SECRET = "INTERKMS_SHARED_SECRET_2026"


# =================================================
# INTER-KMS CONFIG
# =================================================

INTERKMS_TIMEOUT_SECONDS = 5
INTERKMS_MAX_RETRIES = 3
INTERKMS_SYNC_INTERVAL = 10


# =================================================
# CRYPTO CONFIG
# =================================================

ENCRYPTION_ALGORITHM = "AES-256-GCM"
AES_BLOCK_SIZE = 16


# =================================================
# OBSERVABILITY
# =================================================

ENABLE_DEBUG_LOGS = True


# =================================================
# STRESS TEST
# =================================================

ENABLE_STRESS_TEST = False
STRESS_REQUEST_RATE = 50