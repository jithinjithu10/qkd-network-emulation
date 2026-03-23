"""
etsi_api.py (UPDATED - RESEARCH LEVEL)

Fixes:
- Removed session abstraction
- Pure key_id-based access
- ETSI-aligned endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_ENABLED, AUTH_TOKEN, SYSTEM_MODE

security = HTTPBearer()


# =================================================
# AUTH
# =================================================

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    if not AUTH_ENABLED:
        return True

    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid scheme")

    if credentials.credentials != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    return True


# =================================================
# ROUTER
# =================================================

def create_etsi_router(buffer, audit):

    router = APIRouter()

    # -------------------------------------------------
    # STATUS
    # -------------------------------------------------

    @router.get("/etsi/v2/status")
    def status(auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/status", "APPLICATION")

        stats = buffer.stats()

        return {
            "service": "ETSI-KMS",
            "status": "RUNNING",
            "mode": SYSTEM_MODE,
            "available_keys": stats["ready_keys"],
            "sync_index": stats.get("sync_index", 0)
        }

    # -------------------------------------------------
    # GET NEW KEY
    # -------------------------------------------------

    @router.post("/etsi/v2/keys")
    def get_key(auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/keys", "APPLICATION")

        key = buffer.get_next_key()

        if not key:
            audit.error("No keys available", "APPLICATION")
            raise HTTPException(status_code=404, detail="No keys available")

        audit.key_served(key.key_id)

        return {
            "key_id": key.key_id,
            "key": key.key_value,
            "size": key.key_size,
            "origin": key.origin_node
        }

    # -------------------------------------------------
    # GET KEY BY ID (VERY IMPORTANT)
    # -------------------------------------------------

    @router.get("/etsi/v2/keys/{key_id}")
    def get_key_by_id(key_id: str, auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/keys/{id}", "APPLICATION")

        key = buffer.get_key_by_id(key_id)

        if not key:
            raise HTTPException(status_code=404, detail="Key not found")

        return {
            "key_id": key.key_id,
            "key": key.key_value
        }

    return router