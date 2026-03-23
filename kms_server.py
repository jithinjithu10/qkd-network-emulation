"""
kms_server.py (UPDATED - RESEARCH LEVEL)

Fixes:
- Removed "sync-" prefix
- Removed SYNC_KEY_INDEX dependency
- Clean sync-safe key generation
- Consistent key_id handling
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import uuid
import secrets
import hashlib

from config import (
    HOST,
    PORT,
    NODE_ROLE,
    KEY_SIZE,
    DEFAULT_TTL_SECONDS,
    INITIAL_KEY_POOL_SIZE,
    SYSTEM_MODE,
    SYNC_SEED
)

from buffers import QBuffer
from audit import AuditLogger
from models import Key

from etsi_api import create_etsi_router
from interkms_api import create_interkms_router
from interkms_client import InterKMSClient


# =================================================
# SHARED
# =================================================

buffer = QBuffer()
audit = AuditLogger()

interkms_client = InterKMSClient(buffer, audit)


# =================================================
# SYNC KEY GENERATOR
# =================================================

def generate_sync_key(index: int):
    data = f"{SYNC_SEED}-{index}".encode()
    return hashlib.sha256(data).hexdigest()


# =================================================
# PRELOAD KEYS
# =================================================

def preload_keys():

    print(f"[INFO] Preloading keys (mode={SYSTEM_MODE})")

    for i in range(INITIAL_KEY_POOL_SIZE):

        # -----------------------------
        # SYNC MODE
        # -----------------------------
        if SYSTEM_MODE == "SYNC":

            key_id = str(i)   # FIXED (numeric only)
            key_value = generate_sync_key(i)
            origin = "SYNC"

        # -----------------------------
        # ETSI MODE
        # -----------------------------
        else:

            key_id = str(uuid.uuid4())
            key_value = secrets.token_bytes(KEY_SIZE // 8).hex()
            origin = "LOCAL"

        key = Key(
            key_id=key_id,
            key_value=key_value,
            key_size=KEY_SIZE,
            ttl_seconds=DEFAULT_TTL_SECONDS,
            origin_node=origin
        )

        # add to buffer
        if origin == "SYNC":
            buffer.add_sync_key(key)
        else:
            buffer.add_key(key)

        print(f"[KEY GENERATED] id={key_id} value={key_value[:12]}...")

    print(f"[INFO] {INITIAL_KEY_POOL_SIZE} keys preloaded")


# =================================================
# LIFESPAN
# =================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("[SYSTEM] Starting QKD Node...")

    audit.system_start()

    preload_keys()

    # start inter-KMS if client
    if NODE_ROLE == "CLIENT":
        interkms_client.start()
        print("[INFO] Inter-KMS client started")

    print("[SYSTEM] Node ready")

    yield

    print("[SYSTEM] Shutting down...")

    interkms_client.stop()
    audit.system_shutdown()


# =================================================
# APP
# =================================================

app = FastAPI(
    title="ETSI-Aligned QKD Node",
    version="4.0",
    description="QKD Key Management Node",
    lifespan=lifespan
)

app.include_router(create_etsi_router(buffer, audit))
app.include_router(create_interkms_router(buffer, audit))


# =================================================
# MAIN
# =================================================

if __name__ == "__main__":

    uvicorn.run(
        "kms_server:app",
        host=HOST,
        port=PORT,
        reload=False
    )