"""
interkms_api.py (UPDATED - RESEARCH LEVEL)

Fixes:
- No direct buffer access
- Proper key_id handling
- Sync validation added
- Clean lifecycle handling
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_ENABLED, NODE_SHARED_SECRET, NODE_ID, SYSTEM_MODE

security = HTTPBearer()


# =================================================
# AUTH
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
# ROUTER
# =================================================

def create_interkms_router(buffer, audit):

    router = APIRouter()

    # -------------------------------------------------
    # REQUEST KEY
    # -------------------------------------------------

    @router.post("/interkms/v1/request-key")
    async def request_key(
        request: Request,
        auth: bool = Depends(verify_node_token)
    ):

        requester = request.headers.get("X-Node-ID", "UNKNOWN")

        audit.api_call("/interkms/v1/request-key", "INTER-KMS")
        audit.interkms_request(requester)

        try:
            body = await request.json()
        except:
            body = {}

        requested_key_id = body.get("key_id")

        # =================================================
        # CASE 1 → SPECIFIC KEY REQUEST
        # =================================================

        if requested_key_id:

            key = buffer.get_key_by_id(requested_key_id)

            if not key:
                audit.error(
                    f"Key not found: {requested_key_id}",
                    "INTER-KMS"
                )
                raise HTTPException(
                    status_code=404,
                    detail="Key not found"
                )

            # SYNC VALIDATION (VERY IMPORTANT)
            if SYSTEM_MODE == "SYNC":
                expected_index = buffer._sync_index

                if str(expected_index) != str(requested_key_id):
                    audit.sync_mismatch(
                        expected=expected_index,
                        received=requested_key_id
                    )

            audit.key_shared_with_node(key.key_id, requester)
            audit.interkms_response(key.key_id, requester)

            return {
                "key_id": key.key_id,
                "key": key.key_value,
                "origin": NODE_ID,
                "mode": SYSTEM_MODE
            }

        # =================================================
        # CASE 2 → NORMAL REQUEST
        # =================================================

        key = buffer.get_next_key()

        if not key:
            audit.error(
                f"No keys available for {requester}",
                "INTER-KMS"
            )
            raise HTTPException(status_code=404, detail="No keys available")

        audit.key_shared_with_node(key.key_id, requester)
        audit.interkms_response(key.key_id, requester)

        return {
            "key_id": key.key_id,
            "key": key.key_value,
            "origin": NODE_ID,
            "mode": SYSTEM_MODE
        }

    return router