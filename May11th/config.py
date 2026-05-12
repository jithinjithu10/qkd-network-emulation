# config.py
# HYBRID QUANTUM-CLASSICAL QKD ARCHITECTURE CONFIGURATION

import os


# =========================================================
# NODE CONFIGURATION
# =========================================================

"""
IITR -> Server-side QKD node
IITJ -> Client-side QKD node
"""

NODE_ID = os.getenv(
    "NODE_ID",
    "IITR"
)

NODE_ROLE = os.getenv(
    "NODE_ROLE",
    "SERVER"
)


# =========================================================
# SYSTEM MODE
# =========================================================

"""
ETSI:
Hybrid Quantum-Classical ETSI-QKD mode
"""

SYSTEM_MODE = "ETSI"

SYNC_ENABLED = True


# =========================================================
# QUANTUM LAYER
# =========================================================

QUANTUM_LAYER_ENABLED = True

QKD_PROTOCOL = "BB84"

SIMULAQRON_ENABLED = True

ENABLE_RUNTIME_KEY_REGENERATION = True

KEY_REGENERATION_INTERVAL = 30


# =========================================================
# QUANTUM CHANNEL
# =========================================================

"""
Quantum channel responsibilities:
- qubit exchange
- BB84 state transmission
- quantum key generation
"""

QUANTUM_CHANNEL_TYPE = "SIMULAQRON"

SIMULAQRON_ALICE_IP = os.getenv(
    "SIMULAQRON_ALICE_IP",
    "10.11.80.93"
)

SIMULAQRON_BOB_IP = os.getenv(
    "SIMULAQRON_BOB_IP",
    "10.11.80.94"
)

SIMULAQRON_ALICE_PORT = 8016
SIMULAQRON_BOB_PORT = 8019


# =========================================================
# BB84 CONFIGURATION
# =========================================================

BB84_NUM_QUBITS = 32

BB84_BASIS_VALUES = [0, 1]

"""
Acceptable BB84 QBER threshold.
"""

MAX_QBER_THRESHOLD = 0.11


# =========================================================
# SYNCHRONIZATION
# =========================================================

SYNC_SEED = "QKD_SHARED_SEED_2026"

ENABLE_SHA256_SYNC = True

"""
ONLY metadata is synchronized publicly.
Raw keys NEVER leave local nodes.
"""

METADATA_SYNC_ONLY = True


# =========================================================
# SESSION CONFIGURATION
# =========================================================

ENABLE_SESSION_IDS = True

SESSION_TIMEOUT_SECONDS = 300


# =========================================================
# DEPLOYMENT
# =========================================================

"""
LOCAL:
localhost deployment

REMOTE:
IITR ↔ IITJ deployment
"""

DEPLOYMENT_MODE = os.getenv(
    "DEPLOYMENT_MODE",
    "LOCAL"
)


# =========================================================
# NETWORK CONFIGURATION
# =========================================================

IITR_NGROK_URL = os.getenv(
    "IITR_URL"
)

IITJ_NGROK_URL = os.getenv(
    "IITJ_URL"
)


# =========================================================
# PUBLIC CLASSICAL CHANNEL
# =========================================================

"""
Public channel responsibilities:
- ETSI APIs
- FastAPI communication
- metadata synchronization
- SHA-256 verification
- session negotiation
"""

if DEPLOYMENT_MODE == "LOCAL":

    IITR_IP = "127.0.0.1"
    IITJ_IP = "127.0.0.1"

    IITR_BASE_URL = (
        f"http://{IITR_IP}:8000"
    )

    IITJ_BASE_URL = (
        f"http://{IITJ_IP}:8001"
    )

else:

    IITR_BASE_URL = (
        IITR_NGROK_URL
        if IITR_NGROK_URL
        else "http://103.37.201.5:8000"
    )

    IITJ_BASE_URL = (
        IITJ_NGROK_URL
        if IITJ_NGROK_URL
        else "http://14.139.53.130:8001"
    )


# =========================================================
# SERVER CONFIGURATION
# =========================================================

HOST = "0.0.0.0"

if NODE_ID == "IITR":

    PORT = 8000
    EXPECTED_ROLE = "SERVER"

