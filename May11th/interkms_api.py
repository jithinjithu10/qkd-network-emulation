# interkms_api.py
# DISTRIBUTED HYBRID QUANTUM-CLASSICAL INTER-KMS API

from datetime import datetime
import hashlib

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

from config import (

    AUTH_ENABLED,

    NODE_SHARED_SECRET,

    NODE_ID,

    SYSTEM_MODE,

    QKD_PROTOCOL,

    ENABLE_SHA256_SYNC,

    ENABLE_METADATA_SYNC
)


# =========================================================
# SECURITY
# =========================================================

security = HTTPBearer()


# =========================================================
# INTER-KMS AUTHENTICATION
# =========================================================

def verify_node_token(

    credentials:
    HTTPAuthorizationCredentials = Depends(security)

):

    """
    Authentication for:
    - inter-KMS synchronization
    - metadata exchange
    - distributed verification

    Used ONLY on:
    Public Classical Channel
    """

    if not AUTH_ENABLED:
        return True

    if not credentials:

        raise HTTPException(

            status_code=401,

            detail="Missing credentials"
        )

    if credentials.scheme != "Bearer":

        raise HTTPException(

            status_code=401,

            detail="Invalid auth scheme"
        )

    if credentials.credentials != NODE_SHARED_SECRET:

        raise HTTPException(

            status_code=401,

            detail="Invalid node token"
        )

    return True


# =========================================================
# SHA-256
# =========================================================

def sha256_hash(
    key_material: str
):

    return hashlib.sha256(

        bytes.fromhex(key_material)

    ).hexdigest()


# =========================================================
# ROUTER FACTORY
# =========================================================

