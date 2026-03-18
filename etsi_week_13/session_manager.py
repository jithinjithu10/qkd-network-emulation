"""
session_manager.py

Thread-safe ETSI-aligned session management.

Implements:
- Session creation
- Session validation
- Session timeout enforcement
- Automatic cleanup
- Concurrency safety
"""

import uuid
from typing import Dict
from threading import Lock

from models import Session
from audit import AuditLogger


class SessionManager:
    """
    Thread-safe session lifecycle manager.
    """

    def __init__(self, timeout_seconds: int):

        self._sessions: Dict[str, Session] = {}

        self._timeout = timeout_seconds

        self._lock = Lock()

        self.audit = AuditLogger()

    # =================================================
    # CREATE SESSION
    # =================================================

    def create_session(self) -> str:

        with self._lock:

            session_id = str(uuid.uuid4())

            session = Session(session_id, self._timeout)

            self._sessions[session_id] = session

            self.audit.session_created(session_id)

            return session_id

    # =================================================
    # VALIDATE SESSION
    # =================================================

    def validate_session(self, session_id: str) -> Session:

        with self._lock:

            session = self._sessions.get(session_id)

            if not session:
                raise ValueError("Session does not exist")

            session.validate()

            return session

    # =================================================
    # CLOSE SESSION
    # =================================================

    def close_session(self, session_id: str):

        with self._lock:

            session = self._sessions.get(session_id)

            if not session:
                raise ValueError("Session does not exist")

            session.close()

            self.audit.session_closed(session_id)

    # =================================================
    # CLEANUP EXPIRED SESSIONS
    # =================================================

    def cleanup_expired_sessions(self):

        with self._lock:

            expired_ids = []

            for session_id, session in self._sessions.items():

                if session.is_expired():

                    expired_ids.append(session_id)

            for session_id in expired_ids:

                self._sessions[session_id].close()

                self.audit.session_expired(session_id)

    # =================================================
    # HARD CLEAN (OPTIONAL – MEMORY SAFE)
    # =================================================

    def purge_inactive_sessions(self):
        """
        Permanently remove inactive sessions.
        Useful for long-running production nodes.
        """

        with self._lock:

            inactive_ids = [
                sid for sid, session in self._sessions.items()
                if not session.active
            ]

            for sid in inactive_ids:

                del self._sessions[sid]

    # =================================================
    # OBSERVABILITY
    # =================================================

    def stats(self):

        with self._lock:

            active = 0
            inactive = 0

            for session in self._sessions.values():

                if session.active:
                    active += 1
                else:
                    inactive += 1

            return {
                "total_sessions": len(self._sessions),
                "active_sessions": active,
                "inactive_sessions": inactive
            }