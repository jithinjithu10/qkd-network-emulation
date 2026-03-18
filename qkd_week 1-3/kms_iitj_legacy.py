# Legacy Remote KMS (Week 2–3)
# Not used in Week 4 – Single Central KMS model


# Import FastAPI framework to create REST APIs
from fastapi import FastAPI

# Import Key class and KeyState enum for key lifecycle handling
from models import Key, KeyState

# Create FastAPI application instance
app = FastAPI()

# In-memory buffer to store valid (non-expired) processed keys
KEY_BUFFER = []


# REST API endpoint to receive relayed keys from Local KMS
@app.post("/api/v1/relay")
def receive_relay(key_data: dict):
    """
    This function represents the Remote KMS receiving a processed key
    from the Local KMS via a REST API call.
    """

    # ------------------------------------------------------------------
    # STEP 1: Validate that a processed key is present
    # ------------------------------------------------------------------
    if "processed_key_value" not in key_data:
        # Reject keys that have not gone through post-processing
        return {
            "status": "REJECTED",
            "reason": "Unprocessed key received"
        }

    # ------------------------------------------------------------------
    # STEP 2: Create Key object using metadata sent by Local KMS
    # IMPORTANT: created_at is taken from Local KMS to ensure
    # expiry is checked using the original key creation time
    # ------------------------------------------------------------------
    key = Key(
        key_id=key_data["key_id"],                 # Unique key identifier
        raw_key_value=None,                        # Raw key is never sent here
        key_size=key_data["key_size"],             # Key size in bits
        created_at=key_data["created_at"],         # Original creation timestamp
        ttl_seconds=key_data["ttl"]                # Time-to-live
    )

    # Attach the processed (final) key
    key.processed_key_value = key_data["processed_key_value"]

    # ------------------------------------------------------------------
    # STEP 3: Check key expiry using TTL
    # ------------------------------------------------------------------
    if key.is_expired():
        key.state = KeyState.EXPIRED
        print(" Key expired at Remote KMS:", key.key_id)
        return {"status": "REJECTED", "reason": "Key expired"}

    # ------------------------------------------------------------------
    # STEP 4: Store valid processed key
    # ------------------------------------------------------------------
    key.state = KeyState.STORED
    KEY_BUFFER.append(key)

    print(" Final key stored at Remote KMS:", key.key_id)

    # Acknowledge successful reception to Local KMS
    return {"status": "RECEIVED"}
