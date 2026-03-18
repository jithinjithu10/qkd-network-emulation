"""
kms_iitr.py
------------

Central Key Management System (KMS)
Node: IITR

Weeks 4–12 Fully Integrated
ETSI-Aligned Architecture
Production-Grade
Stress-Test Ready
Multi-Node Ready
"""

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import secrets
import uuid
import os

from models import Key, KeyState, KeyRole
from storage import (
    init_db,
    store_key,
    promote_generated_keys,
    fetch_and_reserve,
    consume_key,
    count_ready_keys,
    count_total_keys,
    count_by_state,
    detect_key_exhaustion,
    expire_old_keys
)
from audit import (
    log_event,
    log_key_event,
    log_policy_event,
    log_service_event
)
from policy import PolicyEngine


# =================================================
# NODE CONFIGURATION
# =================================================

NODE_ID = os.getenv("NODE_ID", "IITR")
NODE_ROLE = "CENTRAL_KMS"

policy_engine = PolicyEngine()


# =================================================
# LIFESPAN
# =================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    expire_old_keys()
    log_event(f"{NODE_ID} KMS started")
    yield
    log_event(f"{NODE_ID} KMS stopped")


app = FastAPI(
    title=f"{NODE_ID} Central KMS",
    lifespan=lifespan
)


# =================================================
# STATUS ENDPOINT (ETSI)
# =================================================

@app.get("/api/v1/status")
def get_status():

    log_service_event("Status requested")

    return {
        "node_id": NODE_ID,
        "node_role": NODE_ROLE,
        "status": "UP",
        "supported_key_sizes": [128, 256],
        "supported_roles": ["ENC", "DEC"],
        "max_keys_per_request": 10,
        "policy": {
            "per_app_limit": policy_engine.per_app_limit,
            "refill_threshold": policy_engine.refill_threshold
        }
    }


# =================================================
# KEY GENERATION
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

    if not policy_engine.allow_request(app_id, number_of_keys):
        log_policy_event(f"Quota exceeded for app {app_id}")
        raise HTTPException(status_code=403, detail="Application quota exceeded")

    role = KeyRole(role_str)

    generated = []

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
        store_key(key, node_id=NODE_ID)

        log_key_event(f"[{NODE_ID}] Generated {key.key_id}")

        generated.append({
            "key_id": key.key_id,
            "role": role.value
        })

    return {
        "node_id": NODE_ID,
        "status": "GENERATED",
        "count": len(generated),
        "keys": generated
    }


# =================================================
# PROMOTE GENERATED → READY
# =================================================

@app.post("/api/v1/keys/promote")
def promote_keys():

    promote_generated_keys(node_id=NODE_ID)
    log_key_event(f"[{NODE_ID}] Keys promoted")

    return {
        "node_id": NODE_ID,
        "status": "PROMOTED"
    }


# =================================================
# ALLOCATE KEY (ATOMIC)
# =================================================

@app.post("/api/v1/keys/allocate")
def allocate_key(request: dict):

    session_id = request.get("session_id")
    role_str = request.get("role", "ENC")

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")

    role = KeyRole(role_str)

    expire_old_keys()

    key_id = fetch_and_reserve(role, session_id, node_id=NODE_ID)

    if not key_id:
        log_policy_event("Allocation failed – No READY keys")
        return {
            "node_id": NODE_ID,
            "status": "NO_KEYS_AVAILABLE"
        }

    log_key_event(f"[{NODE_ID}] Reserved {key_id} for {session_id}")

    return {
        "node_id": NODE_ID,
        "status": "RESERVED",
        "key_id": key_id,
        "session_id": session_id
    }


# =================================================
# CONSUME KEY
# =================================================

@app.post("/api/v1/keys/consume")
def consume_reserved_key(request: dict):

    key_id = request.get("key_id")

    if not key_id:
        raise HTTPException(status_code=400, detail="Key ID required")

    consume_key(key_id)

    log_key_event(f"[{NODE_ID}] Consumed {key_id}")

    return {
        "node_id": NODE_ID,
        "status": "CONSUMED",
        "key_id": key_id
    }


# =================================================
# BUFFER STATUS
# =================================================

@app.get("/api/v1/buffer/status")
def buffer_status():

    expire_old_keys()

    enc_ready = count_ready_keys(KeyRole.ENC, NODE_ID)
    dec_ready = count_ready_keys(KeyRole.DEC, NODE_ID)

    return {
        "node_id": NODE_ID,
        "ENC_READY": enc_ready,
        "DEC_READY": dec_ready,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# =================================================
# METRICS (WEEK 11–12)
# =================================================

@app.get("/api/v1/metrics")
def get_metrics():

    return {
        "node_id": NODE_ID,
        "total_keys": count_total_keys(),
        "ready_keys": count_by_state(KeyState.READY),
        "reserved_keys": count_by_state(KeyState.RESERVED),
        "consumed_keys": count_by_state(KeyState.CONSUMED),
        "expired_keys": count_by_state(KeyState.EXPIRED),
        "exhaustion_detected": detect_key_exhaustion()
    }


# =================================================
# ETSI v2 GET_KEY (Atomic)
# =================================================

@app.post("/api/v2/get_key")
def etsi_get_key(request: dict):

    session_id = request.get("session_id", str(uuid.uuid4()))
    role = KeyRole(request.get("role", "ENC"))

    key_id = fetch_and_reserve(role, session_id, node_id=NODE_ID)

    if not key_id:
        return {
            "status": "NO_KEY_AVAILABLE"
        }

    return {
        "status": "KEY_AVAILABLE",
        "key_id": key_id,
        "session_id": session_id
    }
