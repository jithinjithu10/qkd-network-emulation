"""
config.py
----------
Centralized configuration.
"""

import os

CENTRAL_KMS_URL = os.getenv("CENTRAL_KMS_URL", "http://localhost:8001")

REFILL_THRESHOLD = 3
DEFAULT_TTL = 300
