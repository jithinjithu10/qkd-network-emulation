# interkms_api.py (FINAL PRODUCTION VERSION)

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_ENABLED, NODE_SHARED_SECRET, NODE_ID, SYSTEM_MODE
import hashlib

security = HTTPBearer()


# =================================================
# AUTHENTICATION (INTER-KMS)
# =================================================
def verify_node_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    if not AUTH_ENABLED:
        return True

    if not credentials:
        raise HTTPException(status_code=401, detail="Missing credentials")

    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    if credentials.credentials != NODE_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token")

    return True


# =================================================
# XOR HELPER
# =================================================
def xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


# =================================================
# ROUTER
# =================================================
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

        requester = request.headers.get("X-Node-ID")

        # Validate node identity
        if requester not in ["IITR", "IITJ"]:
            raise HTTPException(status_code=400, detail="Invalid node ID")

        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        requested_key_id = data.get("key_id")

        if requested_key_id is None:
            raise HTTPException(status_code=400, detail="key_id required")

        audit.api("/interkms/v1/request-key")
        audit.interkms_request(requester)

        # SAFE FETCH (NO CONSUMPTION)
        key = buffer.get_key_by_id(str(requested_key_id))

        if not key:
            audit.error(f"No key {requested_key_id} for {requester}", "INTER-KMS")
            raise HTTPException(status_code=404, detail="Key not available")

        key_id = key.key_id
        key_value = key.key_value

        # =================================================
        # CHAIN XOR ENCRYPTION
        # =================================================
        if int(key_id) == 0:
            enc_key = key_value
        else:
            prev_id = str(int(key_id) - 1)
            prev_key = buffer.get_key_by_id(prev_id)

            if prev_key:
                try:
                    enc_key = xor(
                        bytes.fromhex(key_value),
                        bytes.fromhex(prev_key.key_value)
                    ).hex()
                except Exception as e:
                    audit.error(f"XOR failed for key {key_id}: {str(e)}")
                    enc_key = key_value
            else:
                audit.error(f"Previous key missing for XOR: {prev_id}")
                enc_key = key_value

        # Correct hash (bytes, not string)
        key_hash = hashlib.sha256(bytes.fromhex(key_value)).hexdigest()

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
    # ACK ENDPOINT
    # -------------------------------------------------
    @router.post("/interkms/v1/ack")
    async def receive_ack(
        request: Request,
        auth: bool = Depends(verify_node_token)
    ):

        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        key_id = data.get("key_id")
        node = data.get("node")

        if not key_id or not node:
            raise HTTPException(status_code=400, detail="Invalid ACK data")

        ack_manager.add_ack(key_id, node)

        audit.log("ACK_RECEIVED", f"{key_id} from {node}", "SYNC")

        if ack_manager.is_complete(key_id):

            audit.log(
                "ACK_COMPLETE",
                f"Key {key_id} confirmed by IITR & IITJ",
                "SYNC"
            )

            ack_manager.remove(key_id)

        return {"status": "ack_received"}

    return router