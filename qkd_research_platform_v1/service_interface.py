"""
service_interface.py
---------------------

Research-Grade ETSI Service Interface (v2)
Session-Aware | Policy-Aware | Quantum-Aware | Metrics Ready
Weeks 8–12 Advanced Integration
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import time
import uuid

from storage import (
    fetch_and_reserve,
    consume_key,
    count_ready_keys,
    expire_old_keys
)

from models import KeyRole
from audit import log_service_event
from policy import PolicyEngine
from session_manager import SessionManager

# =================================================
# INITIALIZE LAYERS
# =================================================

router = APIRouter()

policy_engine = PolicyEngine()
session_manager = SessionManager()


# =================================================
# SERVICE STATUS
# =================================================
@router.get("/api/v2/status")
def get_status():

    log_service_event("Service v2 status requested")

    return {
        "service": "QKD-KMS",
        "version": "v2-research",
        "status": "RUNNING",
        "policy_mode": policy_engine.mode
    }


# =================================================
# CREATE SESSION
# =================================================
@router.post("/api/v2/create_session")
def create_session(request: dict):

    app_id = request.get("app_id", "DEFAULT_APP")
    role = request.get("role", "ENC")
    node_id = request.get("node_id", "IITR")

    try:
        session_id = session_manager.create_session(app_id, role, node_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    log_service_event(f"Session created: {session_id}")

    return {
        "status": "SESSION_CREATED",
        "session_id": session_id
    }


# =================================================
# GET KEY (Session + Policy Aware)
# =================================================
@router.post("/api/v2/get_key")
def get_key(request: dict):

    session_id = request.get("session_id")
    role_str = request.get("role", "ENC")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    if not session_manager.validate_session(session_id):
        raise HTTPException(status_code=403, detail="Invalid or expired session")

    try:
        role = KeyRole(role_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    expire_old_keys()

    start_time = time.time()

    key_id = fetch_and_reserve(role, session_id)

    latency = time.time() - start_time

    if not key_id:
        session_manager.record_failed_allocation(session_id)
        policy_engine.record_failed_allocation()

        log_service_event("Allocation failed – no key available")

        return {
            "status": "NO_KEY_AVAILABLE",
            "allocation_latency_sec": latency
        }

    # Successful allocation
    session_manager.record_key_usage(session_id)
    policy_engine.record_node_allocation("LOCAL")

    log_service_event(f"Key {key_id} reserved for session {session_id}")

    return {
        "status": "KEY_RESERVED",
        "key_id": key_id,
        "session_id": session_id,
        "allocation_latency_sec": latency
    }


# =================================================
# CONSUME KEY
# =================================================
@router.post("/api/v2/consume_key")
def consume_reserved_key(request: dict):

    key_id = request.get("key_id")
    session_id = request.get("session_id")

    if not key_id:
        raise HTTPException(status_code=400, detail="key_id required")

    if not session_manager.validate_session(session_id):
        raise HTTPException(status_code=403, detail="Invalid session")

    consume_key(key_id)

    log_service_event(f"Key consumed: {key_id}")

    return {
        "status": "KEY_CONSUMED",
        "key_id": key_id
    }


# =================================================
# RELEASE KEY (True Release)
# =================================================
@router.post("/api/v2/release_key")
def release_key(request: dict):

    key_id = request.get("key_id")

    if not key_id:
        raise HTTPException(status_code=400, detail="key_id required")

    # In research-grade design, release logic would:
    # RESERVED → READY
    # For now, we mark consumed to avoid reuse risk

    consume_key(key_id)

    log_service_event(f"Key released (marked consumed): {key_id}")

    return {
        "status": "KEY_RELEASE_PROCESSED",
        "key_id": key_id
    }


# =================================================
# BUFFER VISIBILITY
# =================================================
@router.get("/api/v2/buffer")
def buffer_status():

    expire_old_keys()

    return {
        "ENC_READY": count_ready_keys(KeyRole.ENC),
        "DEC_READY": count_ready_keys(KeyRole.DEC),
        "timestamp": datetime.utcnow().isoformat()
    }


# =================================================
# SESSION METRICS
# =================================================
@router.get("/api/v2/session_metrics")
def session_metrics():

    return session_manager.export_metrics()