"""
models.py

Strict ETSI-aligned core data models.

Hybrid-compatible:
- Supports ETSI atomic delivery (READY → CONSUMED)
- Supports reservation lifecycle (READY → RESERVED → CONSUMED)
"""

from enum import Enum
from datetime import datetime, timezone, timedelta


# =================================================
# KEY LIFECYCLE STATES (ETSI-ALIGNED)
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
    Represents a cryptographic key managed by KMS.
    """

    def __init__(
        self,
        key_id: str,
        key_value: str,
        key_size: int,
        ttl_seconds: int
    ):

        self.key_id = key_id
        self.key_value = key_value
        self.key_size = key_size

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
            raise ValueError("Invalid state transition: Key not in READY state")

        if self.is_expired():
            self.state = KeyState.EXPIRED
            raise ValueError("Cannot reserve expired key")

        self.state = KeyState.RESERVED
        self.session_id = session_id

    def consume(self):
        """
        Supports:
        READY → CONSUMED  (ETSI atomic mode)
        RESERVED → CONSUMED (Session mode)
        """

        if self.state not in [KeyState.READY, KeyState.RESERVED]:
            raise ValueError("Invalid state transition to CONSUMED")

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


# =================================================
# SESSION MODEL (Internal Use)
# =================================================

class Session:
    """
    Represents ETSI session between application and KMS.
    Internal abstraction (not part of ETSI external API).
    """

    def __init__(self, session_id: str, timeout_seconds: int):

        self.session_id = session_id
        self.created_at = datetime.now(timezone.utc)
        self.timeout = timedelta(seconds=timeout_seconds)
        self.active = True

    # -------------------------------------------------
    # SESSION VALIDATION
    # -------------------------------------------------

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