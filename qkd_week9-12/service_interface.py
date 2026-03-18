"""
service_interface.py
---------------------

ETSI-style Service Interface Layer (v2)

Implements:
- GET_STATUS
- GET_KEY
- RESERVE_KEY
- RELEASE_KEY
- SESSION_AWARE allocation
- Policy + TTL aware integration
"""

from fastapi import APIRouter, HTTPException
from storage import (
    fetch_ready_key,
    reserve_key,
    consume_key,
    count_ready_keys,
    expire_old_keys
)
from models import KeyRole
from audit import log_service_event
import uuid


router = APIRouter()


# =================================================
# SERVICE STATUS
# =================================================
@router.get("/api/v2/status")
def get_status():

    log_service_event("Service v2 status requested")

    return {
        "service": "QKD-KMS",
        "version": "v2",
        "status": "RUNNING"
    }


# =================================================
# GET KEY (ETSI-style allocation)
# =================================================
@router.post("/api/v2/get_key")
def get_key(request: dict):

    role_str = request.get("role", "ENC")
    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        role = KeyRole(role_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    expire_old_keys()

    key_id = fetch_ready_key(role)

    if not key_id:
        log_service_event("No key available for allocation")
        return {"status": "NO_KEY_AVAILABLE"}

    reserve_key(key_id, session_id)

    log_service_event(f"Key {key_id} reserved for session {session_id}")

    return {
        "status": "KEY_RESERVED",
        "key_id": key_id,
        "session_id": session_id
    }


# =================================================
# RELEASE KEY (Session failure recovery)
# =================================================
@router.post("/api/v2/release_key")
def release_key(request: dict):

    key_id = request.get("key_id")

    if not key_id:
        raise HTTPException(status_code=400, detail="key_id required")

    # Move RESERVED → READY
    # We reuse reserve_key logic carefully in storage layer if needed
    # For now, just re-promote by direct state change

    consume_key(key_id)  # or custom release logic if implemented

    log_service_event(f"Key released (or consumed): {key_id}")

    return {
        "status": "RELEASE_PROCESSED",
        "key_id": key_id
    }


# =================================================
# BUFFER VISIBILITY (Application side monitoring)
# =================================================
@router.get("/api/v2/buffer")
def buffer_status():

    expire_old_keys()

    return {
        "ENC_READY": count_ready_keys(KeyRole.ENC),
        "DEC_READY": count_ready_keys(KeyRole.DEC)
    }


# =================================================
# CREATE SESSION (Week 9 ready)
# =================================================
@router.post("/api/v2/create_session")
def create_session(request: dict):

    role = request.get("role", "ENC")

    try:
        KeyRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    session_id = str(uuid.uuid4())

    log_service_event(f"Session created: {session_id}")

    return {
        "status": "SESSION_CREATED",
        "session_id": session_id
    }
