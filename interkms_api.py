"""
interkms_api.py

FINAL VERSION (SYNC + SESSION AWARE)

Supports:
- Key request
- Optional key_id request
- Sync validation
- Full audit trace
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_ENABLED, NODE_SHARED_SECRET, NODE_ID, SYSTEM_MODE

security = HTTPBearer()


# =================================================
# AUTHENTICATION
# =================================================

def verify_node_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    if not AUTH_ENABLED:
        return True

    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid scheme")

    if credentials.credentials != NODE_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token")

    return True


# =================================================
# ROUTER FACTORY
# =================================================

def create_interkms_router(buffer, audit):

    router = APIRouter()

    # -------------------------------------------------
    # REQUEST KEY FROM NODE
    # -------------------------------------------------

    @router.post("/interkms/v1/request-key")
    async def request_key(
        request: Request,
        auth: bool = Depends(verify_node_token)
    ):

        requester = request.headers.get("X-Node-ID", "UNKNOWN_NODE")

        audit.api_call("/interkms/v1/request-key", plane="INTER-KMS")
        audit.interkms_request(requester)

        body = {}
        try:
            body = await request.json()
        except:
            pass

        requested_key_id = body.get("key_id")

        # =================================================
        # CASE 1 → REQUEST SPECIFIC KEY (SYNC MODE)
        # =================================================

        if requested_key_id:

            for key in list(buffer._ready_queue):

                if key.key_id == requested_key_id:

                    buffer._ready_queue.remove(key)

                    key.consume()

                    audit.key_shared_with_node(key.key_id, requester)
                    audit.interkms_response(key.key_id, requester)

                    return {
                        "key_ID": key.key_id,
                        "key": key.key_value,
                        "origin": NODE_ID,
                        "mode": SYSTEM_MODE,
                        "served_to": requester
                    }

            audit.error(
                f"Requested key not found: {requested_key_id}",
                plane="INTER-KMS"
            )

            raise HTTPException(
                status_code=404,
                detail="Requested key not found"
            )

        # =================================================
        # CASE 2 → NORMAL REQUEST
        # =================================================

        key = buffer.get_next_key()

        if not key:

            audit.error(
                f"Inter-KMS request failed: buffer empty | requester={requester}",
                plane="INTER-KMS"
            )

            raise HTTPException(status_code=404, detail="No keys available")

        audit.key_shared_with_node(key.key_id, requester)
        audit.interkms_response(key.key_id, requester)

        return {
            "key_ID": key.key_id,
            "key": key.key_value,
            "origin": NODE_ID,
            "mode": SYSTEM_MODE,
            "served_to": requester
        }

    return router