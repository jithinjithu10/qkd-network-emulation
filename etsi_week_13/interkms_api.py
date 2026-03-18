"""
interkms_api.py

Inter-KMS Plane (Node-to-Node interface)

Used by remote QKD nodes to request keys.

Implements:
- POST /interkms/v1/request-key
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_ENABLED, NODE_SHARED_SECRET, NODE_ID

security = HTTPBearer()


# =================================================
# AUTHENTICATION FOR INTER-KMS
# =================================================

def verify_node_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    if not AUTH_ENABLED:
        return True

    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme"
        )

    if credentials.credentials != NODE_SHARED_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid node authentication token"
        )

    return True


# =================================================
# ROUTER FACTORY
# =================================================

def create_interkms_router(buffer, audit):

    router = APIRouter()

    # -------------------------------------------------
    # NODE REQUESTS KEY
    # -------------------------------------------------

    @router.post("/interkms/v1/request-key")
    def request_key(auth: bool = Depends(verify_node_token)):

        audit.api_call(
            "/interkms/v1/request-key",
            plane="INTER-KMS"
        )

        key = buffer.get_next_key()

        if not key:

            audit.error(
                "Inter-KMS key request failed: buffer empty",
                plane="INTER-KMS"
            )

            raise HTTPException(
                status_code=404,
                detail="No keys available"
            )

        audit.key_shared_with_node(
            key.key_id,
            remote_node="REMOTE_NODE"
        )

        return {
            "key_ID": key.key_id,
            "key": key.key_value,
            "size": key.key_size,
            "origin": NODE_ID
        }

    return router