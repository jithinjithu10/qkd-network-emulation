# Import FastAPI framework to build REST-based APIs
from fastapi import FastAPI

# Used to make HTTP requests to Remote KMS and Controller
import requests

# Import key generation function from the quantum emulation layer
from emulator import generate_key

# Used to deliberately introduce delay for TTL expiry demonstration
import time

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
    This function represents the Local KMS supplying keys to an application.
    It generates keys, relays them to the Remote KMS, and returns valid keys.
    """

    # Number of keys requested by the application
    required = req["number_of_keys"]

    # Size of each key in bits (e.g., 128 or 256)
    key_size = req["key_size"]

    # List to store keys successfully accepted by Remote KMS
    keys = []

    # Counter to limit retry attempts when keys expire
    attempts = 0
    MAX_ATTEMPTS = 5

    # Try generating and relaying keys until enough are accepted
    # or until maximum retry attempts are reached
    while len(keys) < required and attempts < MAX_ATTEMPTS:
        # Increment retry attempt counter
        attempts += 1

        # Generate a new key using the quantum emulation layer
        # TTL is intentionally small to demonstrate expiry behavior
        key_data = generate_key(key_size, ttl_seconds=30)

        # Introduce artificial delay so the key expires before relay
        # time.sleep(3) # Disabled for transmission demo

        # Log attempt for demonstration and debugging
        print(f"Attempt {attempts}: sending key {key_data['key_id']}")

        # Send the key to Remote KMS via REST API
        response = requests.post(
            REMOTE_KMS_URL,
            json=key_data
        ).json()

        # If Remote KMS accepts the key, add it to the response list
        if response["status"] == "RECEIVED":
            keys.append({
                "key_id": key_data["key_id"],
                "key_value": key_data["key_value"]
            })

    # Return final response to application
    # Keys list may be empty if all generated keys expired
    return {
        "status": "SUCCESS",
        "keys": keys
    }

