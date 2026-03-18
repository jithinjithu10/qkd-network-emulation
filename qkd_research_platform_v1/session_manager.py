"""
session_manager.py
-------------------

Research-Grade ETSI-Inspired Session Management
Quantum-Aware | Adaptive TTL | Risk Scoring | Metrics Ready
Weeks 8–12 Advanced Implementation
"""

import uuid
import time
from datetime import datetime, timezone, timedelta
from models import KeyRole


class SessionState:
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"
    SUSPICIOUS = "SUSPICIOUS"


class SessionManager:

    def __init__(self, default_ttl_seconds: int = 600):

        self.sessions = {}
        self.default_ttl = default_ttl_seconds

    # =================================================
    # CREATE SESSION
    # =================================================
    def create_session(self, app_id: str, role: str, node_id: str):

        role_enum = KeyRole(role)

        session_id = str(uuid.uuid4())

        now = datetime.now(timezone.utc)

        self.sessions[session_id] = {
            "app_id": app_id,
            "node_id": node_id,
            "role": role_enum,
            "state": SessionState.ACTIVE,
            "created_at": now,
            "expires_at": now + timedelta(seconds=self.default_ttl),
            "keys_allocated": 0,
            "bytes_transferred": 0,
            "rekey_count": 0,
            "failed_allocations": 0,
            "risk_score": 0,
            "allocation_timestamps": []
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
    # RECORD KEY USAGE
    # =================================================
    def record_key_usage(self, session_id: str):

        session = self.sessions.get(session_id)

        if not session or session["state"] != SessionState.ACTIVE:
            return

        session["keys_allocated"] += 1
        session["allocation_timestamps"].append(time.time())

        self._update_risk_score(session_id)

    # =================================================
    # RECORD FAILED ALLOCATION
    # =================================================
    def record_failed_allocation(self, session_id: str):

        session = self.sessions.get(session_id)

        if not session:
            return

        session["failed_allocations"] += 1
        session["risk_score"] += 2

        if session["failed_allocations"] > 5:
            session["state"] = SessionState.SUSPICIOUS

    # =================================================
    # RECORD DATA TRANSFER
    # =================================================
    def record_transfer(self, session_id: str, bytes_count: int):

        session = self.sessions.get(session_id)

        if not session:
            return

        session["bytes_transferred"] += bytes_count

    # =================================================
    # RECORD REKEY EVENT
    # =================================================
    def record_rekey(self, session_id: str):

        session = self.sessions.get(session_id)

        if not session:
            return

        session["rekey_count"] += 1

    # =================================================
    # ADAPTIVE TTL (Novel)
    # =================================================
    def adapt_ttl(self, session_id: str, policy_mode: str):

        session = self.sessions.get(session_id)

        if not session:
            return

        if policy_mode == "STRESS":
            session["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=120)

        elif policy_mode == "ADAPTIVE":
            session["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=300)

    # =================================================
    # RISK SCORE UPDATE
    # =================================================
    def _update_risk_score(self, session_id: str):

        session = self.sessions.get(session_id)

        timestamps = session["allocation_timestamps"]

        if len(timestamps) < 5:
            return

        # Check burst behavior (5 allocations in < 2 seconds)
        if timestamps[-1] - timestamps[-5] < 2:
            session["risk_score"] += 3

        if session["risk_score"] > 5:
            session["state"] = SessionState.SUSPICIOUS

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
    # SESSION INFO
    # =================================================
    def get_session(self, session_id: str):
        return self.sessions.get(session_id)

    # =================================================
    # ACTIVE SESSIONS
    # =================================================
    def list_active_sessions(self):

        return [
            sid for sid, s in self.sessions.items()
            if s["state"] == SessionState.ACTIVE
        ]

    # =================================================
    # EXPORT METRICS
    # =================================================
    def export_metrics(self):

        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(self.list_active_sessions()),
            "suspicious_sessions": len(
                [s for s in self.sessions.values()
                 if s["state"] == SessionState.SUSPICIOUS]
            )
        }