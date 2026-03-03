"""
kms_server.py

Entry point for ETSI-aligned QKD Node.

Implements:
- Shared local key buffer (QBuffer)
- ETSI Application Plane (v2)
- Inter-KMS Plane (Node-to-Node)
- Optional Inter-KMS Client (if NODE_ROLE = CLIENT)
- Proper startup key preload
- Clean dependency injection architecture
"""

from fastapi import FastAPI
import uvicorn
import uuid
import secrets

from config import (
    HOST,
    PORT,
    NODE_ROLE,
    KEY_SIZE,
    DEFAULT_TTL_SECONDS,
    INITIAL_KEY_POOL_SIZE
)

from buffers import QBuffer
from audit import AuditLogger
from models import Key

from etsi_api import create_etsi_router
from interkms_api import create_interkms_router
from interkms_client import InterKMSClient


# =================================================
# SHARED NODE COMPONENTS
# =================================================

buffer = QBuffer()
audit = AuditLogger()

# Inter-KMS Client (only active on CLIENT nodes)
interkms_client = InterKMSClient(buffer, audit)


# =================================================
# FASTAPI APPLICATION
# =================================================

app = FastAPI(
    title="ETSI-Aligned QKD Node",
    version="2.2",
    description="ETSI-compliant QKD Key Management Node"
)

app.include_router(create_etsi_router(buffer, audit))
app.include_router(create_interkms_router(buffer, audit))


# =================================================
# KEY PRELOAD FUNCTION
# =================================================

def preload_keys():
    """
    Preload key pool at node startup.
    ETSI-aligned: Key material must exist before serving requests.
    """

    for _ in range(INITIAL_KEY_POOL_SIZE):
        key_id = str(uuid.uuid4())
        key_value = secrets.token_bytes(KEY_SIZE // 8).hex()

        key = Key(
            key_id=key_id,
            key_value=key_value,
            key_size=KEY_SIZE,
            ttl_seconds=DEFAULT_TTL_SECONDS
        )

        buffer.add_key(key)
        audit.key_added(key_id)


# =================================================
# STARTUP EVENT
# =================================================

@app.on_event("startup")
def startup_event():
    """
    Node initialization:
    1. Preload local key pool
    2. Activate Inter-KMS client if CLIENT node
    """

    preload_keys()
    print("[INFO] Key pool preloaded")

    if NODE_ROLE == "CLIENT":
        interkms_client.start()
        print("[INFO] Inter-KMS client activated")


# =================================================
# MAIN ENTRY
# =================================================

if __name__ == "__main__":
    uvicorn.run(
        "kms_server:app",
        host=HOST,
        port=PORT,
        reload=False
    )