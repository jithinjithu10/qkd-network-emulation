"""
config.py

Configuration for ETSI-aligned QKD Node
Supports multi-node scalable architecture
"""

# =================================================
# NODE CONFIGURATION (CRITICAL)
# =================================================

NODE_ID = "IITJ"          # Change to IITR on other server
NODE_ROLE = "SERVER"      # SERVER (IITJ) or CLIENT (IITR)

# =================================================
# SERVER CONFIGURATION
# =================================================

HOST = "0.0.0.0"
PORT = 8001

# =================================================
# KEY CONFIGURATION
# =================================================

KEY_SIZE = 256                 # bits
DEFAULT_TTL_SECONDS = 300      # key lifetime
INITIAL_KEY_POOL_SIZE = 20     # preloaded key count

# =================================================
# SESSION CONFIGURATION
# =================================================

SESSION_TIMEOUT_SECONDS = 600

# =================================================
# AUTHENTICATION CONFIGURATION
# =================================================

AUTH_ENABLED = True

# Application plane token
AUTH_TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"

# Inter-KMS node token (can be separated later)
NODE_SHARED_SECRET = "INTERKMS_SHARED_SECRET_2026"

# =================================================
# FUTURE SCALING (6-NODE NETWORK READY)
# =================================================

# Known peer nodes (for inter-KMS extension)
PEER_NODES = {
    "IITR": "http://10.13.2.132:8001",
    # Add more nodes later:
    # "NODE3": "http://x.x.x.x:8001",
}