"""
Research-Grade Audit Logging System
PERFORMANCE OPTIMIZED + DEBUG MODE
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

# ⚠ PERFORMANCE SWITCH
ENABLE_AUDIT_LOGGING = os.getenv("QKD_ENABLE_AUDIT", "true").lower() == "true"

# Batch mode (reduces disk I/O)
ENABLE_BATCH_MODE = os.getenv("QKD_BATCH_AUDIT", "true").lower() == "true"
BATCH_SIZE = 50

_log_lock = threading.Lock()
_log_buffer = []


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
    Structured audit logger.
    Performance-aware version.
    """

    if not ENABLE_AUDIT_LOGGING:
        return

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
        log_line = json.dumps(log_entry)
    else:
        log_line = (
            f"[{timestamp}] "
            f"[{event_type}] "
            f"[mode={policy_mode}] "
            f"[lat={latency}] "
            f"[pressure={pressure}] "
            f"{message}"
        )

    if ENABLE_BATCH_MODE:
        _buffer_log(log_line)
    else:
        _write_direct(log_line)


# =================================================
# BUFFERED WRITE
# =================================================

def _buffer_log(line):

    global _log_buffer

    with _log_lock:

        _log_buffer.append(line)

        if len(_log_buffer) >= BATCH_SIZE:
            _flush_buffer()


def _flush_buffer():

    global _log_buffer

    if not _log_buffer:
        return

    print(f"Flushing {_log_buffer.__len__()} audit logs to disk")

    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        for line in _log_buffer:
            f.write(line + "\n")

    _log_buffer.clear()


# =================================================
# DIRECT WRITE (SLOWER)
# =================================================

def _write_direct(line):

    print("Direct audit write")

    with _log_lock:
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


# =================================================
# SPECIALIZED HELPERS
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