# etsi_api.py
# HYBRID QUANTUM-CLASSICAL ETSI-QKD API

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

from config import (

    AUTH_ENABLED,
    AUTH_TOKEN,

    SYSTEM_MODE,
    QKD_PROTOCOL,

    ENABLE_SHA256_SYNC,
    ENABLE_METADATA_SYNC,

    NODE_ID
)


# =========================================================
# SECURITY
# =========================================================

security = HTTPBearer()


# =========================================================
# AUTHENTICATION
# =========================================================

def verify_token(

    credentials:
    HTTPAuthorizationCredentials = Depends(security)

):

    """
    Public Classical Channel Authentication

    Used ONLY for:
    - ETSI APIs
    - metadata synchronization
    - inter-KMS communication

    NOT:
    - quantum channel
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

    if credentials.credentials != AUTH_TOKEN:

        raise HTTPException(

            status_code=401,

            detail="Invalid token"
        )

    return True


# =========================================================
# ROUTER FACTORY
# =========================================================

def create_etsi_router(
    buffer,
    audit
):

    router = APIRouter()

    # =====================================================
    # STATUS ENDPOINT
    # =====================================================

    @router.get("/etsi/v2/status")
    def status(
        auth: bool = Depends(verify_token)
    ):

        """
        ETSI-QKD node status.
        """

        audit.api("/etsi/v2/status")

        stats = buffer.stats()

        return {

            "service":
                "Hybrid-QKD-KMS",

            "status":
                "RUNNING",

            "node":
                NODE_ID,

            "mode":
                SYSTEM_MODE,

            "qkd_protocol":
                QKD_PROTOCOL,

            "available_keys":
                stats.get(
                    "ready_keys",
                    0
                ),

            "total_keys":
                stats.get(
                    "total_keys",
                    0
                ),

            "verified_keys":
                stats.get(
                    "verified_keys",
                    0
                ),

            "sync_index":
                stats.get(
                    "sync_index",
                    0
                )
        }

    # =====================================================
    # GET NEXT KEY
    # =====================================================

    @router.post("/etsi/v2/keys")
    def get_next_key(
        auth: bool = Depends(verify_token)
    ):

        """
        Fetch locally synchronized quantum key.

        IMPORTANT
        ---------
        This endpoint should eventually expose
        ONLY metadata.

        Current implementation still exposes
        local key material for demo/testing.
        """

        audit.api("/etsi/v2/keys")

        key = buffer.peek_next_key()

        if not key:

            audit.error(
                "No synchronized keys available"
            )

            raise HTTPException(

                status_code=404,

                detail="No synchronized keys"
            )

        metadata = buffer.get_metadata(
            key.key_id
        )

        audit.key_served(
            key.key_id
        )

        return {

            # ---------------------------------------------
            # KEY IDENTIFIER
            # ---------------------------------------------
            "key_id":
                key.key_id,

            # ---------------------------------------------
            # TEMPORARY DEMO FIELD
            # ---------------------------------------------
            "key":
                key.key_value,

            # ---------------------------------------------
            # KEY INFO
            # ---------------------------------------------
            "size":
                key.key_size,

            "origin":
                key.origin_node,

            # ---------------------------------------------
            # QKD
            # ---------------------------------------------
            "protocol":
                QKD_PROTOCOL,

            "mode":
                SYSTEM_MODE,

            # ---------------------------------------------
            # SYNCHRONIZATION
            # ---------------------------------------------
            "sync_index":
                metadata.get(
                    "sync_index",
                    0
                ),

            "verified":
                metadata.get(
                    "verified",
                    False
                ),

            # ---------------------------------------------
            # HASH
            # ---------------------------------------------
            "key_hash":
                metadata.get(
                    "key_hash"
                )
        }

    # =====================================================
    # GET KEY BY ID
    # =====================================================

    @router.get("/etsi/v2/keys/{key_id}")
    def get_key_by_id(

        key_id: str,

        auth: bool = Depends(verify_token)
    ):

        """
        Fetch local synchronized key state.

        IMPORTANT
        ---------
        Real ETSI systems should exchange:
        - metadata
        - hashes
        - synchronization state

        NOT raw key material.
        """

        audit.api(
            f"/etsi/v2/keys/{key_id}"
        )

        key = buffer.get_key_by_id(
            key_id
        )

        if not key:

            audit.error(
                f"Key not found: {key_id}"
            )

            raise HTTPException(

                status_code=404,

                detail="Key not found"
            )

        metadata = buffer.get_metadata(
            key_id
        )

        audit.key_served(
            key_id
        )

        response = {

            # ---------------------------------------------
            # IDENTIFIER
            # ---------------------------------------------
            "key_id":
                key.key_id,

            # ---------------------------------------------
            # TEMPORARY DEMO FIELD
            # ---------------------------------------------
            "key":
                key.key_value,

            # ---------------------------------------------
            # INFO
            # ---------------------------------------------
            "size":
                key.key_size,

            # ---------------------------------------------
            # QKD
            # ---------------------------------------------
            "protocol":
                QKD_PROTOCOL,

            "mode":
                SYSTEM_MODE,

            # ---------------------------------------------
            # METADATA
            # ---------------------------------------------
            "sync_index":
                metadata.get(
                    "sync_index",
                    0
                ),

            "created_at":
                metadata.get(
                    "created_at"
                ),

            "origin":
                metadata.get(
                    "origin"
                ),

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
        # SHA-256
        # =================================================

        if ENABLE_SHA256_SYNC:

            response["key_hash"] = (
                metadata.get("key_hash")
            )

        return response

    # =====================================================
    # METADATA ONLY
    # =====================================================

    @router.get("/etsi/v2/metadata/{key_id}")
    def get_metadata_only(

        key_id: str,

        auth: bool = Depends(verify_token)
    ):

        """
        Proper ETSI metadata synchronization.

        NO raw quantum key exposure.
        """

        if not ENABLE_METADATA_SYNC:

            raise HTTPException(

                status_code=403,

                detail=
                    "Metadata sync disabled"
            )

        audit.api(
            f"/etsi/v2/metadata/{key_id}"
        )

        metadata = buffer.get_metadata(
            key_id
        )

        if not metadata:

            raise HTTPException(

                status_code=404,

                detail=
                    "Metadata not found"
            )

        audit.sync_metadata(

            key_id,

            metadata.get(
                "session_id"
            ),

            metadata.get(
                "sync_index"
            )
        )

        return {

            "key_id":
                metadata.get(
                    "key_id"
                ),

            "sync_index":
                metadata.get(
                    "sync_index"
                ),

            "created_at":
                metadata.get(
                    "created_at"
                ),

            "origin":
                metadata.get(
                    "origin"
                ),

            "verified":
                metadata.get(
                    "verified"
                ),

            "key_hash":
                metadata.get(
                    "key_hash"
                )
        }

    # =====================================================
    # VERIFY HASH
    # =====================================================

    @router.post("/etsi/v2/verify/{key_id}")
    def verify_hash(

        key_id: str,

        payload: dict,

        auth: bool = Depends(verify_token)
    ):

        """
        Verify synchronization integrity.

        SHA-256(K_IITR) == SHA-256(K_IITJ)

        WITHOUT transferring raw keys.
        """

        received_hash = payload.get(
            "key_hash"
        )

        if not received_hash:

            raise HTTPException(

                status_code=400,

                detail="Missing key_hash"
            )

        verified = buffer.verify_key_hash(

            key_id,

            received_hash
        )

        if verified:

            audit.sync_success(
                key_id
            )

        else:

            audit.sync_fail(
                key_id
            )

        return {

            "key_id":
                key_id,

            "verified":
                verified
        }

    return router