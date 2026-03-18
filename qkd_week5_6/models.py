"""
models.py
----------
Defines data models and lifecycle states for cryptographic keys
used in Week 5 (Advanced Key Buffering) and
Week 6 (Policy-Driven KMS).
"""

from enum import Enum
from datetime import datetime, timezone, timedelta


# -------------------------------------------------
# Key Lifecycle States
# -------------------------------------------------
class KeyState(str, Enum):
    """
    Complete lifecycle of a key inside the KMS.
    """
    GENERATED = "GENERATED"     # Key created and placed in Q Buffer
    READY = "READY"             # Key available for allocation
    RESERVED = "RESERVED"       # Key allocated to a session (S Buffer)
    CONSUMED = "CONSUMED"       # Key used by application
    EXPIRED = "EXPIRED"         # Key expired due to TTL


# -------------------------------------------------
# Key Usage Role
# -------------------------------------------------
class KeyRole(str, Enum):
    """
    Defines how a key is used.
    """
    ENC = "ENC"   # Encryption key
    DEC = "DEC"   # Decryption key


# -------------------------------------------------
# Key Data Model
# -------------------------------------------------
class Key:
    """
    Represents a cryptographic key managed by the Central KMS.
    """

    def __init__(
        self,
        key_id: str,
        key_value: str,
        key_size: int,
        created_at: str,
        ttl_seconds: int,
        role: KeyRole
    ):
        # Unique identifier
        self.key_id = key_id

        # Final cryptographic key material
        self.key_value = key_value

        # Key size in bits
        self.key_size = key_size

        # Creation timestamp (UTC)
        self.created_at = datetime.fromisoformat(created_at)

        # Time-to-live
        self.ttl = timedelta(seconds=ttl_seconds)

        # Encryption or Decryption pool
        self.role = role

        # Initial lifecycle state
        self.state = KeyState.GENERATED

        # Session ID (used when key is RESERVED)
        self.session_id = None

        # Policy metadata (Week 6)
        self.usage_count = 0
        self.freshness_score = 100  # starts fully fresh

    # -------------------------------------------------
    # Expiry Check
    # -------------------------------------------------
    def is_expired(self) -> bool:
        """
        Check whether the key has exceeded its TTL.
        """
        return datetime.now(timezone.utc) > (self.created_at + self.ttl)

    # -------------------------------------------------
    # Freshness Update (Week 6)
    # -------------------------------------------------
    def degrade_freshness(self):
        """
        Reduce freshness score after each use.
        """
        self.freshness_score = max(0, self.freshness_score - 10)

