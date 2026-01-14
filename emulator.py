# secrets module provides cryptographically secure random numbers
# This is used to generate strong random key material
import secrets

# uuid is used to generate a unique identifier for each key
import uuid

# datetime utilities for timestamping key creation in UTC
from datetime import datetime, timezone

def generate_key(key_size_bits: int, ttl_seconds=30):
    """
    Generate a cryptographic key with metadata.
    This function acts as a software-based QKD emulation layer.
    """

    # Convert key size from bits to bytes
    # Example: 256 bits -> 32 bytes
    key_bytes = key_size_bits // 8

    # Return the generated key and its metadata as a dictionary
    return {
        # Unique identifier for tracking the key across KMS nodes
        "key_id": str(uuid.uuid4()),

        # Cryptographically secure random key material
        # Generated using OS-level entropy sources
        "key_value": secrets.token_bytes(key_bytes).hex(),

        # Size of the key in bits
        "key_size": key_size_bits,

        # Time-to-live (TTL) of the key in seconds
        # Determines how long the key remains valid
        "ttl": ttl_seconds,

        # UTC timestamp indicating when the key was created
        # Used by Remote KMS to independently validate expiry
        "created_at": datetime.now(timezone.utc).isoformat()
    }
