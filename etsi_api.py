"""
etsi_api.py

Strict ETSI-aligned Service Interface
with Bearer Token Authentication.

Implements:
- GET /etsi/v1/status
- POST /etsi/v1/open_session
- POST /etsi/v1/reserve
- POST /etsi/v1/get_key
- POST /etsi/v1/consume
- POST /etsi/v1/close_session
"""

from fastapi import APIRouter, HTTPException, Header
from buffers import QBuffer
from session_manager import SessionManager
from audit import AuditLogger
from models import Key
from config import (
    KEY_SIZE,
    DEFAULT_TTL_SECONDS,
    SESSION_TIMEOUT_SECONDS,
    INITIAL_KEY_POOL_SIZE,
    AUTH_ENABLED,
    AUTH_TOKEN
)
import uuid
import secrets


# =================================================
# INITIALIZATION
# =================================================

router = APIRouter()

buffer = QBuffer()
session_manager = SessionManager(SESSION_TIMEOUT_SECONDS)
audit = AuditLogger()


# =================================================
# AUTHENTICATION CHECK
# =================================================

def _validate_auth(authorization: str | None):

    if not AUTH_ENABLED:
        return

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.split(" ")[1]

    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication token")


# =================================================
# INTERNAL KEY GENERATION (PRELOAD)
# =================================================

def _preload_keys():

    for _ in range(INITIAL_KEY_POOL_SIZE):
        key_id = str(uuid.uuid4())
        key_value = secrets.token_bytes(KEY_SIZE // 8).hex()
        key = Key(key_id, key_value, KEY_SIZE, DEFAULT_TTL_SECONDS)
        buffer.add_key(key)
        audit.key_added(key_id)


_preload_keys()


# =================================================
# STATUS
# =================================================

@router.get("/etsi/v1/status")
def status(authorization: str | None = Header(default=None)):

    _validate_auth(authorization)

    return {
        "service": "ETSI-KMS",
        "status": "RUNNING"
    }


# =================================================
# OPEN SESSION
# =================================================

@router.post("/etsi/v1/open_session")
def open_session(authorization: str | None = Header(default=None)):

    _validate_auth(authorization)

    session_id = session_manager.create_session()
    audit.session_created(session_id)

    return {
        "session_id": session_id
    }


# =================================================
# RESERVE KEY
# =================================================

@router.post("/etsi/v1/reserve")
def reserve(request: dict, authorization: str | None = Header(default=None)):

    _validate_auth(authorization)

    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        session_manager.validate_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    key = buffer.reserve_key(session_id)

    if not key:
        return {"status": "NO_KEY_AVAILABLE"}

    audit.key_reserved(key.key_id, session_id)

    return {
        "status": "RESERVED",
        "key_id": key.key_id
    }


# =================================================
# GET KEY MATERIAL
# =================================================

@router.post("/etsi/v1/get_key")
def get_key(request: dict, authorization: str | None = Header(default=None)):

    _validate_auth(authorization)

    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        session_manager.validate_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    key = buffer.get_reserved_key(session_id)

    if not key:
        raise HTTPException(status_code=404, detail="No reserved key")

    return {
        "key_id": key.key_id,
        "key_value": key.key_value,
        "key_size": key.key_size
    }


# =================================================
# CONSUME KEY
# =================================================

@router.post("/etsi/v1/consume")
def consume(request: dict, authorization: str | None = Header(default=None)):

    _validate_auth(authorization)

    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        session_manager.validate_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    key = buffer.consume_key(session_id)

    if not key:
        raise HTTPException(status_code=404, detail="No reserved key")

    audit.key_consumed(key.key_id)

    return {
        "status": "CONSUMED",
        "key_id": key.key_id
    }


# =================================================
# CLOSE SESSION
# =================================================

@router.post("/etsi/v1/close_session")
def close_session(request: dict, authorization: str | None = Header(default=None)):

    _validate_auth(authorization)

    session_id = request.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        session_manager.close_session(session_id)
        buffer.release_key(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    audit.session_closed(session_id)

    return {
        "status": "SESSION_CLOSED"
    }