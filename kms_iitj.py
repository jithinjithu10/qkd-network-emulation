# Import FastAPI framework to create REST APIs
from fastapi import FastAPI

# Import Key class and KeyState enum for key lifecycle handling
from models import Key, KeyState

# Create FastAPI application instance
app = FastAPI()

# In-memory buffer to store valid (non-expired) keys at Remote KMS
KEY_BUFFER = []

# REST API endpoint to receive relayed keys from Local KMS
@app.post("/api/v1/relay")
def receive_relay(key_data: dict):
    """
    This function represents the Remote KMS receiving a key
    from the Local KMS via a REST API call.
    """

    # Create a Key object using metadata sent by Local KMS
    # IMPORTANT: created_at is taken from Local KMS to ensure
    # expiry is checked using the original key creation time
    key = Key(
        key_id=key_data["key_id"],          # Unique identifier of the key
        key_value=key_data["key_value"],    # Actual key material
        key_size=key_data["key_size"],      # Size of the key in bits
        created_at=key_data["created_at"],  # Original creation timestamp
        ttl_seconds=key_data["ttl"]          # Time-to-live of the key
    )

    # Check whether the key has expired based on TTL and creation time
    if key.is_expired():
        # If expired, mark key state as EXPIRED
        key.state = KeyState.EXPIRED

        # Log expiry event (useful for demo and debugging)
        print(" Key expired at Remote KMS:", key.key_id)

        # Reject the key and inform Local KMS
        return {"status": "REJECTED", "reason": "Key expired"}

    # If key is still valid, mark it as READY
    key.state = KeyState.READY

    # Store the valid key in the Remote KMS buffer
    KEY_BUFFER.append(key)

    # Log successful storage
    print(" Key stored at Remote KMS:", key.key_id)

    # Acknowledge successful reception to Local KMS
    return {"status": "RECEIVED"}
