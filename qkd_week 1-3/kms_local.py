# Import FastAPI framework to build REST-based APIs
from fastapi import FastAPI

# Used to make HTTP requests to Remote KMS and Controller
import requests

# Import raw key generation function from the emulation layer
from emulator import generate_key

# Import post-processing functions
from post_processing import (
    key_sifting,
    error_filtering,
    privacy_amplification
)

# Create FastAPI application instance (Local KMS)
app = FastAPI()

# URL of Central Controller (control-plane routing)
CONTROLLER_URL = "http://localhost:8000/api/v1/route"

# URL of Remote KMS relay endpoint
REMOTE_KMS_URL = "http://localhost:8002/api/v1/relay"


# REST API endpoint for Application to Local KMS key request (ETSI QKD-014 style)
@app.post("/api/v1/keys/get")
def get_keys(req: dict):
    """
    Local KMS supplies keys to an application.
    Raw keys are generated, post-processed, relayed to Remote KMS,
    and only accepted keys are returned to the application.
    """

    # Number of keys requested by the application
    required = req["number_of_keys"]

    # Size of each key in bits (e.g., 128 or 256)
    key_size = req["key_size"]

    # List to store keys successfully accepted by Remote KMS
    keys = []

    # Counter to limit retry attempts
    attempts = 0
    MAX_ATTEMPTS = 5

    # Try generating and relaying keys until enough are accepted
    while len(keys) < required and attempts < MAX_ATTEMPTS:
        attempts += 1

        # ------------------------------------------------------------------
        # STEP 1: Generate RAW key using the emulation layer
        # ------------------------------------------------------------------
        key_data = generate_key(key_size, ttl_seconds=30)

        raw_key = key_data["raw_key_value"]
        print(f"Attempt {attempts}: Raw key generated ({raw_key[:20]}...)")

        # ------------------------------------------------------------------
        # STEP 2: Post-processing pipeline
        # ------------------------------------------------------------------
        sifted_key = key_sifting(raw_key)
        filtered_key = error_filtering(sifted_key)
        final_key = privacy_amplification(filtered_key)

        print(f"Processed key generated ({final_key[:20]}...)")

        # Attach processed key to payload
        key_data["processed_key_value"] = final_key

        # Remove raw key before sending (security boundary)
        del key_data["raw_key_value"]

        # ------------------------------------------------------------------
        # STEP 3: Relay processed key to Remote KMS
        # ------------------------------------------------------------------
        response = requests.post(
            REMOTE_KMS_URL,
            json=key_data
        ).json()

        # ------------------------------------------------------------------
        # STEP 4: Accept key only if Remote KMS confirms storage
        # ------------------------------------------------------------------
        if response["status"] == "RECEIVED":
            keys.append({
                "key_id": key_data["key_id"],
                "key_value": final_key
            })

    # Return final response to application
    return {
        "status": "SUCCESS",
        "keys": keys
    }
