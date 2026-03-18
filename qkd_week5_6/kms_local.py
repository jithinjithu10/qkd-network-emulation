"""
kms_local.py
-------------
Local client KMS / application interface.

Implements:
- Key generation request (Q Buffer fill)
- Policy-based key allocation (S Buffer)
- Key consumption lifecycle
"""

from fastapi import FastAPI
import requests
import uuid

app = FastAPI()

# Central KMS (server) address
CENTRAL_KMS_URL = "http://10.13.1.220:8001"


# -------------------------------------------------
# STEP 1: Ask Central KMS to generate keys (Q Buffer)
# -------------------------------------------------
@app.post("/api/v1/keys/generate")
def generate_keys():
    """
    Request Central KMS to generate keys into Q Buffer.
    """
    response = requests.post(
        f"{CENTRAL_KMS_URL}/api/v1/keys/generate",
        json={
            "number_of_keys": 1,
            "key_size": 256,
            "role": "ENC"   # Encryption pool
        }
    )

    return response.json()


# -------------------------------------------------
# STEP 2: Allocate a key for a session (S Buffer)
# -------------------------------------------------
@app.post("/api/v1/keys/allocate")
def allocate_key():
    """
    Request a reserved key for a specific session.
    """
    session_id = str(uuid.uuid4())

    response = requests.post(
        f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
        json={
            "session_id": session_id,
            "role": "ENC"
        }
    )

    return {
        "session_id": session_id,
        "allocation_response": response.json()
    }


# -------------------------------------------------
# STEP 3: Consume a previously reserved key
# -------------------------------------------------
@app.post("/api/v1/keys/consume")
def consume_key(request: dict):
    """
    Consume a reserved key after encryption/decryption.
    """
    key_id = request["key_id"]

    response = requests.post(
        f"{CENTRAL_KMS_URL}/api/v1/keys/consume",
        json={
            "key_id": key_id
        }
    )

    return response.json()


# -------------------------------------------------
# STEP 4: Monitor buffer status (Week 6)
# -------------------------------------------------
@app.get("/api/v1/buffer/status")
def buffer_status():
    """
    Fetch buffer status from Central KMS.
    """
    response = requests.get(
        f"{CENTRAL_KMS_URL}/api/v1/buffer/status"
    )

    return response.json()
