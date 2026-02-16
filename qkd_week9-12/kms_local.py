"""
kms_local.py
------------

QKD Client Node
Weeks 8–10 Implementation

Acts as:
- ETSI-style KMS Client
- Application-facing interface
- Secure session handler
- Failure-aware key requester
"""

from fastapi import FastAPI, HTTPException
import requests
import os
import uuid

app = FastAPI(title="QKD Client Node")

# =================================================
# CONFIGURATION
# =================================================

CENTRAL_KMS_URL = os.getenv(
    "CENTRAL_KMS_URL",
    "http://10.13.2.132:8001"
)

REQUEST_TIMEOUT = 5


# =================================================
# STATUS CHECK
# =================================================

@app.get("/api/v1/status")
def get_status():

    try:
        response = requests.get(
            f"{CENTRAL_KMS_URL}/api/v1/status",
            timeout=REQUEST_TIMEOUT
        )

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# GENERATE KEYS (Forward to KMS)
# =================================================

@app.post("/api/v1/keys/generate")
def generate_keys(request: dict):

    try:
        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/generate",
            json=request,
            timeout=REQUEST_TIMEOUT
        )

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# PROMOTE KEYS
# =================================================

@app.post("/api/v1/keys/promote")
def promote_keys():

    try:
        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/promote",
            timeout=REQUEST_TIMEOUT
        )

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# ALLOCATE KEY (Session abstraction)
# =================================================

@app.post("/api/v1/keys/allocate")
def allocate_key(request: dict):

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
            "kms_response": response.json()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# CONSUME KEY
# =================================================

@app.post("/api/v1/keys/consume")
def consume_key(request: dict):

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================
# BUFFER STATUS
# =================================================

@app.get("/api/v1/buffer/status")
def buffer_status():

    try:
        response = requests.get(
            f"{CENTRAL_KMS_URL}/api/v1/buffer/status",
            timeout=REQUEST_TIMEOUT
        )

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
