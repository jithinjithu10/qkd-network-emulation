# etsi_api.py (FINAL CORRECT VERSION)

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

    if not credentials:
        raise HTTPException(status_code=401, detail="Missing credentials")

    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

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

        audit.api("/etsi/v2/status")

        stats = buffer.stats()

        return {
            "service": "ETSI-KMS",
            "status": "RUNNING",
            "mode": SYSTEM_MODE,
            "available_keys": stats.get("ready_keys", 0),
            "total_keys": stats.get("total_keys", 0),
            "sync_index": stats.get("sync_index", 0)
        }

    # -------------------------------------------------
    # GET NEXT KEY (NON-DESTRUCTIVE)
    # -------------------------------------------------
    @router.post("/etsi/v2/keys")
    def get_next_key(auth: bool = Depends(verify_token)):
        """
        Returns next key WITHOUT consuming it.
        Required for sender side encryption.
        """

        audit.api("/etsi/v2/keys")

        key = buffer.peek_next_key()   # IMPORTANT: must NOT remove

        if not key:
            audit.error("No keys available")
            raise HTTPException(status_code=404, detail="No keys available")

        audit.key_served(key.key_id)

        return {
            "key_id": key.key_id,
            "key": key.key_value,
            "size": key.key_size,
            "origin": key.origin_node
        }

    # -------------------------------------------------
    # GET KEY BY ID (SYNC / RECEIVER)
    # -------------------------------------------------
    @router.get("/etsi/v2/keys/{key_id}")
    def get_key_by_id(key_id: str, auth: bool = Depends(verify_token)):

        audit.api(f"/etsi/v2/keys/{key_id}")

        key = buffer.get_key_by_id(key_id)

        if not key:
            audit.error(f"Key not found: {key_id}")
            raise HTTPException(status_code=404, detail="Key not found")

        audit.key_served(key_id)

        return {
            "key_id": key.key_id,
            "key": key.key_value
        }

    return router