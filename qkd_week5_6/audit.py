"""
audit.py
---------
Maintains an append-only audit log of all key-related events
with timezone-aware UTC timestamps.
"""

from datetime import datetime, timezone

AUDIT_FILE = "audit.log"


def log_event(message: str):
    """
    Write an audit event with a UTC timestamp.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    with open(AUDIT_FILE, "a") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")
