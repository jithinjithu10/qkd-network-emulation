"""
etsi_api.py

FINAL VERSION (SESSION-AWARE ETSI API)

Supports:
- Key fetch
- Session-based reservation
- Reserved key retrieval
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_ENABLED, AUTH_TOKEN, SYSTEM_MODE

security = HTTPBearer()


# =================================================
# AUTHENTICATION
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
# ROUTER FACTORY
# =================================================

def create_etsi_router(buffer, audit):

    router = APIRouter()

    # -------------------------------------------------
    # STATUS
    # -------------------------------------------------

    @router.get("/etsi/v2/status")
    def status(auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/status", plane="APPLICATION")

        stats = buffer.stats()

        return {
            "service": "ETSI-KMS",
            "version": "v2",
            "status": "RUNNING",
            "system_mode": SYSTEM_MODE,
            "available_keys": stats["ready_keys"],
            "reserved_keys": stats.get("reserved_keys", 0),
            "sync_index": stats.get("sync_index", 0)
        }

    # -------------------------------------------------
    # KEY FETCH (DIRECT)
    # -------------------------------------------------

    @router.post("/etsi/v2/keys")
    def get_key(auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/keys", plane="APPLICATION")

        key = buffer.get_next_key()

        if not key:
            audit.error("Key request failed: buffer empty", "APPLICATION")
            raise HTTPException(status_code=404, detail="No keys available")

        audit.key_served(key.key_id)

        return {
            "key_ID": key.key_id,
            "key": key.key_value,
            "size": key.key_size,
            "origin": key.origin_node,
            "mode": SYSTEM_MODE
        }

    # -------------------------------------------------
    # SESSION-BASED RESERVATION (NEW)
    # -------------------------------------------------

    @router.post("/etsi/v2/reserve")
    def reserve_key(session_id: str, auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/reserve", plane="APPLICATION")

        key = buffer.reserve_key(session_id)

        if not key:
            audit.error("Reservation failed: no key", "APPLICATION")
            raise HTTPException(status_code=404, detail="No keys available")

        #  log session mapping
        audit.session_key_mapping(session_id, key.key_id)

        return {
            "session_id": session_id,
            "key_ID": key.key_id,
            "origin": key.origin_node
        }

    # -------------------------------------------------
    #  GET RESERVED KEY (NEW)
    # -------------------------------------------------

    @router.get("/etsi/v2/reserved/{session_id}")
    def get_reserved(session_id: str, auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/reserved", plane="APPLICATION")

        key = buffer.get_reserved_key(session_id)

        if not key:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "key_ID": key.key_id,
            "key": key.key_value
        }

    # -------------------------------------------------
    #  CONSUME RESERVED KEY (NEW)
    # -------------------------------------------------

    @router.post("/etsi/v2/consume/{session_id}")
    def consume_reserved(session_id: str, auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/consume", plane="APPLICATION")

        key = buffer.consume_key(session_id)

        if not key:
            raise HTTPException(status_code=404, detail="Session not found")

        audit.key_consumed(key.key_id)

        return {
            "session_id": session_id,
            "key_ID": key.key_id,
            "status": "CONSUMED"
        }

    return router