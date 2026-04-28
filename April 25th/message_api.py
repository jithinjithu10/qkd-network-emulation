# message_api.py
# FINAL STABLE VERSION (NO DEADLOCK, NO SELF-HTTP, BUFFER-ONLY)

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from secure_transfer import SecureTransfer
from audit import AuditLogger
from config import AUTH_TOKEN


# =================================================
# CONFIG
# =================================================

KMS_URL = "http://127.0.0.1:8001"   # IITJ KMS (used only for logging/context)

audit = AuditLogger()
router = APIRouter()
security = HTTPBearer()

# This will be injected from kms_server.py
buffer_ref = None


# =================================================
# SET BUFFER (INJECTED FROM MAIN SERVER)
# =================================================
def set_buffer(buffer):
    global buffer_ref
    buffer_ref = buffer


# =================================================
# AUTHENTICATION
# =================================================
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    if not credentials:
        raise HTTPException(status_code=401, detail="Missing credentials")

    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    if credentials.credentials != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    return True


# =================================================
# RECEIVE MESSAGE (FINAL CLEAN VERSION)
# =================================================
@router.post("/receive-message")
async def receive_message(
    request: Request,
    auth: bool = Depends(verify_token)
):
    """
    Receives encrypted message from IITR and decrypts using local buffer.
    No HTTP calls are made internally to avoid deadlocks.
    """

    audit.api("/receive-message")

    # -------------------------------
    # PARSE REQUEST
    # -------------------------------
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    key_id = data.get("key_id")
    iv_hex = data.get("iv")
    ct_hex = data.get("ciphertext")
    tag_hex = data.get("tag")

    # -------------------------------
    # VALIDATION
    # -------------------------------
    if not key_id or not iv_hex or not ct_hex or not tag_hex:
        raise HTTPException(status_code=400, detail="Missing fields")

    try:
        iv = bytes.fromhex(iv_hex)
        ciphertext = bytes.fromhex(ct_hex)
        tag = bytes.fromhex(tag_hex)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid hex")

    # -------------------------------
    # BUFFER CHECK (CRITICAL)
    # -------------------------------
    if buffer_ref is None:
        raise HTTPException(status_code=500, detail="Buffer not initialized")

    key_obj = buffer_ref.get_key_by_id(str(key_id))

    if key_obj is None:
        raise HTTPException(status_code=503, detail="Key not available locally")

    # -------------------------------
    # DECRYPT (LOCAL BUFFER ONLY)
    # -------------------------------
    try:
        st = SecureTransfer(KMS_URL, AUTH_TOKEN)

        plaintext = st.receive_secure_message(
            key_id,
            iv,
            ciphertext,
            tag,
            buffer=buffer_ref   # critical: prevents HTTP self-call
        )

    except Exception as e:
        audit.error(f"Decryption failed: {str(e)}", plane="APP")
        raise HTTPException(status_code=500, detail="Decryption failed")

    # -------------------------------
    # LOG OUTPUT
    # -------------------------------
    print("\n==============================")
    print(" RECEIVED SECURE MESSAGE")
    print("==============================")
    print(f"Key ID: {key_id}")
    print(f"Message: {plaintext}")
    print("==============================\n")

    audit.log("MESSAGE_RECEIVED", f"id={key_id}", "APP")

    return {
        "status": "success",
        "message": plaintext
    }