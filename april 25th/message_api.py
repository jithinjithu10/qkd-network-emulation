# message_api.py
# Purpose:
# Receives encrypted message from IITR and decrypts it at IITJ
#
# This is REQUIRED for real communication between nodes


from fastapi import APIRouter, Request, HTTPException
from secure_transfer import SecureTransfer
from audit import AuditLogger


# =================================================
# CONFIGURATION
# =================================================

# IMPORTANT: CHANGE THIS
# IITJ SIDE → use local KMS
# Example:
# KMS_URL = "http://localhost:8001"

KMS_URL = "http://localhost:8001"


# IMPORTANT: MUST MATCH config.py AUTH_TOKEN
TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"


audit = AuditLogger()

router = APIRouter()


# =================================================
# RECEIVE MESSAGE ENDPOINT
# =================================================

@router.post("/receive-message")
async def receive_message(request: Request):
    """
    Receives encrypted message from IITR
    Decrypts using correct key_id from KMS
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
        raise HTTPException(status_code=400, detail="Invalid hex format")

    # -------------------------------
    # DECRYPT
    # -------------------------------
    try:
        st = SecureTransfer(KMS_URL, TOKEN)

        plaintext = st.receive_secure_message(
            key_id,
            iv,
            ciphertext,
            tag
        )

    except Exception as e:
        audit.error(f"Decryption failed: {str(e)}", plane="APP")
        raise HTTPException(status_code=500, detail="Decryption failed")

    # -------------------------------
    # LOG + OUTPUT
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