"""
config.py

Configuration for ETSI-aligned QKD Node

Supports:
- Multi-node QKD networks
- ETSI Application Plane
- Inter-KMS communication
- Encryption demonstration
- Future 6-node scaling
"""

# =================================================
# NODE CONFIGURATION (CRITICAL)
# =================================================

NODE_ID = "IITJ"           # Change to IITR on second node
NODE_ROLE = "SERVER"       # SERVER (IITJ) or CLIENT (IITR)

# =================================================
# SERVER CONFIGURATION
# =================================================

HOST = "0.0.0.0"
PORT = 8001

# =================================================
# KEY CONFIGURATION
# =================================================

# QKD key size
KEY_SIZE = 256                     # bits

# Key lifetime
DEFAULT_TTL_SECONDS = 300          # seconds

# Initial key pool
INITIAL_KEY_POOL_SIZE = 20

# Maximum buffer size (future adaptive buffering)
MAX_BUFFER_SIZE = 1000

# =================================================
# SESSION CONFIGURATION
# =================================================

SESSION_TIMEOUT_SECONDS = 600

# =================================================
# AUTHENTICATION CONFIGURATION
# =================================================

AUTH_ENABLED = True

# Application Plane Authentication
AUTH_TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"

# Inter-KMS Node Authentication
NODE_SHARED_SECRET = "INTERKMS_SHARED_SECRET_2026"

# =================================================
# INTER-KMS NETWORK CONFIGURATION
# =================================================

# Timeout for node-to-node communication
INTERKMS_TIMEOUT_SECONDS = 5

# Key request retry attempts
INTERKMS_MAX_RETRIES = 3

# Background key synchronization interval
INTERKMS_SYNC_INTERVAL = 10

# =================================================
# CRYPTOGRAPHY CONFIGURATION
# =================================================

# Algorithm used by applications
ENCRYPTION_ALGORITHM = "AES-256"

# AES block size
AES_BLOCK_SIZE = 16

# =================================================
# APPLICATION DEMO CONFIGURATION
# =================================================

# Test message for secure transfer demo
DEMO_MESSAGE = "Hello from QKD Secure Channel"

# =================================================
# FUTURE SCALING (6-NODE NETWORK READY)
# =================================================

# Known peer nodes (Inter-KMS routing table)
PEER_NODES = {

    "IITR": "http://10.13.2.132:8001",

    # Future nodes
    # "NODE3": "http://10.13.2.140:8001",
    # "NODE4": "http://10.13.2.141:8001",
    # "NODE5": "http://10.13.2.142:8001",
    # "NODE6": "http://10.13.2.143:8001",

}

# =================================================
# OBSERVABILITY CONFIGURATION
# =================================================

ENABLE_DEBUG_LOGS = True

# =================================================
# STRESS TEST CONFIGURATION (WEEK 11)
# =================================================

ENABLE_STRESS_TEST = False

STRESS_REQUEST_RATE = 50        # requests/sec