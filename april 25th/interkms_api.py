# interkms_api.py
# Purpose:
# Handles inter-KMS communication between IITR and IITJ:
# - Key synchronization
# - Secure key transfer
# - ACK tracking for consistency
#
# NOTE:
# No direct IP changes here.
# Uses PEER_NODES from config.py.
# Ensure NODE_SHARED_SECRET matches on both nodes.


from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_ENABLED, NODE_SHARED_SECRET, NODE_ID, SYSTEM_MODE
import hashlib


security = HTTPBearer()


# =================================================
# AUTHENTICATION (INTER-KMS)
# =================================================
def verify_node_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifies node-to-node authentication using shared secret.
    """

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
# XOR HELPER (FOR KEY OBFUSCATION)
# =================================================
def xor(a: bytes, b: bytes) -> bytes:
    """
    Simple XOR operation.
    Used for obfuscating key using previous key.
    """
    return bytes(x ^ y for x, y in zip(a, b))


# =================================================
# ROUTER FACTORY
# =================================================
def create_interkms_router(buffer, audit, ack_manager):

    router = APIRouter()

    # -------------------------------------------------
    # REQUEST KEY FROM PEER
    # -------------------------------------------------
    @router.post("/interkms/v1/request-key")
    async def request_key(
        request: Request,
        auth: bool = Depends(verify_node_token)
    ):
        """
        Provides next key or specific key_id to peer node.
        """

        requester = request.headers.get("X-Node-ID", "UNKNOWN")

        audit.api("/interkms/v1/request-key")
        audit.interkms_request(requester)

        # Safe JSON parsing
        try:
            body = await request.json()
        except Exception:
            body = {}

        requested_key_id = body.get("key_id")

        # =================================================
        # FETCH KEY
        # =================================================
        if requested_key_id is not None:
            key = buffer.get_key_by_id(str(requested_key_id))
        else:
            key = buffer.get_next_key()

        if not key:
            audit.error(f"No key available for {requester}", plane="INTER-KMS")
            raise HTTPException(status_code=404, detail="No key available")

        key_id = key.key_id
        key_value = key.key_value

        # =================================================
        # SECURE TRANSFER (XOR WITH PREVIOUS KEY)
        # =================================================
        try:
            prev_id = str(int(key_id) - 1)
        except ValueError:
            prev_id = None

        prev_key = buffer.get_key_by_id(prev_id) if prev_id else None

        if prev_key:
            try:
                enc_key = xor(
                    bytes.fromhex(key_value),
                    bytes.fromhex(prev_key.key_value)
                ).hex()
            except Exception:
                # fallback if XOR fails
                enc_key = key_value
        else:
            # first key (genesis case)
            enc_key = key_value

        # Hash for verification
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
    # ACK ENDPOINT
    # -------------------------------------------------
    @router.post("/interkms/v1/ack")
    async def receive_ack(
        request: Request,
        auth: bool = Depends(verify_node_token)
    ):
        """
        Receives acknowledgment for key usage.
        Ensures both IITR and IITJ confirm usage.
        """

        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        key_id = data.get("key_id")
        node = data.get("node")

        if not key_id or not node:
            raise HTTPException(status_code=400, detail="Invalid ACK data")

        # Store ACK
        ack_manager.add_ack(key_id, node)

        audit.log("ACK_RECEIVED", f"{key_id} from {node}", "SYNC")

        # Check completion
        if ack_manager.is_complete(key_id):

            audit.log(
                "ACK_COMPLETE",
                f"Key {key_id} confirmed by IITR & IITJ",
                "SYNC"
            )

            # Cleanup to avoid memory growth
            ack_manager.remove(key_id)

        return {"status": "ack_received"}

    return router