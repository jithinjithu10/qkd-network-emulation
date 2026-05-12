# session_manager.py
# ADVANCED HYBRID QKD SESSION MANAGEMENT LAYER

import time
import uuid
import hashlib

from threading import Lock

from audit import AuditLogger

from config import (

    NODE_ID,

    QKD_PROTOCOL,

    DEFAULT_TTL_SECONDS
)


class SessionManager:

    """
    Session Manager

    Responsibilities
    ----------------
    - session lifecycle
    - BB84 session coordination
    - synchronization tracking
    - replay protection
    - key-session mapping
    - distributed orchestration
    - secure metadata management
    """

    def __init__(self):

        self.audit = AuditLogger()

        self.lock = Lock()

        # =================================================
        # STORAGE
        # =================================================

        self.sessions = {}

        self.key_session_map = {}

        self.message_session_map = {}

        # =================================================
        # REPLAY TRACKING
        # =================================================

        self.used_nonces = set()

        self.used_message_ids = set()

        # =================================================
        # METRICS
        # =================================================

        self.created_sessions = 0

        self.closed_sessions = 0

        self.expired_sessions = 0

        self.failed_sessions = 0

        self.replay_attempts = 0

        self.sync_failures = 0

    # =====================================================
    # SESSION DIGEST
    # =====================================================

    def session_digest(
        self,
        session_id
    ):

        return hashlib.sha256(

            f"{session_id}-{NODE_ID}".encode()

        ).hexdigest()

    # =====================================================
    # CREATE SESSION
    # =====================================================

    def create_session(

        self,

        source_node=None,

        destination_node=None
    ):

        with self.lock:

            session_id = str(
                uuid.uuid4()
            )[:8]

            created = time.time()

            session_data = {

                # -----------------------------------------
                # IDENTITY
                # -----------------------------------------

                "session_id":
                    session_id,

                "digest":
                    self.session_digest(
                        session_id
                    ),

                "protocol":
                    QKD_PROTOCOL,

                "node":
                    NODE_ID,

                # -----------------------------------------
                # ROUTING
                # -----------------------------------------

                "source":
                    source_node,

                "destination":
                    destination_node,

                # -----------------------------------------
                # TIMESTAMPS
                # -----------------------------------------

                "created_at":
                    created,

                "last_activity":
                    created,

                "expires_at":
                    (
                        created
                        +
                        DEFAULT_TTL_SECONDS
                    ),

                # -----------------------------------------
                # STATE
                # -----------------------------------------

                "status":
                    "ACTIVE",

                "verified":
                    False,

                "locked":
                    False,

                # -----------------------------------------
                # COUNTERS
                # -----------------------------------------

                "messages":
                    0,

                "sync_index":
                    0,

                "message_counter":
                    0,

                # -----------------------------------------
                # SECURITY
                # -----------------------------------------

                "replay_attempts":
                    0,

                "security_events":
                    [],

                # -----------------------------------------
                # KEYS
                # -----------------------------------------

                "keys":
                    [],

                # -----------------------------------------
                # MESSAGE IDS
                # -----------------------------------------

                "message_ids":
                    []
            }

            self.sessions[
                session_id
            ] = session_data

            self.created_sessions += 1

            self.audit.log(

                "SESSION_CREATED",

                (
                    f"session={session_id}"
                ),

                "SESSION"
            )

            return session_id

    # =====================================================
    # VERIFY NONCE
    # =====================================================

    def verify_nonce(
        self,
        nonce
    ):

        with self.lock:

            if nonce in self.used_nonces:

                self.replay_attempts += 1

                return False

            self.used_nonces.add(
                nonce
            )

            return True

    # =====================================================
    # VERIFY MESSAGE ID
    # =====================================================

    def verify_message_id(
        self,
        message_id
    ):

        with self.lock:

            if message_id in self.used_message_ids:

                self.replay_attempts += 1

                return False

            self.used_message_ids.add(
                message_id
            )

            return True

    # =====================================================
    # LOCK SESSION
    # =====================================================

    def lock_session(
        self,
        session_id
    ):

        with self.lock:

            if session_id not in self.sessions:
                return False

            self.sessions[
                session_id
            ]["locked"] = True

            return True

    # =====================================================
    # UNLOCK SESSION
    # =====================================================

    def unlock_session(
        self,
        session_id
    ):

        with self.lock:

            if session_id not in self.sessions:
                return False

            self.sessions[
                session_id
            ]["locked"] = False

            return True

    # =====================================================
    # ADD KEY
    # =====================================================

    def add_key(

        self,

        session_id,

        key_id
    ):

        with self.lock:

            if session_id not in self.sessions:

                return False

            session = self.sessions[
                session_id
            ]

            session["keys"].append(
                key_id
            )

            session["sync_index"] += 1

            session["last_activity"] = (
                time.time()
            )

            self.key_session_map[
                key_id
            ] = session_id

            self.audit.log(

                "SESSION_KEY_ADDED",

                (
                    f"session={session_id} "
                    f"key={key_id}"
                ),

                "SESSION"
            )

            return True

    # =====================================================
    # ADD MESSAGE
    # =====================================================

    def add_message(

        self,

        session_id,

        message_id=None
    ):

        with self.lock:

            if session_id not in self.sessions:
                return False

            session = self.sessions[
                session_id
            ]

            if message_id is None:

                message_id = str(
                    uuid.uuid4()
                )[:8]

            if not self.verify_message_id(
                message_id
            ):

                session[
                    "replay_attempts"
                ] += 1

                return False

            session["messages"] += 1

            session[
                "message_counter"
            ] += 1

            session[
                "last_activity"
            ] = time.time()

            session[
                "message_ids"
            ].append(message_id)

            self.message_session_map[
                message_id
            ] = session_id

            return True

    # =====================================================
    # VERIFY SESSION
    # =====================================================

    def verify_session(
        self,
        session_id
    ):

        with self.lock:

            if session_id not in self.sessions:
                return False

            session = self.sessions[
                session_id
            ]

            session["verified"] = True

            session[
                "last_activity"
            ] = time.time()

            self.audit.log(

                "SESSION_VERIFIED",

                (
                    f"session={session_id}"
                ),

                "SESSION"
            )

            return True

    # =====================================================
    # SECURITY EVENT
    # =====================================================

    def add_security_event(

        self,

        session_id,

        event
    ):

        with self.lock:

            if session_id not in self.sessions:
                return False

            self.sessions[
                session_id
            ]["security_events"].append({

                "event":
                    event,

                "timestamp":
                    time.time()
            })

            return True

    # =====================================================
    # CLOSE SESSION
    # =====================================================

    def close_session(
        self,
        session_id
    ):

        with self.lock:

            if session_id not in self.sessions:
                return False

            session = self.sessions[
                session_id
            ]

            session["status"] = "CLOSED"

            session["closed_at"] = (
                time.time()
            )

            session[
                "last_activity"
            ] = time.time()

            self.closed_sessions += 1

            self.audit.log(

                "SESSION_CLOSED",

                (
                    f"session={session_id}"
                ),

                "SESSION"
            )

            return True

    # =====================================================
    # EXPIRE SESSION
    # =====================================================

    def expire_session(
        self,
        session_id
    ):

        with self.lock:

            if session_id not in self.sessions:
                return False

            session = self.sessions[
                session_id
            ]

            session["status"] = "EXPIRED"

            session[
                "expired_at"
            ] = time.time()

            self.expired_sessions += 1

            self.audit.log(

                "SESSION_EXPIRED",

                (
                    f"session={session_id}"
                ),

                "SESSION"
            )

            return True

    # =====================================================
    # CHECK EXPIRATION
    # =====================================================

    def check_expired_sessions(self):

        current = time.time()

        expired = []

        with self.lock:

            for sid, session in self.sessions.items():

                if (

                    session["status"]
                    == "ACTIVE"
                    and
                    current > session["expires_at"]
                ):

                    expired.append(sid)

            for sid in expired:

                self.expire_session(sid)

        return expired

    # =====================================================
    # GET SESSION
    # =====================================================

    def get_session(
        self,
        session_id
    ):

        return self.sessions.get(
            session_id
        )

    # =====================================================
    # GET SESSION BY KEY
    # =====================================================

    def get_session_by_key(
        self,
        key_id
    ):

        sid = self.key_session_map.get(
            key_id
        )

        if not sid:
            return None

        return self.sessions.get(sid)

    # =====================================================
    # GET SESSION BY MESSAGE
    # =====================================================

    def get_session_by_message(
        self,
        message_id
    ):

        sid = self.message_session_map.get(
            message_id
        )

        if not sid:
            return None

        return self.sessions.get(sid)

    # =====================================================
    # ACTIVE SESSIONS
    # =====================================================

    def active_sessions(self):

        active = {}

        for sid, session in self.sessions.items():

            if session["status"] == "ACTIVE":

                active[sid] = session

        return active

    # =====================================================
    # CLOSED SESSIONS
    # =====================================================

    def closed_sessions_list(self):

        closed = {}

        for sid, session in self.sessions.items():

            if session["status"] == "CLOSED":

                closed[sid] = session

        return closed

    # =====================================================
    # STATS
    # =====================================================

    def stats(self):

        active = len(
            self.active_sessions()
        )

        return {

            "created_sessions":
                self.created_sessions,

            "closed_sessions":
                self.closed_sessions,

            "expired_sessions":
                self.expired_sessions,

            "failed_sessions":
                self.failed_sessions,

            "active_sessions":
                active,

            "tracked_keys":
                len(self.key_session_map),

            "tracked_messages":
                len(self.message_session_map),

            "replay_attempts":
                self.replay_attempts,

            "sync_failures":
                self.sync_failures
        }

    # =====================================================
    # EXPORT
    # =====================================================

    def export_all(self):

        return {

            "sessions":
                self.sessions,

            "stats":
                self.stats()
        }

    # =====================================================
    # DEBUG
    # =====================================================

    def debug_dump(self):

        return self.export_all()


# =========================================================
# STANDALONE TEST
# =====================================================

if __name__ == "__main__":

    sm = SessionManager()

    sid = sm.create_session(

        source_node="IITR",

        destination_node="IITJ"
    )

    sm.add_key(sid, "0")

    sm.add_message(
        sid,
        "MSG001"
    )

    sm.verify_session(sid)

    print("\nSESSION DATA")

    print(
        sm.get_session(sid)
    )

    print("\nSTATS")

    print(
        sm.stats()
    )