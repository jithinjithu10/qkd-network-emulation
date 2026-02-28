"""
config.py

Configuration for ETSI-compliant KMS
"""

# =================================================
# SERVER CONFIGURATION
# =================================================

HOST = "0.0.0.0"
PORT = 8001


# =================================================
# KEY CONFIGURATION
# =================================================

KEY_SIZE = 256                 # bits
DEFAULT_TTL_SECONDS = 300      # key lifetime in seconds
INITIAL_KEY_POOL_SIZE = 20     # number of keys preloaded


# =================================================
# SESSION CONFIGURATION
# =================================================

SESSION_TIMEOUT_SECONDS = 600  # session validity duration