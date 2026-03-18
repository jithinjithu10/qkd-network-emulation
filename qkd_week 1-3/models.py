# ===============================
# MODELS (WEEK 4 – CENTRAL KMS)
# ===============================

from enum import Enum
from datetime import datetime, timezone, timedelta


class KeyState(str, Enum):
    """
    Lifecycle states managed by the Central KMS.
    """
    READY = "READY"        # Key is valid and available
    CONSUMED = "CONSUMED"  # Key has been used by application
    EXPIRED = "EXPIRED"    # Key expired due to TTL


class Key:
    """
    Represents a cryptographic key managed by the Central KMS.
    Raw and intermediate states are intentionally not stored.
    """

    def __init__(self, key_id, key_value, key_size, created_at, ttl_seconds, state=KeyState.READY):
        self.key_id = key_id
        self.key_value = key_value
        self.key_size = key_size

        # Parse ISO timestamp (UTC)
        self.created_at = datetime.fromisoformat(created_at)

        # TTL handling
        self.ttl = timedelta(seconds=ttl_seconds)
        self.state = state

    @property
    def expires_at(self):
        return self.created_at + self.ttl

    def is_expired(self):
        return datetime.now(timezone.utc) > self.expires_at
