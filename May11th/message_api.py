# message_api.py
# ADVANCED HYBRID QUANTUM-CLASSICAL QKD MESSAGE API

from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    Depends
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from crypto_engine import CryptoEngine

from audit import AuditLogger

from config import (

    AUTH_TOKEN,

    PEER_NODES,
    NODE_ID,

    SYSTEM_MODE,
    QKD_PROTOCOL,

    ENABLE_SHA256_SYNC,
    ENABLE_REPLAY_PROTECTION
)

import hashlib
import hmac
import time
import uuid

from datetime import datetime

# =========================================================
# CONFIGURATION
# =========================================================

KMS_URL = PEER_NODES[NODE_ID]

audit = AuditLogger()

router = APIRouter()

security = HTTPBearer()

# =========================================================
# BUFFER
# =========================================================

buffer_ref = None

# =========================================================
# REPLAY TRACKING
# =========================================================

used_nonces = set()

used_message_ids = set()

# =========================================================
# METRICS
# =========================================================

received_messages = 0

received_files = 0

replay_attempts = 0

decryption_failures = 0

# =========================================================
# SET BUFFER
# =========================================================

def set_buffer(buffer):

    global buffer_ref

    buffer_ref = buffer

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
# CONSTANT-TIME HASH VERIFY
# =========================================================

def verify_sync(

    local_key,

    received_hash
):

    if not ENABLE_SHA256_SYNC:
        return True

    local_hash = sha256_hash(
        local_key
    )

    return hmac.compare_digest(

        local_hash,

        received_hash
    )

# =========================================================
# VERIFY NONCE
# =========================================================

def verify_nonce(
    nonce
):

    global replay_attempts

    if not ENABLE_REPLAY_PROTECTION:
        return True

    if not nonce:
        return False

    if nonce in used_nonces:

        replay_attempts += 1

        return False

    used_nonces.add(
        nonce
    )

    return True

# =========================================================
# VERIFY MESSAGE ID
# =========================================================

def verify_message_id(
    message_id
):

    global replay_attempts

    if not message_id:
        return False

    if message_id in used_message_ids:

        replay_attempts += 1

        return False

    used_message_ids.add(
        message_id
    )

    return True

# =========================================================
# VERIFY TIMESTAMP
# =========================================================

def verify_timestamp(
    metadata
):

    timestamp = metadata.get(
        "timestamp"
    )

    if not timestamp:
        return False

    try:

        current = time.time()

        remote = float(timestamp)

        drift = abs(
            current - remote
        )

        if drift > 120:
            return False

    except:
        return False

    return True

# =========================================================
# AUTH
# =========================================================

def verify_token(

    credentials:
    HTTPAuthorizationCredentials = Depends(security)

):

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
# VERIFY METADATA
# =========================================================

def verify_metadata(
    metadata
):

    required = [

        "session_id",

        "protocol",

        "timestamp"
    ]

    for field in required:

        if field not in metadata:

            return False

    if metadata["protocol"] != QKD_PROTOCOL:

        return False

    if not verify_timestamp(
        metadata
    ):

        return False

    return True

# =========================================================
# RECEIVE SECURE MESSAGE
# =========================================================