def create_interkms_router(

    buffer,

    audit,

    ack_manager
):

    router = APIRouter()

    # =====================================================
    # REQUEST KEY METADATA
    # =====================================================

    @router.post("/interkms/v1/request-key")
    async def request_key(

        request: Request,

        auth: bool = Depends(
            verify_node_token
        )
    ):

        """
        Metadata synchronization endpoint.

        Public classical channel exchanges:
        - metadata
        - synchronization state
        - SHA-256 hashes

        NEVER:
        - raw quantum keys
        """

        requester = request.headers.get(
            "X-Node-ID"
        )

        # -------------------------------------------------
        # VALIDATE REQUESTER
        # -------------------------------------------------

        trusted_nodes = [
            "IITR",
            "IITJ"
        ]

        if requester not in trusted_nodes:

            raise HTTPException(

                status_code=400,

                detail="Invalid node ID"
            )

        # -------------------------------------------------
        # PARSE REQUEST
        # -------------------------------------------------

        try:

            data = await request.json()

        except Exception:

            raise HTTPException(

                status_code=400,

                detail="Invalid JSON"
            )

        requested_key_id = data.get(
            "key_id"
        )

        if requested_key_id is None:

            raise HTTPException(

                status_code=400,

                detail="key_id required"
            )

        # -------------------------------------------------
        # AUDIT
        # -------------------------------------------------

        audit.api(
            "/interkms/v1/request-key"
        )

        audit.interkms_request(
            requester
        )

        # -------------------------------------------------
        # FETCH LOCAL KEY
        # -------------------------------------------------

        key = buffer.get_key_by_id(
            str(requested_key_id)
        )

        if not key:

            audit.error(

                (
                    f"Missing synchronized key "
                    f"{requested_key_id}"
                ),

                "INTER-KMS"
            )

            raise HTTPException(

                status_code=404,

                detail="Key unavailable"
            )

        # -------------------------------------------------
        # FETCH METADATA
        # -------------------------------------------------

        metadata = buffer.get_metadata(
            requested_key_id
        )

        if not metadata:

            raise HTTPException(

                status_code=404,

                detail="Metadata unavailable"
            )

        # -------------------------------------------------
        # HASH
        # -------------------------------------------------

        key_hash = sha256_hash(
            key.key_value
        )

        # -------------------------------------------------
        # ACK TRACKING
        # -------------------------------------------------

        ack_manager.create_entry(

            key_id=key.key_id,

            session_id=metadata.get(
                "session_id",
                "UNKNOWN"
            ),

            sync_index=metadata.get(
                "sync_index",
                0
            )
        )

        # -------------------------------------------------
        # AUDIT
        # -------------------------------------------------

        audit.metadata_shared(

            key.key_id,

            requester
        )

        audit.interkms_response(

            key.key_id,

            requester
        )

        # =================================================
        # RESPONSE
        # =================================================

        response = {

            # ---------------------------------------------
            # KEY IDENTITY
            # ---------------------------------------------
            "key_id":
                key.key_id,

            # ---------------------------------------------
            # SESSION
            # ---------------------------------------------
            "session_id":
                metadata.get(
                    "session_id"
                ),

            "sync_index":
                metadata.get(
                    "sync_index"
                ),

            # ---------------------------------------------
            # QKD
            # ---------------------------------------------
            "protocol":
                QKD_PROTOCOL,

            "mode":
                SYSTEM_MODE,

            # ---------------------------------------------
            # NODE INFO
            # ---------------------------------------------
            "origin":
                NODE_ID,

            "timestamp":
                datetime.utcnow().isoformat(),

            # ---------------------------------------------
            # HASH
            # ---------------------------------------------
            "key_hash":
                key_hash,

            # ---------------------------------------------
            # VERIFICATION
            # ---------------------------------------------
            "verified":
                metadata.get(
                    "verified",
                    False
                )
        }

        # =================================================
        # OPTIONAL DEMO MODE
        # =================================================
        # NEVER use in real QKD deployments
        # =================================================

        if not ENABLE_METADATA_SYNC:

            response["key"] = (
                key.key_value
            )

        return response

    # =====================================================
    # VERIFY SYNCHRONIZATION
    # =====================================================

    @router.post("/interkms/v1/verify")
    async def verify_synchronization(

        request: Request,

        auth: bool = Depends(
            verify_node_token
        )
    ):

        """
        Verify synchronization integrity.

        SHA-256(K_IITR)
            ==
        SHA-256(K_IITJ)

        WITHOUT key transport.
        """

        try:

            data = await request.json()

        except Exception:

            raise HTTPException(

                status_code=400,

                detail="Invalid JSON"
            )

        key_id = data.get("key_id")

        node = data.get("node")

        key_hash = data.get("key_hash")

        if (

            not key_id
            or not node
            or not key_hash

        ):

            raise HTTPException(

                status_code=400,

                detail=
                    "Incomplete verification payload"
            )

        # -------------------------------------------------
        # VERIFY
        # -------------------------------------------------

        verified = buffer.verify_key_hash(

            key_id,

            key_hash
        )

        # -------------------------------------------------
        # ACK
        # -------------------------------------------------

        ack_manager.add_ack(

            key_id=key_id,

            node=node,

            key_hash=key_hash
        )

        # -------------------------------------------------
        # AUDIT
        # -------------------------------------------------

        audit.hash_verification(
            key_id,
            verified
        )

        if verified:

            audit.sync_success(
                key_id
            )

        else:

            audit.sync_fail(
                key_id
            )

        # -------------------------------------------------
        # COMPLETE?
        # -------------------------------------------------

        if ack_manager.is_complete(
            key_id
        ):

            if ack_manager.is_verified(
                key_id
            ):

                audit.synchronization_complete(
                    key_id
                )

            ack_manager.remove(
                key_id
            )

        return {

            "key_id":
                key_id,

            "verified":
                verified
        }

    # =====================================================
    # LEGACY ACK
    # =====================================================

    @router.post("/interkms/v1/ack")
    async def receive_ack(

        request: Request,

        auth: bool = Depends(
            verify_node_token
        )
    ):

        """
        Backward-compatible ACK endpoint.

        Supports:
        - synchronization tracking
        - distributed verification
        - replay-safe orchestration
        """

        try:

            data = await request.json()

        except Exception:

            raise HTTPException(

                status_code=400,

                detail="Invalid JSON"
            )

        key_id = data.get("key_id")

        node = data.get("node")

        key_hash = data.get("key_hash")

        if not key_id or not node:

            raise HTTPException(

                status_code=400,

                detail="Invalid ACK data"
            )

        # -------------------------------------------------
        # STORE ACK
        # -------------------------------------------------

        ack_manager.add_ack(

            key_id=key_id,

            node=node,

            key_hash=(
                key_hash
                if key_hash
                else "UNKNOWN"
            )
        )

        # -------------------------------------------------
        # AUDIT
        # -------------------------------------------------

        audit.log(

            "ACK_RECEIVED",

            f"{key_id} from {node}",

            "SYNC"
        )

        # -------------------------------------------------
        # COMPLETE?
        # -------------------------------------------------

        if ack_manager.is_complete(
            key_id
        ):

            if ack_manager.is_verified(
                key_id
            ):

                audit.log(

                    "ACK_COMPLETE",

                    (
                        f"Key {key_id} "
                        f"verified at IITR & IITJ"
                    ),

                    "SYNC"
                )

            else:

                audit.log(

                    "ACK_HASH_MISMATCH",

                    (
                        f"Key {key_id} "
                        f"verification failed"
                    ),

                    "SYNC"
                )

            ack_manager.remove(
                key_id
            )

        return {

            "status":
                "ack_received"
        }

    return router