else:

    PORT = 8001
    EXPECTED_ROLE = "CLIENT"


# =========================================================
# VALIDATION
# =========================================================

if NODE_ROLE != EXPECTED_ROLE:

    raise ValueError(
        f"Invalid NODE_ROLE for {NODE_ID}. "
        f"Expected {EXPECTED_ROLE}, "
        f"got {NODE_ROLE}"
    )


# =========================================================
# PEER CONFIGURATION
# =========================================================

PEER_NODES = {

    "IITR": IITR_BASE_URL,

    "IITJ": IITJ_BASE_URL
}


def get_peer_url():

    """
    Returns opposite peer URL.
    """

    if NODE_ID == "IITR":
        return PEER_NODES["IITJ"]

    return PEER_NODES["IITR"]


# =========================================================
# KEY CONFIGURATION
# =========================================================

"""
Quantum-derived AES session keys.
"""

KEY_SIZE = 256

DEFAULT_TTL_SECONDS = 300

INITIAL_KEY_POOL_SIZE = 20

MAX_BUFFER_SIZE = 1000

MAX_BYTES_PER_KEY = 32


# =========================================================
# KEY ROTATION
# =========================================================

ENABLE_KEY_ROTATION = True

KEY_ROTATION_INTERVAL = 60


# =========================================================
# AUTH CONFIGURATION
# =========================================================

AUTH_ENABLED = True

AUTH_TOKEN = (
    "ETSI_DEMO_SECURE_TOKEN_2026"
)

NODE_SHARED_SECRET = (
    "INTERKMS_SHARED_SECRET_2026"
)


# =========================================================
# INTER-KMS
# =========================================================

INTERKMS_TIMEOUT_SECONDS = 5

INTERKMS_MAX_RETRIES = 3

INTERKMS_SYNC_INTERVAL = 10


# =========================================================
# METADATA SYNCHRONIZATION
# =========================================================

ENABLE_METADATA_SYNC = True

SYNC_METADATA_FIELDS = [

    "key_id",

    "session_id",

    "sync_index",

    "key_hash",

    "timestamp"
]


# =========================================================
# HASHING
# =========================================================

HASH_ALGORITHM = "SHA-256"


# =========================================================
# CRYPTOGRAPHY
# =========================================================

"""
AES-GCM uses BB84-derived keys.
"""

ENCRYPTION_ALGORITHM = "AES-256-GCM"

AES_BLOCK_SIZE = 16


# =========================================================
# OBSERVABILITY
# =========================================================

ENABLE_DEBUG_LOGS = True

ENABLE_QKD_LOGS = True

ENABLE_SYNC_LOGS = True


# =========================================================
# DASHBOARD
# =========================================================

ENABLE_STREAMLIT_DASHBOARD = True

DASHBOARD_PORT = 8501


# =========================================================
# REVERSE PROXY
# =========================================================

ENABLE_CADDY_PROXY = True

REVERSE_PROXY_PORT = 443


# =========================================================
# NGROK
# =========================================================

ENABLE_NGROK = True


# =========================================================
# SECURITY
# =========================================================

ENABLE_QBER_MONITORING = True

ENABLE_INTRUSION_ALERTS = True


# =========================================================
# STRESS TEST
# =========================================================

ENABLE_STRESS_TEST = False

STRESS_REQUEST_RATE = 50


# =========================================================
# RESEARCH FLAGS
# =========================================================

ENABLE_SDN_ROUTING = False

ENABLE_MULTI_NODE_QKD = False

ENABLE_TELEPORTATION = True


# =========================================================
# FINAL ARCHITECTURE
# =========================================================

"""
ARCHITECTURE OVERVIEW
=====================

Quantum Layer
--------------
- SimulaQron
- BB84
- Qubit transmission
- Quantum key generation

Public Classical Channel
-------------------------
- FastAPI
- ETSI APIs
- Metadata synchronization
- SHA-256 verification
- Session negotiation

Secure Communication Layer
---------------------------
- AES-GCM
- Encrypted messaging
- File transfer

Deployment
-----------
- IITR ↔ IITJ
- ngrok
- Reverse proxy
- Inter-institute communication
"""