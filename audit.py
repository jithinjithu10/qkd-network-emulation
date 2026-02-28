"""
audit.py

Strict ETSI-aligned audit logging.

Implements:
- Key lifecycle logging
- Session logging
- API operation logging
"""

from datetime import datetime, timezone


class AuditLogger:

    def __init__(self):
        pass

    # =================================================
    # GENERIC LOG
    # =================================================

    def log(self, event_type: str, message: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] [{event_type}] {message}")

    # =================================================
    # SESSION EVENTS
    # =================================================

    def session_created(self, session_id: str):
        self.log("SESSION_CREATED", f"Session ID: {session_id}")

    def session_closed(self, session_id: str):
        self.log("SESSION_CLOSED", f"Session ID: {session_id}")

    def session_expired(self, session_id: str):
        self.log("SESSION_EXPIRED", f"Session ID: {session_id}")

    # =================================================
    # KEY EVENTS
    # =================================================

    def key_added(self, key_id: str):
        self.log("KEY_ADDED", f"Key ID: {key_id}")

    def key_reserved(self, key_id: str, session_id: str):
        self.log("KEY_RESERVED", f"Key ID: {key_id} | Session: {session_id}")

    def key_consumed(self, key_id: str):
        self.log("KEY_CONSUMED", f"Key ID: {key_id}")

    def key_expired(self, key_id: str):
        self.log("KEY_EXPIRED", f"Key ID: {key_id}")

    # =================================================
    # ERROR EVENTS
    # =================================================

    def error(self, message: str):
        self.log("ERROR", message)