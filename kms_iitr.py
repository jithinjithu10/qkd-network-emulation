# Import FastAPI framework to build REST-based APIs
from fastapi import FastAPI

# Import raw key generation function from the emulation layer
from emulator import generate_key

# Import post-processing functions (Week 3)
from post_processing import (
    key_sifting,
    error_filtering,
    privacy_amplification
)

# Create FastAPI application instance (Local KMS - IIT Roorkee)
app = FastAPI()


# ----------------------------------------------------------------------
# ETSI GS QKD 014 - getStatus API
# ----------------------------------------------------------------------
@app.get("/api/v1/status")
def get_status():
    """
    ETSI GS QKD 014 - KMS status endpoint
    """
    return {
        "status": "UP",
        "kms_id": "IITR-KMS",
        "supported_key_sizes": [128, 256],
        "max_keys_per_request": 10
    }


# ----------------------------------------------------------------------
# ETSI GS QKD 014 - getKey API
# ----------------------------------------------------------------------
@app.post("/api/v1/keys/get")
def get_keys(req: dict):
    """
    Local KMS supplies keys to an application.

    Flow:
    1. Generate raw key (emulation layer)
    2. Apply post-processing (Week 3)
       - Key sifting
       - Error filtering
       - Privacy amplification
    3. Return processed key directly to application
       (ETSI demo mode – no Remote KMS dependency)
    """

    # Number of keys requested by the application
    required = req["number_of_keys"]

    # Size of each key in bits (e.g., 128 or 256)
    key_size = req["key_size"]

    # List to store processed keys
    keys = []

    # Safety limit to avoid infinite loops
    attempts = 0
    MAX_ATTEMPTS = 5

    # Generate keys until requested count is met
    while len(keys) < required and attempts < MAX_ATTEMPTS:
        attempts += 1

        # --------------------------------------------------------------
        # STEP 1: Generate RAW key using the emulation layer
        # --------------------------------------------------------------
        key_data = generate_key(key_size, ttl_seconds=30)

        raw_key = key_data["raw_key_value"]
        print(f"Attempt {attempts}: Raw key generated ({raw_key[:20]}...)")

        # --------------------------------------------------------------
        # STEP 2: Post-processing pipeline (Week 3)
        # --------------------------------------------------------------
        sifted_key = key_sifting(raw_key)
        filtered_key = error_filtering(sifted_key)
        final_key = privacy_amplification(filtered_key)

        print(f"Processed key generated ({final_key[:20]}...)")

        # --------------------------------------------------------------
        # STEP 3: ETSI DEMO MODE
        # Directly return processed key to application
        # --------------------------------------------------------------
        keys.append({
            "key_id": key_data["key_id"],
            "key_value": final_key
        })

    # --------------------------------------------------------------
    # Final response to application
    # --------------------------------------------------------------
    return {
        "status": "SUCCESS",
        "keys": keys
    }
