# Enum is used to define a fixed set of key lifecycle states
from enum import Enum

# datetime utilities for timestamp handling and expiry calculation
from datetime import datetime, timezone, timedelta

# KeyState defines the lifecycle states of a QKD key
# These states are used by the KMS to manage key validity
class KeyState(str, Enum):
    INIT = "INIT"        # Key is created but not yet validated or stored
    READY = "READY"      # Key is valid and available for use
    CONSUMED = "CONSUMED"  # Key has been used by an application
    EXPIRED = "EXPIRED"  # Key is no longer valid due to TTL expiry

# Key class represents a single cryptographic key in the QKD system
class Key:
    def __init__(self, key_id, key_value, key_size, created_at, ttl_seconds):
        """
        Initialize a Key object with metadata required for lifecycle tracking.
        """

        # Unique identifier for the key (used for tracking and auditing)
        self.key_id = key_id

        # Actual cryptographic key material
        self.key_value = key_value

        # Size of the key in bits (e.g., 128 or 256)
        self.key_size = key_size

        # Original creation timestamp of the key
        # Parsed from ISO format string sent by Local KMS
        self.created_at = datetime.fromisoformat(created_at)

        # Time-to-live (TTL) of the key expressed as a time duration
        self.ttl = timedelta(seconds=ttl_seconds)

        # Initial lifecycle state of the key
        self.state = KeyState.INIT

    def is_expired(self):
        """
        Check whether the key has exceeded its allowed lifetime.
        """

        # Compare current UTC time with (creation time + TTL)
        # If current time is greater, the key is considered expired
        return datetime.now(timezone.utc) > self.created_at + self.ttl
