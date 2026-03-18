"""
session_manager.py

FINAL VERSION (STRICT SESSION CONTROL)

Enhancements:
- Strong session-key binding (no overwrite)
- Reverse mapping (key → session)
- Validation enforcement
- Safer access patterns
"""

import uuid
from typing import Dict
from threading import Lock

from models import Session
from audit import AuditLogger


class SessionManager:

    def __init__(self, timeout_seconds: int):

        self._sessions: Dict[str, Session] = {}

        # session → key
        self._session_keys: Dict[str, str] = {}

        # 🔥 NEW → key → session (reverse mapping)
        self._key_sessions: Dict[str, str] = {}

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

            self.audit.log(
                "SESSION_VALIDATED",
                f"Session ID: {session_id}",
                plane="APPLICATION"
            )

            return session

    # =================================================
    # BIND KEY TO SESSION (STRICT)
    # =================================================

    def bind_key(self, session_id: str, key_id: str):

        with self._lock:

            # Validate session
            session = self.validate_session(session_id)

            # ❗ prevent re-binding
            if session_id in self._session_keys:
                raise ValueError("Session already has a key assigned")

            # ❗ prevent key reuse
            if key_id in self._key_sessions:
                raise ValueError("Key already assigned to another session")

            self._session_keys[session_id] = key_id
            self._key_sessions[key_id] = session_id

            session.bind_key(key_id)

            self.audit.log(
                "SESSION_KEY_BOUND",
                f"Session: {session_id} → Key: {key_id}",
                plane="APPLICATION"
            )

    # =================================================
    # GET SESSION KEY (SAFE)
    # =================================================

    def get_session_key(self, session_id: str):

        with self._lock:

            self.validate_session(session_id)

            key_id = self._session_keys.get(session_id)

            if not key_id:
                raise ValueError("No key bound to session")

            return key_id

    # =================================================
    # GET SESSION FROM KEY (NEW)
    # =================================================

    def get_session_from_key(self, key_id: str):

        with self._lock:

            return self._key_sessions.get(key_id)

    # =================================================
    # CLOSE SESSION
    # =================================================

    def close_session(self, session_id: str):

        with self._lock:

            session = self._sessions.get(session_id)

            if not session:
                raise ValueError("Session does not exist")

            session.close()

            key_id = self._session_keys.get(session_id)

            if key_id:
                del self._session_keys[session_id]
                del self._key_sessions[key_id]

            self.audit.session_closed(session_id)

    # =================================================
    # CLEANUP EXPIRED
    # =================================================

    def cleanup_expired_sessions(self):

        with self._lock:

            expired_ids = []

            for session_id, session in self._sessions.items():

                if session.is_expired():
                    expired_ids.append(session_id)

            for session_id in expired_ids:

                self._sessions[session_id].close()

                key_id = self._session_keys.get(session_id)

                if key_id:
                    del self._session_keys[session_id]
                    del self._key_sessions[key_id]

                self.audit.session_expired(session_id)

    # =================================================
    # HARD CLEAN
    # =================================================

    def purge_inactive_sessions(self):

        with self._lock:

            inactive_ids = [
                sid for sid, session in self._sessions.items()
                if not session.active
            ]

            for sid in inactive_ids:

                key_id = self._session_keys.get(sid)

                if key_id:
                    del self._key_sessions[key_id]
                    del self._session_keys[sid]

                del self._sessions[sid]

    # =================================================
    # STATS
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
                "inactive_sessions": inactive,
                "session_key_bindings": len(self._session_keys)
            }