# interkms_api.py (FINAL - SECURE SYNC + ACK)

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_ENABLED, NODE_SHARED_SECRET, NODE_ID, SYSTEM_MODE
import hashlib

security = HTTPBearer()


# =================================================
# AUTH
# =================================================

def verify_node_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    if not AUTH_ENABLED:
        return True

    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid scheme")

    if credentials.credentials != NODE_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token")

    return True


# =================================================
# SIMPLE XOR
# =================================================

def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


# =================================================
# ROUTER
# =================================================

#  UPDATED SIGNATURE
def create_interkms_router(buffer, audit, ack_manager):

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

        audit.api("/interkms/v1/request-key")
        audit.interkms_request(requester)

        try:
            body = await request.json()
        except:
            body = {}

        requested_key_id = body.get("key_id")

        # =================================================
        # GET KEY
        # =================================================

        if requested_key_id:
            key = buffer.get_key_by_id(requested_key_id)
        else:
            key = buffer.get_next_key()

        if not key:
            audit.error(f"No key available for {requester}")
            raise HTTPException(status_code=404, detail="No key available")

        # =================================================
        # SECURE TRANSFER
        # =================================================

        key_id = key.key_id
        key_value = key.key_value

        prev_id = str(int(key_id) - 1)
        prev_key = buffer.get_key_by_id(prev_id)

        if prev_key:
            enc_key = xor(
                bytes.fromhex(key_value),
                bytes.fromhex(prev_key.key_value)
            ).hex()
        else:
            enc_key = key_value

        key_hash = hashlib.sha256(key_value.encode()).hexdigest()

        # =================================================
        # LOGGING
        # =================================================

        audit.key_shared_with_node(key_id, requester)
        audit.interkms_response(key_id, requester)

        return {
            "key_id": key_id,
            "enc_key": enc_key,
            "hash": key_hash,
            "origin": NODE_ID,
            "mode": SYSTEM_MODE
        }

    # -------------------------------------------------
    # ACK ENDPOINT (NEW)
    # -------------------------------------------------

    @router.post("/interkms/v1/ack")
    async def receive_ack(
        request: Request,
        auth: bool = Depends(verify_node_token)
    ):

        try:
            data = await request.json()
        except:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        key_id = data.get("key_id")
        node = data.get("node")

        if not key_id or not node:
            raise HTTPException(status_code=400, detail="Invalid ACK data")

        # store ACK
        ack_manager.add_ack(key_id, node)

        audit.log("ACK_RECEIVED", f"{key_id} from {node}", "SYNC")

        # check if both nodes acknowledged
        if ack_manager.is_complete(key_id):

            audit.log(
                "ACK_COMPLETE",
                f"Key {key_id} confirmed by IITR & IITJ",
                "SYNC"
            )

            # optional cleanup
            ack_manager.remove(key_id)

        return {"status": "ack_received"}

    return router