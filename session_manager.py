"""
session_manager.py

Strict ETSI-aligned session management.

Implements:
- Session creation
- Session validation
- Session timeout enforcement
- Session closure
"""

import uuid
from typing import Dict
from models import Session


class SessionManager:
    """
    Manages ETSI sessions between client and KMS.
    """

    def __init__(self, timeout_seconds: int):
        self._sessions: Dict[str, Session] = {}
        self._timeout = timeout_seconds

    # =================================================
    # CREATE SESSION
    # =================================================

    def create_session(self) -> str:

        session_id = str(uuid.uuid4())
        session = Session(session_id, self._timeout)
        self._sessions[session_id] = session

        return session_id

    # =================================================
    # VALIDATE SESSION
    # =================================================

    def validate_session(self, session_id: str) -> Session:

        session = self._sessions.get(session_id)

        if not session:
            raise ValueError("Session does not exist")

        session.validate()  # Will raise if invalid or expired

        return session

    # =================================================
    # CLOSE SESSION
    # =================================================

    def close_session(self, session_id: str):

        session = self._sessions.get(session_id)

        if not session:
            raise ValueError("Session does not exist")

        session.close()

    # =================================================
    # CLEANUP EXPIRED SESSIONS
    # =================================================

    def cleanup_expired_sessions(self):

        expired_ids = []

        for session_id, session in self._sessions.items():
            if session.is_expired():
                expired_ids.append(session_id)

        for session_id in expired_ids:
            self._sessions[session_id].close()

    # =================================================
    # DEBUG / OBSERVABILITY
    # =================================================

    def stats(self):
        active = 0
        expired = 0

        for session in self._sessions.values():
            if session.active:
                active += 1
            else:
                expired += 1

        return {
            "total_sessions": len(self._sessions),
            "active_sessions": active,
            "inactive_sessions": expired
        }