"""
models.py
----------
Defines the data model and lifecycle states for cryptographic keys
managed by the Central Key Management System (KMS).
"""

from enum import Enum
from datetime import datetime, timezone, timedelta


class KeyState(str, Enum):
    """
    Enumeration of possible lifecycle states of a key.
    """
    READY = "READY"        # Key is valid and available for use
    CONSUMED = "CONSUMED"  # Key has been issued to an application
    EXPIRED = "EXPIRED"    # Key is no longer valid due to TTL expiry


class Key:
    """
    Represents a cryptographic key stored and managed by the Central KMS.
    Raw or intermediate QKD states are not stored at this stage.
    """

    def __init__(self, key_id, key_value, key_size, created_at, ttl_seconds):
        # Unique identifier for the key
        self.key_id = key_id

        # Final cryptographic key material
        self.key_value = key_value

        # Size of the key in bits (e.g., 128, 256)
        self.key_size = key_size

        # Timestamp when the key was created (UTC)
        self.created_at = datetime.fromisoformat(created_at)

        # Time-to-live duration
        self.ttl = timedelta(seconds=ttl_seconds)

        # Initial lifecycle state
        self.state = KeyState.READY

    def is_expired(self):
        """
        Check whether the key has exceeded its allowed lifetime.
        """
        return datetime.now(timezone.utc) > (self.created_at + self.ttl)
