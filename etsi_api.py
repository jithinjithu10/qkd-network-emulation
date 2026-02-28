"""
etsi_api.py

Hybrid ETSI v2 Service Interface
External interface strictly ETSI-style.

Implements:
- GET  /etsi/v2/status
- POST /etsi/v2/keys  (atomic key retrieval)

Internal session logic remains hidden.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from buffers import QBuffer
from audit import AuditLogger
from models import Key
from config import (
    KEY_SIZE,
    DEFAULT_TTL_SECONDS,
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
audit = AuditLogger()

security = HTTPBearer()


# =================================================
# AUTHENTICATION
# =================================================

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    if not AUTH_ENABLED:
        return True

    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    if credentials.credentials != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return True


# =================================================
# PRELOAD KEY POOL
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

@router.get("/etsi/v2/status")
def status(auth: bool = Depends(verify_token)):

    return {
        "service": "ETSI-KMS",
        "version": "v2",
        "status": "RUNNING",
        "available_keys": buffer.stats()["ready_keys"]
    }


# =================================================
# ETSI v2 ATOMIC KEY DELIVERY
# =================================================

@router.post("/etsi/v2/keys")
def get_key(auth: bool = Depends(verify_token)):

    key = buffer.get_next_key()

    if not key:
        raise HTTPException(status_code=404, detail="No keys available")

    audit.key_consumed(key.key_id)

    return {
        "key_ID": key.key_id,
        "key": key.key_value,
        "size": key.key_size
    }