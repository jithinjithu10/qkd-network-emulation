"""
models.py

FINAL VERSION (RESEARCH-GRADE)

Enhancements:
- Sync index tracking
- Strong session-key binding
- Node-pair awareness
- Improved validation
"""

from enum import Enum
from datetime import datetime, timezone, timedelta
import hashlib


# =================================================
# KEY STATES
# =================================================

class KeyState(str, Enum):

    READY = "READY"
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"


# =================================================
# KEY MODEL
# =================================================

class Key:

    def __init__(
        self,
        key_id: str,
        key_value: str,
        key_size: int,
        ttl_seconds: int,
        origin_node: str = "LOCAL"
    ):

        self.key_id = key_id
        self.key_value = key_value
        self.key_size = key_size

        self.origin_node = origin_node

        self.created_at = datetime.now(timezone.utc)

        self.ttl = timedelta(seconds=ttl_seconds)
        self.expires_at = self.created_at + self.ttl

        self.state = KeyState.READY
        self.session_id = None

        #  NEW → extract sync index if exists
        self.sync_index = self._extract_index()

        #  fingerprint for validation
        self.fingerprint = self._compute_fingerprint()

        self.used_at = None

    # -------------------------------------------------
    # INDEX EXTRACTION
    # -------------------------------------------------

    def _extract_index(self):

        if self.key_id.startswith("sync-"):
            try:
                return int(self.key_id.split("-")[1])
            except:
                return None
        return None

    # -------------------------------------------------
    # FINGERPRINT
    # -------------------------------------------------

    def _compute_fingerprint(self) -> str:
        return hashlib.sha256(self.key_value.encode()).hexdigest()

    # -------------------------------------------------
    # EXPIRY
    # -------------------------------------------------

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    # -------------------------------------------------
    # SYNC VALIDATION
    # -------------------------------------------------

    def matches(self, other_key) -> bool:
        return self.fingerprint == other_key.fingerprint

    # -------------------------------------------------
    # STATE TRANSITIONS
    # -------------------------------------------------

    def reserve(self, session_id: str):

        if self.state != KeyState.READY:
            raise ValueError("Key not READY")

        if self.is_expired():
            self.expire()
            raise ValueError("Expired key")

        if self.session_id is not None:
            raise ValueError("Key already bound to session")

        self.state = KeyState.RESERVED
        self.session_id = session_id

    def consume(self):

        if self.state not in (KeyState.READY, KeyState.RESERVED):
            raise ValueError("Invalid transition to CONSUMED")

        self.state = KeyState.CONSUMED
        self.used_at = datetime.now(timezone.utc)

        #  clear session binding after use
        self.session_id = None

    def expire(self):

        if self.state == KeyState.CONSUMED:
            return

        self.state = KeyState.EXPIRED
        self.session_id = None

    # -------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------

    def to_dict(self):

        return {
            "key_ID": self.key_id,
            "key": self.key_value,
            "size": self.key_size,
            "origin": self.origin_node,
            "fingerprint": self.fingerprint,
            "sync_index": self.sync_index,
            "expires_at": self.expires_at.isoformat()
        }

    # -------------------------------------------------
    # DEBUG
    # -------------------------------------------------

    def __repr__(self):

        return (
            f"<Key id={self.key_id} "
            f"state={self.state} "
            f"origin={self.origin_node} "
            f"sync_index={self.sync_index}>"
        )


# =================================================
# SESSION MODEL
# =================================================

class Session:

    def __init__(self, session_id: str, timeout_seconds: int):

        self.session_id = session_id

        self.created_at = datetime.now(timezone.utc)

        self.timeout = timedelta(seconds=timeout_seconds)
        self.expires_at = self.created_at + self.timeout

        self.active = True

        #  NEW → bind key
        self.key_id = None

    def bind_key(self, key_id: str):
        self.key_id = key_id

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def validate(self):

        if not self.active:
            raise ValueError("Session closed")

        if self.is_expired():
            self.active = False
            raise ValueError("Session expired")

    def close(self):
        self.active = False

    def __repr__(self):
        return f"<Session id={self.session_id} key={self.key_id} active={self.active}>"