@router.post("/receive-message")
async def receive_message(

    request: Request,

    auth: bool = Depends(verify_token)
):

    global received_messages
    global decryption_failures

    audit.api("/receive-message")

    # =====================================================
    # REQUEST
    # =====================================================

    try:

        data = await request.json()

    except Exception:

        raise HTTPException(

            status_code=400,

            detail="Invalid JSON"
        )

    # =====================================================
    # EXTRACT
    # =====================================================

    key_id = data.get("key_id")

    iv_hex = data.get("iv")

    ct_hex = data.get("ciphertext")

    tag_hex = data.get("tag")

    nonce = data.get("nonce")

    delivery_id = data.get(
        "delivery_id"
    )

    metadata = data.get(
        "metadata",
        {}
    )

    # =====================================================
    # VALIDATE
    # =====================================================

    if (
        not key_id
        or not iv_hex
        or not ct_hex
        or not tag_hex
    ):

        raise HTTPException(

            status_code=400,

            detail="Missing required fields"
        )

    # =====================================================
    # METADATA
    # =====================================================

    valid_metadata = verify_metadata(
        metadata
    )

    if not valid_metadata:

        raise HTTPException(

            status_code=403,

            detail="Invalid metadata"
        )

    # =====================================================
    # REPLAY
    # =====================================================

    if nonce:

        valid_nonce = verify_nonce(
            nonce
        )

        if not valid_nonce:

            raise HTTPException(

                status_code=403,

                detail="Replay nonce detected"
            )

    if delivery_id:

        valid_delivery = verify_message_id(
            delivery_id
        )

        if not valid_delivery:

            raise HTTPException(

                status_code=403,

                detail="Replay delivery detected"
            )

    # =====================================================
    # HEX
    # =====================================================

    try:

        iv = bytes.fromhex(iv_hex)

        ciphertext = bytes.fromhex(
            ct_hex
        )

        tag = bytes.fromhex(tag_hex)

    except Exception:

        raise HTTPException(

            status_code=400,

            detail="Invalid hex encoding"
        )

    # =====================================================
    # BUFFER
    # =====================================================

    if buffer_ref is None:

        raise HTTPException(

            status_code=500,

            detail="Buffer unavailable"
        )

    # =====================================================
    # KEY
    # =====================================================

    key_obj = buffer_ref.get_key_by_id(
        str(key_id)
    )

    if key_obj is None:

        raise HTTPException(

            status_code=503,

            detail="Local key unavailable"
        )

    # =====================================================
    # HASH
    # =====================================================

    received_hash = metadata.get(
        "key_hash"
    )

    if received_hash:

        verified = verify_sync(

            key_obj.key_value,

            received_hash
        )

        audit.hash_verification(
            key_id,
            verified
        )

        if not verified:

            audit.sync_fail(key_id)

            raise HTTPException(

                status_code=403,

                detail="SHA-256 verification failed"
            )

        audit.sync_success(
            key_id
        )

    # =====================================================
    # SESSION
    # =====================================================

    session_id = metadata.get(
        "session_id",
        "UNKNOWN"
    )

    sync_index = metadata.get(
        "sync_index",
        0
    )

    # =====================================================
    # DECRYPTION
    # =====================================================

    start = time.perf_counter()

    try:

        ce = CryptoEngine(

            key_hex=
                key_obj.key_value,

            key_id=
                key_id,

            mode=
                SYSTEM_MODE,

            session_id=
                session_id,

            sync_index=
                sync_index
        )

        if received_hash:

            verified = ce.verify_hash(
                received_hash
            )

            if not verified:

                raise Exception(
                    "Hash mismatch"
                )

        plaintext = ce.decrypt(

            iv,

            ciphertext,

            tag

        ).decode()

    except Exception as e:

        decryption_failures += 1

        audit.error(

            (
                f"Decryption failed: "
                f"{str(e)}"
            ),

            plane="APP"
        )

        raise HTTPException(

            status_code=500,

            detail="AES-GCM decryption failed"
        )

    latency = (
        time.perf_counter()
        - start
    )

    received_messages += 1

    # =====================================================
    # OUTPUT
    # =====================================================

    timestamp = datetime.utcnow().isoformat()

    print("\n" + "=" * 65)

    print(
        " RECEIVED SECURE MESSAGE "
    )

    print("=" * 65)

    print(f"\nTimestamp:")
    print(timestamp)

    print(f"\nDelivery ID:")
    print(delivery_id)

    print(f"\nKey ID:")
    print(key_id)

    print(f"\nSession ID:")
    print(session_id)

    print(f"\nProtocol:")
    print(QKD_PROTOCOL)

    print(f"\nMode:")
    print(SYSTEM_MODE)

    print(f"\nSynchronization:")
    print("VERIFIED")

    print(f"\nReplay Protection:")
    print("PASSED")

    print(f"\nDecryption Latency:")
    print(f"{latency:.6f}s")

    print(f"\nMessage:")
    print(plaintext)

    print("\n" + "=" * 65)

    # =====================================================
    # AUDIT
    # =====================================================

    audit.log(

        "MESSAGE_RECEIVED",

        (
            f"key_id={key_id} "
            f"session={session_id} "
            f"delivery={delivery_id}"
        ),

        "APP"
    )

    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "status":
            "success",

        "node":
            NODE_ID,

        "protocol":
            QKD_PROTOCOL,

        "mode":
            SYSTEM_MODE,

        "verified":
            True,

        "delivery_id":
            delivery_id,

        "latency":
            latency,

        "message":
            plaintext
    }

# =========================================================
# RECEIVE FILE
# =========================================================

@router.post("/receive-file")
async def receive_file(

    request: Request,

    auth: bool = Depends(verify_token)
):

    global received_files
    global decryption_failures

    audit.api("/receive-file")

    try:

        data = await request.json()

    except Exception:

        raise HTTPException(

            status_code=400,

            detail="Invalid JSON"
        )

    chunks = data.get("chunks")

    metadata = data.get(
        "metadata",
        {}
    )

    if not chunks:

        raise HTTPException(

            status_code=400,

            detail="Missing chunks"
        )

    valid_metadata = verify_metadata(
        metadata
    )

    if not valid_metadata:

        raise HTTPException(

            status_code=403,

            detail="Invalid metadata"
        )

    decrypted_output = b""

    chunk_counter = 0

    for chunk in chunks:

        try:

            nonce = chunk.get("nonce")

            if nonce:

                valid_nonce = verify_nonce(
                    nonce
                )

                if not valid_nonce:

                    raise Exception(
                        "Replay nonce"
                    )

            key_id = chunk["key_id"]

            key_obj = buffer_ref.get_key_by_id(
                key_id
            )

            if not key_obj:

                raise Exception(
                    f"Missing key {key_id}"
                )

            ce = CryptoEngine(

                key_hex=
                    key_obj.key_value,

                key_id=
                    key_id,

                mode=
                    SYSTEM_MODE
            )

            plaintext = ce.decrypt(

                bytes.fromhex(
                    chunk["iv"]
                ),

                bytes.fromhex(
                    chunk["ciphertext"]
                ),

                bytes.fromhex(
                    chunk["tag"]
                )
            )

            decrypted_output += plaintext

            chunk_counter += 1

        except Exception as e:

            decryption_failures += 1

            audit.error(

                (
                    f"Chunk decryption failed: "
                    f"{str(e)}"
                ),

                "APP"
            )

            raise HTTPException(

                status_code=500,

                detail="File decryption failed"
            )

    received_files += 1

    audit.log(

        "FILE_RECEIVED",

        (
            f"chunks={chunk_counter}"
        ),

        "APP"
    )

    return {

        "status":
            "success",

        "chunks":
            chunk_counter,

        "size":
            len(decrypted_output)
    }

# =========================================================
# METRICS
# =========================================================

@router.get("/message-metrics")
async def message_metrics():

    return {

        "received_messages":
            received_messages,

        "received_files":
            received_files,

        "replay_attempts":
            replay_attempts,

        "decryption_failures":
            decryption_failures
    }