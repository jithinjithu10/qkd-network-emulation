"""
kms_local.py
-------------
Local Client KMS / Application Interface.

Implements:
- GET_STATUS
- Key generation request (Q Buffer fill)
- Key promotion
- Policy-based key allocation (S Buffer)
- Key consumption lifecycle
- Buffer monitoring
- Session abstraction
- Server-flexible configuration
"""

from fastapi import FastAPI, HTTPException
import requests
import uuid
import os

app = FastAPI(title="Local Client KMS")

# =================================================
# SERVER CONFIGURATION (SERVER FLEXIBLE)
# =================================================

CENTRAL_KMS_URL = os.getenv(
    "CENTRAL_KMS_URL",
    "http://43.205.178.40:8001"   # Default: AWS cloud KMS
)

REQUEST_TIMEOUT = 5  # seconds


# =================================================
# WEEK 8 – SERVICE INTERFACE: GET_STATUS
# =================================================

@app.get("/api/v1/status")
def get_status():
    """
    Fetch status from Central KMS.
    """
    try:
        response = requests.get(
            f"{CENTRAL_KMS_URL}/api/v1/status",
            timeout=REQUEST_TIMEOUT
        )
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# WEEK 5 – GENERATE KEYS (Q BUFFER FILL)
# =================================================

@app.post("/api/v1/keys/generate")
def generate_keys(request: dict):
    """
    Ask Central KMS to generate keys.
    """

    number_of_keys = request.get("number_of_keys", 1)
    key_size = request.get("key_size", 256)
    role = request.get("role", "ENC")

    try:
        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/generate",
            json={
                "number_of_keys": number_of_keys,
                "key_size": key_size,
                "role": role
            },
            timeout=REQUEST_TIMEOUT
        )

        return response.json()

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# WEEK 5 – PROMOTE GENERATED → READY
# =================================================

@app.post("/api/v1/keys/promote")
def promote_keys():
    """
    Trigger key promotion phase.
    """

    try:
        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/promote",
            timeout=REQUEST_TIMEOUT
        )

        return response.json()

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# WEEK 6 – KEY ALLOCATION (SESSION ABSTRACTION)
# =================================================

@app.post("/api/v1/keys/allocate")
def allocate_key(request: dict):
    """
    Allocate key for a session.
    """

    role = request.get("role", "ENC")
    session_id = str(uuid.uuid4())

    try:
        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
            json={
                "session_id": session_id,
                "role": role
            },
            timeout=REQUEST_TIMEOUT
        )

        return {
            "session_id": session_id,
            "allocation_response": response.json()
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# WEEK 6 – KEY CONSUMPTION
# =================================================

@app.post("/api/v1/keys/consume")
def consume_key(request: dict):
    """
    Consume reserved key.
    """

    key_id = request.get("key_id")

    if not key_id:
        raise HTTPException(status_code=400, detail="key_id required")

    try:
        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/consume",
            json={"key_id": key_id},
            timeout=REQUEST_TIMEOUT
        )

        return response.json()

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# WEEK 6 – BUFFER MONITORING
# =================================================

@app.get("/api/v1/buffer/status")
def buffer_status():
    """
    Fetch READY key counts from Central KMS.
    """

    try:
        response = requests.get(
            f"{CENTRAL_KMS_URL}/api/v1/buffer/status",
            timeout=REQUEST_TIMEOUT
        )

        return response.json()

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
