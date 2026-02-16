"""
config.py
----------

Centralized configuration for full QKD Stack
Weeks 1 – 12 Complete
ETSI-style Client–Server Architecture
6-Node Scalable
Research & Evaluation Ready
"""

import os


# =================================================
# DEPLOYMENT MODE
# =================================================

DEPLOYMENT_MODE = os.getenv("QKD_MODE", "DEVELOPMENT")
# DEVELOPMENT | PRODUCTION | STRESS


# =================================================
# CONTROLLER CONFIGURATION (Control Plane)
# =================================================

CONTROLLER_HOST = os.getenv("CONTROLLER_HOST", "0.0.0.0")
CONTROLLER_PORT = int(os.getenv("CONTROLLER_PORT", 9000))

CONTROLLER_URL = os.getenv(
    "CONTROLLER_URL",
    f"http://localhost:{CONTROLLER_PORT}"
)


# =================================================
# CENTRAL KMS CONFIGURATION (Data Plane)
# =================================================

CENTRAL_KMS_HOST = os.getenv("CENTRAL_KMS_HOST", "0.0.0.0")
CENTRAL_KMS_PORT = int(os.getenv("CENTRAL_KMS_PORT", 8001))

CENTRAL_KMS_URL = os.getenv(
    "CENTRAL_KMS_URL",
    f"http://localhost:{CENTRAL_KMS_PORT}"
)


# =================================================
# NODE CONFIGURATION
# =================================================

NODE_ID = os.getenv("NODE_ID", "IITR")
NODE_ROLE = os.getenv("NODE_ROLE", "CENTRAL_KMS")
# CENTRAL_KMS | EDGE_KMS | APPLICATION_NODE


# =================================================
# NETWORK CONFIGURATION (6 NODE READY)
# =================================================

MAX_NODES = 6

DEFAULT_LINK_RATE = 1000          # keys per second
DEFAULT_LINK_LATENCY = 1          # milliseconds (logical)
DEFAULT_LINK_STATUS = "AVAILABLE"


# =================================================
# KEY PARAMETERS
# =================================================

SUPPORTED_KEY_SIZES = [128, 256]

DEFAULT_TTL = int(os.getenv("DEFAULT_TTL", 300))

MAX_KEYS_PER_REQUEST = 10


# =================================================
# POLICY PARAMETERS (Week 6)
# =================================================

REFILL_THRESHOLD = 3

PER_APPLICATION_LIMIT = 5

MIN_FRESHNESS_SCORE = 30


# =================================================
# WEEK 9 – APPLICATION LAYER
# =================================================

APPLICATION_KEY_STORE_ENABLED = True

MAX_KEYS_PER_SESSION = 5

SESSION_TIMEOUT_SECONDS = 600

APPLICATION_BUFFER_LIMIT = 20


# =================================================
# WEEK 10 – DATA TRANSFER LAYER
# =================================================

ENABLE_AES_256 = True
ENABLE_OTP_METADATA = True

REKEY_THRESHOLD = 100_000  # bytes transferred before re-key

MAX_TRANSFER_SIZE = 5_000_000  # bytes


# =================================================
# WEEK 11 – STRESS TEST PARAMETERS
# =================================================

ENABLE_STRESS_MODE = False

KEY_EXHAUSTION_TEST_RATE = 50  # keys per second

LINK_DEGRADATION_PROBABILITY = 0.1

SIMULATED_PACKET_LOSS = 0.02


# =================================================
# WEEK 12 – METRICS COLLECTION
# =================================================

ENABLE_METRICS = True

METRICS_EXPORT_INTERVAL = 10  # seconds

EXPORT_METRICS_TO_FILE = True

METRICS_FILE = os.getenv("QKD_METRICS_FILE", "metrics.log")

ENABLE_LATENCY_TRACKING = True

ENABLE_TRAFFIC_TRACKING = True


# =================================================
# SECURITY SETTINGS
# =================================================

REQUIRE_AUTH_TOKEN = True

ALLOW_LOCALHOST_BYPASS = True

TLS_ENABLED = False  # Future: HTTPS support


# =================================================
# ETSI COMPATIBILITY FLAGS
# =================================================

ETSI_API_VERSION = "v2"

ENABLE_ETSI_COMPLIANCE_MODE = True
