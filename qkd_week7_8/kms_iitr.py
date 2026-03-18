"""
kms_iitr.py
------------
Central Key Management System (KMS) – IIT Roorkee node.

Integrated:
- Week 4: Core KMS
- Week 5: Q/S Buffers
- Week 6: TTL + Policy
- Week 7: Control Plane Ready
- Week 8: Service Interface Layer (v2 mounted)
"""

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import secrets
import uuid

from models import Key, KeyState, KeyRole
from storage import (
    init_db,
    store_key,
    promote_generated_keys,
    fetch_ready_key,
    reserve_key,
    consume_key,
    count_ready_keys,
    expire_old_keys
)
from audit import (
    log_event,
    log_key_event,
    log_policy_event,
    log_service_event
)
from policy import PolicyEngine
from service_interface import router as service_router


# =================================================
# GLOBAL POLICY ENGINE
# =================================================
policy_engine = PolicyEngine()


# =================================================
# LIFESPAN HANDLER
# =================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    expire_old_keys()
    log_event("IITR-KMS started")
    yield
    log_event("IITR-KMS stopped")


app = FastAPI(title="IITR Central KMS", lifespan=lifespan)

# Mount Week 8 Service Interface
app.include_router(service_router)


# =================================================
# WEEK 8 – GET_STATUS
# =================================================
@app.get("/api/v1/status")
def get_status():

    log_service_event("Status requested")

    return {
        "status": "UP",
        "kms_id": "IITR-KMS",
        "supported_key_sizes": [128, 256],
        "supported_roles": ["ENC", "DEC"],
        "max_keys_per_request": 10
    }


# =================================================
# WEEK 5 – KEY GENERATION (Q BUFFER FILL)
# =================================================
@app.post("/api/v1/keys/generate")
def generate_keys(request: dict):

    number_of_keys = request.get("number_of_keys")
    key_size = request.get("key_size")
    role_str = request.get("role", "ENC")
    app_id = request.get("app_id", "DEFAULT_APP")

    if number_of_keys is None or key_size is None:
        raise HTTPException(status_code=400, detail="Missing parameters")

    if key_size not in [128, 256]:
        raise HTTPException(status_code=400, detail="Unsupported key size")

    if number_of_keys <= 0 or number_of_keys > 10:
        raise HTTPException(status_code=400, detail="Max 10 keys per request")

    # POLICY: per-app limit
    if not policy_engine.allow_request(app_id, number_of_keys):
        log_policy_event(f"Quota exceeded for app {app_id}")
        raise HTTPException(status_code=403, detail="Application quota exceeded")

    try:
        role = KeyRole(role_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    generated_keys = []

    for _ in range(number_of_keys):

        key_bytes = key_size // 8
        key_value = secrets.token_bytes(key_bytes).hex()

        key = Key(
            key_id=str(uuid.uuid4()),
            key_value=key_value,
            key_size=key_size,
            created_at=datetime.now(timezone.utc),
            ttl_seconds=300,
            role=role
        )

        key.state = KeyState.GENERATED
        store_key(key)

        log_key_event(f"Key generated: {key.key_id} ({role.value})")

        generated_keys.append({
            "key_id": key.key_id,
            "role": role.value
        })

    return {
        "status": "GENERATED",
        "count": len(generated_keys),
        "keys": generated_keys
    }


# =================================================
# WEEK 5 – PROMOTION (GENERATED → READY)
# =================================================
@app.post("/api/v1/keys/promote")
def promote_keys():

    promote_generated_keys()
    log_key_event("Keys promoted from GENERATED to READY")

    return {"status": "PROMOTED"}


# =================================================
# WEEK 6 – KEY ALLOCATION (Policy + TTL)
# =================================================
@app.post("/api/v1/keys/allocate")
def allocate_key(request: dict):

    session_id = request.get("session_id")
    role_str = request.get("role", "ENC")

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")

    try:
        role = KeyRole(role_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    expire_old_keys()

    key_id = fetch_ready_key(role)

    if not key_id:
        log_policy_event("Allocation failed – No READY keys")
        return {"status": "NO_KEYS_AVAILABLE"}

    reserve_key(key_id, session_id)

    log_key_event(f"Key reserved: {key_id} for session {session_id}")

    return {
        "status": "RESERVED",
        "key_id": key_id,
        "session_id": session_id
    }


# =================================================
# WEEK 6 – KEY CONSUMPTION
# =================================================
@app.post("/api/v1/keys/consume")
def consume_reserved_key(request: dict):

    key_id = request.get("key_id")

    if not key_id:
        raise HTTPException(status_code=400, detail="Key ID required")

    consume_key(key_id)

    log_key_event(f"Key consumed: {key_id}")

    return {
        "status": "CONSUMED",
        "key_id": key_id
    }


# =================================================
# WEEK 6 – BUFFER MONITORING
# =================================================
@app.get("/api/v1/buffer/status")
def buffer_status():

    expire_old_keys()

    enc_ready = count_ready_keys(KeyRole.ENC)
    dec_ready = count_ready_keys(KeyRole.DEC)

    return {
        "ENC_READY": enc_ready,
        "DEC_READY": dec_ready
    }
