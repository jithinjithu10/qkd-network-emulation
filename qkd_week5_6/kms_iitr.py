"""
kms_iitr.py
------------
Central Key Management System (KMS) – IIT Roorkee node.

Implements:
- ETSI-style key provisioning
- Q Buffer (READY keys)
- S Buffer (RESERVED keys per session)
- ENC / DEC key pool separation
- Policy-driven key selection
- Persistent storage
- Audit logging
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import secrets
import uuid

from models import Key, KeyState, KeyRole
from storage import (
    init_db,
    store_key,
    fetch_ready_key,
    reserve_key,
    consume_key,
    count_ready_keys
)
from audit import log_event


# -------------------------------------------------
# Lifespan handler (startup / shutdown)
# -------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler replaces deprecated startup/shutdown events.
    """
    init_db()
    log_event("IITR-KMS started")
    yield
    log_event("IITR-KMS stopped")


# Create FastAPI application
app = FastAPI(lifespan=lifespan)


# -------------------------------------------------
# Status Endpoint (ETSI-style capability exposure)
# -------------------------------------------------
@app.get("/api/v1/status")
def get_status():
    """
    Health and capability endpoint for the KMS.
    """
    return {
        "status": "UP",
        "kms_id": "IITR-KMS",
        "supported_key_sizes": [128, 256],
        "supported_roles": ["ENC", "DEC"],
        "max_keys_per_request": 10
    }


# -------------------------------------------------
# Key Generation Endpoint (Q Buffer fill)
# -------------------------------------------------
@app.post("/api/v1/keys/generate")
def generate_keys(request: dict):
    """
    Generate cryptographic keys and store them in Q Buffer.
    """
    number_of_keys = request["number_of_keys"]
    key_size = request["key_size"]
    role = request.get("role", "ENC")  # Default ENC

    keys = []

    for _ in range(number_of_keys):
        # Generate cryptographically secure random key
        key_bytes = key_size // 8
        key_value = secrets.token_bytes(key_bytes).hex()

        # Create Key object (Q Buffer entry)
        key = Key(
            key_id=str(uuid.uuid4()),
            key_value=key_value,
            key_size=key_size,
            created_at=datetime.now(timezone.utc).isoformat(),
            ttl_seconds=300,
            role=KeyRole(role)
        )

        key.state = KeyState.READY

        # Store key in persistent storage
        store_key(key)
        log_event(f"Key generated and stored: {key.key_id} ({role})")

        keys.append({
            "key_id": key.key_id,
            "role": role
        })

    return {
        "status": "SUCCESS",
        "generated_keys": keys
    }


# -------------------------------------------------
# Key Allocation Endpoint (Q → S Buffer)
# -------------------------------------------------
@app.post("/api/v1/keys/allocate")
def allocate_key(request: dict):
    """
    Allocate a key for a session/application.
    """
    session_id = request["session_id"]
    role = KeyRole(request.get("role", "ENC"))

    key_id = fetch_ready_key(role)

    if not key_id:
        return {"status": "NO_KEYS_AVAILABLE"}

    reserve_key(key_id, session_id)
    log_event(f"Key reserved: {key_id} for session {session_id}")

    return {
        "status": "RESERVED",
        "key_id": key_id,
        "session_id": session_id
    }


# -------------------------------------------------
# Key Consumption Endpoint
# -------------------------------------------------
@app.post("/api/v1/keys/consume")
def consume_reserved_key(request: dict):
    """
    Consume a previously reserved key.
    """
    key_id = request["key_id"]

    consume_key(key_id)
    log_event(f"Key consumed: {key_id}")

    return {
        "status": "CONSUMED",
        "key_id": key_id
    }


# -------------------------------------------------
# Buffer Monitoring Endpoint (Week 6)
# -------------------------------------------------
@app.get("/api/v1/buffer/status")
def buffer_status():
    """
    Expose buffer state for monitoring and adaptive refill.
    """
    return {
        "ENC_READY": count_ready_keys(KeyRole.ENC),
        "DEC_READY": count_ready_keys(KeyRole.DEC)
    }
