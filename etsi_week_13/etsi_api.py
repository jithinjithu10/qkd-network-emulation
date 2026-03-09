"""
etsi_api.py

ETSI v2 Service Interface (Application Plane)

Implements:
- GET  /etsi/v2/status
- POST /etsi/v2/keys

Features:
- ETSI-style atomic key delivery
- Bearer token authentication
- Audit logging
- Router factory for dependency injection
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_ENABLED, AUTH_TOKEN

security = HTTPBearer()


# =================================================
# AUTHENTICATION
# =================================================

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    if not AUTH_ENABLED:
        return True

    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme"
        )

    if credentials.credentials != AUTH_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    return True


# =================================================
# ROUTER FACTORY
# =================================================

def create_etsi_router(buffer, audit):

    router = APIRouter()

    # -------------------------------------------------
    # ETSI STATUS ENDPOINT
    # -------------------------------------------------

    @router.get("/etsi/v2/status")
    def status(auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/status", plane="APPLICATION")

        stats = buffer.stats()

        return {
            "service": "ETSI-KMS",
            "version": "v2",
            "status": "RUNNING",
            "available_keys": stats["ready_keys"]
        }

    # -------------------------------------------------
    # ETSI KEY RETRIEVAL
    # -------------------------------------------------

    @router.post("/etsi/v2/keys")
    def get_key(auth: bool = Depends(verify_token)):

        audit.api_call("/etsi/v2/keys", plane="APPLICATION")

        key = buffer.get_next_key()

        if not key:

            audit.error(
                "Key request failed: buffer empty",
                plane="APPLICATION"
            )

            raise HTTPException(
                status_code=404,
                detail="No keys available"
            )

        return {
            "key_ID": key.key_id,
            "key": key.key_value,
            "size": key.key_size
        }

    return router