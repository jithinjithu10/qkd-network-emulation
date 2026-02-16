"""
audit.py
---------

Centralized append-only audit logging system.
ETSI-aligned and Week 8–12 ready.

Supports:
- Key lifecycle logging
- Policy decisions
- Node and link control events
- ETSI service interface activity
- Secure transfer logging
- Stress and attack simulation logging

Features:
- Absolute path safe
- Environment configurable
- Thread-safe
- JSON structured logging (optional)
- Multi-instance safe
- Request ID tracking
- Client identity tracking (for mTLS/API auth)
"""

import os
import threading
import json
from datetime import datetime, timezone


# =================================================
# Absolute Log Path (Server + Local Safe)
# =================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AUDIT_FILE = os.getenv(
    "QKD_AUDIT_FILE",
    os.path.join(BASE_DIR, "audit.log")
)

# Optional JSON logging mode
JSON_LOGGING = os.getenv("QKD_JSON_LOGGING", "false").lower() == "true"

# Thread lock for concurrent writes
_log_lock = threading.Lock()


# =================================================
# Core Logging Function
# =================================================

def log_event(
    message: str,
    event_type: str = "SYSTEM",
    request_id: str | None = None,
    client_id: str | None = None,
    metadata: dict | None = None
):
    """
    Write an audit event with:
    - UTC timestamp
    - Event category
    - Optional request ID
    - Optional client identity
    - Optional structured metadata

    ETSI-compliant systems require traceability.
    """

    timestamp = datetime.now(timezone.utc).isoformat()

    if JSON_LOGGING:
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "message": message,
            "request_id": request_id,
            "client_id": client_id,
            "metadata": metadata or {}
        }
        log_line = json.dumps(log_entry) + "\n"
    else:
        log_line = (
            f"[{timestamp}] "
            f"[{event_type}] "
            f"[req={request_id}] "
            f"[client={client_id}] "
            f"{message}\n"
        )

    with _log_lock:
        with open(AUDIT_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(log_line)


# =================================================
# Specialized Log Helpers
# =================================================

def log_key_event(message: str, **kwargs):
    log_event(message, event_type="KEY", **kwargs)


def log_policy_event(message: str, **kwargs):
    log_event(message, event_type="POLICY", **kwargs)


def log_network_event(message: str, **kwargs):
    log_event(message, event_type="NETWORK", **kwargs)


def log_service_event(message: str, **kwargs):
    log_event(message, event_type="SERVICE", **kwargs)


def log_security_event(message: str, **kwargs):
    log_event(message, event_type="SECURITY", **kwargs)


def log_transfer_event(message: str, **kwargs):
    log_event(message, event_type="TRANSFER", **kwargs)


def log_attack_event(message: str, **kwargs):
    log_event(message, event_type="ATTACK", **kwargs)


# =================================================
# Read Log (Monitoring / Week 12 Metrics)
# =================================================

def read_audit_log(lines: int = 100):
    """
    Return last N lines from audit log.
    Useful for monitoring endpoints and evaluation.
    """

    if not os.path.exists(AUDIT_FILE):
        return []

    with open(AUDIT_FILE, "r", encoding="utf-8") as log_file:
        all_lines = log_file.readlines()

    return all_lines[-lines:]


# =================================================
# Clear Log (Testing / Week 11 Reset)
# =================================================

def clear_audit_log():
    """
    Clear audit log safely (used in stress test resets).
    """

    with _log_lock:
        with open(AUDIT_FILE, "w", encoding="utf-8"):
            pass
