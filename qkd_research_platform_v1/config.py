"""
config.py
----------

Research-Grade Configuration Framework
Full QKD Stack
Experiment-Driven | ETSI-Aligned | Reproducible

Weeks 1–12 Complete
"""

import os
import random


# =================================================
# EXPERIMENT PROFILE
# =================================================

EXPERIMENT_PROFILE = os.getenv("QKD_PROFILE", "BASELINE")
# BASELINE | ADAPTIVE | STRESS | HIGH_LATENCY | LOW_RATE


# =================================================
# REPRODUCIBILITY
# =================================================

SIMULATION_SEED = int(os.getenv("SIMULATION_SEED", 42))
random.seed(SIMULATION_SEED)


# =================================================
# DEPLOYMENT MODE
# =================================================

DEPLOYMENT_MODE = os.getenv("QKD_MODE", "DEVELOPMENT")
# DEVELOPMENT | PRODUCTION | STRESS


# =================================================
# CONTROLLER CONFIGURATION
# =================================================

CONTROLLER_HOST = os.getenv("CONTROLLER_HOST", "0.0.0.0")
CONTROLLER_PORT = int(os.getenv("CONTROLLER_PORT", 9000))

CONTROLLER_URL = os.getenv(
    "CONTROLLER_URL",
    f"http://localhost:{CONTROLLER_PORT}"
)


# =================================================
# CENTRAL KMS CONFIGURATION
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


# =================================================
# NETWORK / PHYSICS LAYER
# =================================================

DEFAULT_LINK_RATE = 1000
DEFAULT_LINK_LATENCY = 1
DEFAULT_LINK_STATUS = "AVAILABLE"

QBER_THRESHOLD = 0.11
BASE_KEY_GENERATION_RATE = 1000
PHOTON_LOSS_RATE = 0.02
NOISE_PROBABILITY = 0.01


# =================================================
# KEY PARAMETERS
# =================================================

SUPPORTED_KEY_SIZES = [128, 256]
DEFAULT_TTL = 300
MAX_KEYS_PER_REQUEST = 10


# =================================================
# POLICY MODE
# =================================================

POLICY_MODE = os.getenv("POLICY_MODE", "ADAPTIVE")
# BASELINE | ADAPTIVE

REFILL_THRESHOLD = 3
PER_APPLICATION_LIMIT = 5
MIN_FRESHNESS_SCORE = 30


# =================================================
# APPLICATION LAYER
# =================================================

MAX_KEYS_PER_SESSION = 5
SESSION_TIMEOUT_SECONDS = 600
APPLICATION_BUFFER_LIMIT = 20


# =================================================
# DATA TRANSFER
# =================================================

ENABLE_AES_256 = True
REKEY_THRESHOLD = 100_000
MAX_TRANSFER_SIZE = 5_000_000


# =================================================
# STRESS PARAMETERS
# =================================================

ENABLE_STRESS_MODE = False
KEY_EXHAUSTION_TEST_RATE = 50
LINK_DEGRADATION_PROBABILITY = 0.1
SIMULATED_PACKET_LOSS = 0.02


# =================================================
# CONTROLLER ENFORCEMENT FLAGS
# =================================================

ENFORCE_LINK_STATUS = True
ENFORCE_LINK_CAPACITY = True
ENFORCE_NODE_AUTH = True


# =================================================
# TRUST SYSTEM
# =================================================

TRUST_DECAY_ON_HEARTBEAT_FAIL = 10
TRUST_DECAY_ON_AUTH_FAIL = 5
TRUST_MIN_THRESHOLD = 20


# =================================================
# METRICS & LOGGING
# =================================================

ENABLE_METRICS = True
METRICS_EXPORT_INTERVAL = 10
EXPORT_METRICS_TO_FILE = True
METRICS_FILE = "metrics.log"
ENABLE_LATENCY_TRACKING = True
ENABLE_TRAFFIC_TRACKING = True


# =================================================
# SECURITY SETTINGS
# =================================================

REQUIRE_AUTH_TOKEN = True
TLS_ENABLED = False


# =================================================
# ETSI COMPATIBILITY
# =================================================

ETSI_API_VERSION = "v2"
ENABLE_ETSI_COMPLIANCE_MODE = True