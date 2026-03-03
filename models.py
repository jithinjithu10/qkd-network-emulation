"""
models.py

ETSI-aligned core data models.
Scalable for multi-node QKD network.

Supports:
- Atomic ETSI key delivery
- Reservation lifecycle
- Node-aware key origin
- Strict state transitions
"""

from enum import Enum
from datetime import datetime, timezone, timedelta


# =================================================
# KEY LIFECYCLE STATES
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
    """
    Represents a cryptographic key managed by a QKD node.
    """

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
        self.origin_node = origin_node  # For inter-KMS tracking

        self.created_at = datetime.now(timezone.utc)
        self.ttl = timedelta(seconds=ttl_seconds)

        self.state = KeyState.READY
        self.session_id = None

    # -------------------------------------------------
    # EXPIRY CHECK
    # -------------------------------------------------

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > (self.created_at + self.ttl)

    # -------------------------------------------------
    # STATE TRANSITIONS
    # -------------------------------------------------

    def reserve(self, session_id: str):
        """
        READY → RESERVED
        """

        if self.state != KeyState.READY:
            raise ValueError("Key not in READY state")

        if self.is_expired():
            self.expire()
            raise ValueError("Cannot reserve expired key")

        self.state = KeyState.RESERVED
        self.session_id = session_id

    def consume(self):
        """
        Supports:
        READY → CONSUMED (ETSI atomic)
        RESERVED → CONSUMED (session mode)
        """

        if self.state not in (KeyState.READY, KeyState.RESERVED):
            raise ValueError("Invalid transition to CONSUMED")

        self.state = KeyState.CONSUMED
        self.session_id = None

    def expire(self):
        """
        Any non-consumed key can expire.
        """

        if self.state == KeyState.CONSUMED:
            return

        self.state = KeyState.EXPIRED
        self.session_id = None

    # -------------------------------------------------
    # SERIALIZATION (for inter-KMS transfer)
    # -------------------------------------------------

    def to_dict(self):
        return {
            "key_ID": self.key_id,
            "key": self.key_value,
            "size": self.key_size,
            "origin": self.origin_node
        }


# =================================================
# SESSION MODEL (INTERNAL ONLY)
# =================================================

class Session:
    """
    Internal session abstraction.
    Not part of ETSI external API.
    """

    def __init__(self, session_id: str, timeout_seconds: int):

        self.session_id = session_id
        self.created_at = datetime.now(timezone.utc)
        self.timeout = timedelta(seconds=timeout_seconds)
        self.active = True

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > (self.created_at + self.timeout)

    def validate(self):

        if not self.active:
            raise ValueError("Session is closed")

        if self.is_expired():
            self.active = False
            raise ValueError("Session expired")

    def close(self):
        self.active = False