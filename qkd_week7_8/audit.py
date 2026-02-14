"""
audit.py
---------
Centralized append-only audit logging system.

Supports:
- Week 5: Key lifecycle logging
- Week 6: Policy events
- Week 7: Node and link events
- Week 8: Service interface activity

Server-flexible:
- Absolute path safe
- Environment configurable
- Thread-safe
- Multi-instance safe
"""

import os
import threading
from datetime import datetime, timezone


# =================================================
# Absolute Log Path (Server + Local Safe)
# =================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Allow environment override (useful for AWS/Docker)
AUDIT_FILE = os.getenv(
    "QKD_AUDIT_FILE",
    os.path.join(BASE_DIR, "audit.log")
)


# Thread lock for safe concurrent writes
_log_lock = threading.Lock()


# =================================================
# Core Logging Function
# =================================================

def log_event(message: str, event_type: str = "SYSTEM"):
    """
    Write an audit event with:
    - UTC timestamp
    - Event category
    - Message

    Thread-safe and deployment-safe.
    """

    timestamp = datetime.now(timezone.utc).isoformat()

    log_line = f"[{timestamp}] [{event_type}] {message}\n"

    with _log_lock:
        with open(AUDIT_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(log_line)


# =================================================
# Specialized Log Helpers (Week-Aligned)
# =================================================

def log_key_event(message: str):
    log_event(message, event_type="KEY")

def log_policy_event(message: str):
    log_event(message, event_type="POLICY")

def log_network_event(message: str):
    log_event(message, event_type="NETWORK")

def log_service_event(message: str):
    log_event(message, event_type="SERVICE")


# =================================================
# Read Log (Week 7 Monitoring Ready)
# =================================================

def read_audit_log(lines: int = 100):
    """
    Return last N lines from audit log.
    Useful for monitoring endpoints.
    """

    if not os.path.exists(AUDIT_FILE):
        return []

    with open(AUDIT_FILE, "r", encoding="utf-8") as log_file:
        all_lines = log_file.readlines()

    return all_lines[-lines:]
