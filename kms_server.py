"""
kms_server.py

Enhanced ETSI-aligned QKD Node

Now supports:
- ETSI mode (random key generation)
- SYNC mode (deterministic key generation)
- Inter-KMS communication
- Full audit logging
- Lifespan-based startup/shutdown (UPDATED)
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
    SYNC_SEED,
    SYNC_KEY_INDEX
)

from buffers import QBuffer
from audit import AuditLogger
from models import Key

from etsi_api import create_etsi_router
from interkms_api import create_interkms_router
from interkms_client import InterKMSClient


# =================================================
# SHARED COMPONENTS
# =================================================

buffer = QBuffer()
audit = AuditLogger()

interkms_client = InterKMSClient(buffer, audit)


# =================================================
# KEY GENERATION LOGIC
# =================================================

def generate_sync_key(index: int):
    """
    Deterministic key generation (QKD emulation)
    Same key on both nodes
    """
    data = f"{SYNC_SEED}-{index}".encode()
    return hashlib.sha256(data).hexdigest()


# =================================================
# PRELOAD KEYS
# =================================================

def preload_keys():

    print(f"[INFO] Preloading keys (mode={SYSTEM_MODE})")

    for i in range(INITIAL_KEY_POOL_SIZE):

        # -----------------------------
        # SYNC MODE → SAME KEY_ID + VALUE
        # -----------------------------
        if SYSTEM_MODE == "SYNC":

            index = SYNC_KEY_INDEX + i

            key_id = f"sync-{index}"   #  FIXED
            key_value = generate_sync_key(index)
            origin = "SYNC"

        # -----------------------------
        # ETSI MODE → RANDOM
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

        # -----------------------------
        # ADD TO BUFFER
        # -----------------------------
        if origin == "SYNC":
            buffer.add_sync_key(key)
        else:
            buffer.add_key(key)

        # -----------------------------
        # DEBUG LOG
        # -----------------------------
        print(f"[KEY GENERATED] id={key_id} value={key_value[:12]}...")

    print(f"[INFO] {INITIAL_KEY_POOL_SIZE} keys preloaded successfully")


# =================================================
# LIFESPAN HANDLER (REPLACES on_event)
# =================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("[SYSTEM] Starting QKD KMS Node...")

    audit.system_start()

    # Step 1 → preload keys
    preload_keys()

    # Step 2 → Inter-KMS client (ONLY CLIENT NODE)
    if NODE_ROLE == "CLIENT":
        interkms_client.start()
        print("[INFO] Inter-KMS client activated")

    print("[SYSTEM] Node is ready ")

    yield  #  APP RUNS HERE

    # -----------------------------
    # SHUTDOWN LOGIC
    # -----------------------------
    print("[SYSTEM] Shutting down...")

    interkms_client.stop()
    audit.system_shutdown()


# =================================================
# FASTAPI APP
# =================================================

app = FastAPI(
    title="ETSI-Aligned QKD Node",
    version="3.1",
    description="ETSI-compliant QKD Key Management Node",
    lifespan=lifespan   #  IMPORTANT
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