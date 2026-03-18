"""
session_manager.py
-------------------

ETSI-inspired Session Management Layer

Supports:
- Role-aware sessions (ENC / DEC)
- Node-aware sessions
- Session lifecycle states
- TTL enforcement
- Multi-node ready (Week 7+)
- Secure application integration (Week 9)
"""

import uuid
from datetime import datetime, timezone, timedelta
from models import KeyRole


class SessionState:
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class SessionManager:

    def __init__(self, default_ttl_seconds: int = 600):
        self.sessions = {}
        self.default_ttl = default_ttl_seconds

    # =================================================
    # CREATE SESSION
    # =================================================
    def create_session(self, app_id: str, role: str, node_id: str):

        try:
            role_enum = KeyRole(role)
        except ValueError:
            raise ValueError("Invalid role")

        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            "app_id": app_id,
            "node_id": node_id,
            "role": role_enum,
            "state": SessionState.ACTIVE,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(seconds=self.default_ttl),
            "keys_allocated": 0
        }

        return session_id

    # =================================================
    # VALIDATE SESSION
    # =================================================
    def validate_session(self, session_id: str):

        session = self.sessions.get(session_id)

        if not session:
            return False

        if session["state"] != SessionState.ACTIVE:
            return False

        if datetime.now(timezone.utc) > session["expires_at"]:
            session["state"] = SessionState.EXPIRED
            return False

        return True

    # =================================================
    # INCREMENT KEY USAGE
    # =================================================
    def record_key_usage(self, session_id: str):

        session = self.sessions.get(session_id)

        if session and session["state"] == SessionState.ACTIVE:
            session["keys_allocated"] += 1

    # =================================================
    # CLOSE SESSION
    # =================================================
    def close_session(self, session_id: str):

        session = self.sessions.get(session_id)

        if not session:
            return False

        session["state"] = SessionState.CLOSED
        return True

    # =================================================
    # GET SESSION INFO (Monitoring)
    # =================================================
    def get_session(self, session_id: str):
        return self.sessions.get(session_id)

    # =================================================
    # LIST ACTIVE SESSIONS
    # =================================================
    def list_active_sessions(self):

        active_sessions = []

        for sid, session in self.sessions.items():
            if session["state"] == SessionState.ACTIVE:
                active_sessions.append(sid)

        return active_sessions
