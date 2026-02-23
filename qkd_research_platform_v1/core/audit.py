"""
audit.py
---------

Research-Grade Audit Logging System
ETSI-Aligned | Experiment-Aware | Metrics-Ready

Enhancements:
- High resolution timestamps
- Experiment tagging
- Policy mode tracking
- Buffer pressure logging
- Latency tracking support
- JSON-first structured logging
"""

import os
import threading
import json
import time
from datetime import datetime, timezone


# =================================================
# CONFIGURATION
# =================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AUDIT_FILE = os.getenv(
    "QKD_AUDIT_FILE",
    os.path.join(BASE_DIR, "audit.log")
)

JSON_LOGGING = os.getenv("QKD_JSON_LOGGING", "true").lower() == "true"

EXPERIMENT_ID = os.getenv("QKD_EXPERIMENT_ID", "default_experiment")

_log_lock = threading.Lock()


# =================================================
# CORE LOGGER
# =================================================

def log_event(
    message: str,
    event_type: str = "SYSTEM",
    request_id: str | None = None,
    client_id: str | None = None,
    policy_mode: str | None = None,
    latency: float | None = None,
    pressure: float | None = None,
    metadata: dict | None = None
):
    """
    Central structured audit logger.
    High precision timestamp + experiment tagging.
    """

    timestamp = datetime.now(timezone.utc).isoformat()
    monotonic_time = time.time()

    log_entry = {
        "timestamp_utc": timestamp,
        "timestamp_epoch": monotonic_time,
        "experiment_id": EXPERIMENT_ID,
        "event_type": event_type,
        "message": message,
        "request_id": request_id,
        "client_id": client_id,
        "policy_mode": policy_mode,
        "latency_seconds": latency,
        "buffer_pressure": pressure,
        "metadata": metadata or {}
    }

    if JSON_LOGGING:
        log_line = json.dumps(log_entry) + "\n"
    else:
        log_line = (
            f"[{timestamp}] "
            f"[{event_type}] "
            f"[mode={policy_mode}] "
            f"[lat={latency}] "
            f"[pressure={pressure}] "
            f"{message}\n"
        )

    with _log_lock:
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)


# =================================================
# SPECIALIZED LOG HELPERS
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
# READ LAST N LOGS
# =================================================

def read_audit_log(lines: int = 100):

    if not os.path.exists(AUDIT_FILE):
        return []

    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    return all_lines[-lines:]


# =================================================
# CLEAR LOG
# =================================================

def clear_audit_log():

    with _log_lock:
        with open(AUDIT_FILE, "w", encoding="utf-8"):
            pass