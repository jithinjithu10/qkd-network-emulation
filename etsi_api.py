"""
etsi_api.py

ETSI v2 Service Interface (Application Plane)

Implements:
- GET  /etsi/v2/status
- POST /etsi/v2/keys
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import (
    KEY_SIZE,
    DEFAULT_TTL_SECONDS,
    INITIAL_KEY_POOL_SIZE,
    AUTH_ENABLED,
    AUTH_TOKEN
)
from models import Key
import uuid
import secrets


security = HTTPBearer()


# =================================================
# AUTHENTICATION
# =================================================

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    if not AUTH_ENABLED:
        return True

    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    if credentials.credentials != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return True


# =================================================
# ROUTER FACTORY (IMPORTANT)
# =================================================

def create_etsi_router(buffer, audit):

    router = APIRouter()

    # -------------------------------------------------
    # PRELOAD KEYS (Only Once Per Node)
    # -------------------------------------------------

    for _ in range(INITIAL_KEY_POOL_SIZE):
        key_id = str(uuid.uuid4())
        key_value = secrets.token_bytes(KEY_SIZE // 8).hex()
        key = Key(key_id, key_value, KEY_SIZE, DEFAULT_TTL_SECONDS)
        buffer.add_key(key)
        audit.key_added(key_id)

    # -------------------------------------------------
    # STATUS
    # -------------------------------------------------

    @router.get("/etsi/v2/status")
    def status(auth: bool = Depends(verify_token)):

        return {
            "service": "ETSI-KMS",
            "version": "v2",
            "status": "RUNNING",
            "available_keys": buffer.stats()["ready_keys"]
        }

    # -------------------------------------------------
    # ATOMIC KEY DELIVERY
    # -------------------------------------------------

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

    return router