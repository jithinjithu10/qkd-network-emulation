"""
models.py (UPDATED - RESEARCH LEVEL)

Fixes:
- Removed session abstraction
- Removed sync- logic
- Simplified key lifecycle
- Clean ETSI-aligned design
"""

from enum import Enum
from datetime import datetime, timezone, timedelta
import hashlib


# =================================================
# KEY STATES
# =================================================

class KeyState(str, Enum):

    READY = "READY"
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
        self.used_at = None

        # fingerprint (useful for sync validation)
        self.fingerprint = self._compute_fingerprint()

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
    # STATE TRANSITIONS
    # -------------------------------------------------

    def consume(self):

        if self.state != KeyState.READY:
            raise ValueError("Key not READY")

        if self.is_expired():
            self.expire()
            raise ValueError("Key expired")

        self.state = KeyState.CONSUMED
        self.used_at = datetime.now(timezone.utc)

    def expire(self):

        self.state = KeyState.EXPIRED

    # -------------------------------------------------
    # MATCH (SYNC VALIDATION)
    # -------------------------------------------------

    def matches(self, other_key) -> bool:
        return self.fingerprint == other_key.fingerprint

    # -------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------

    def to_dict(self):

        return {
            "key_id": self.key_id,
            "key": self.key_value,
            "size": self.key_size,
            "origin": self.origin_node,
            "fingerprint": self.fingerprint,
            "expires_at": self.expires_at.isoformat()
        }

    # -------------------------------------------------
    # DEBUG
    # -------------------------------------------------

    def __repr__(self):

        return (
            f"<Key id={self.key_id} "
            f"state={self.state} "
            f"origin={self.origin_node}>"
        )