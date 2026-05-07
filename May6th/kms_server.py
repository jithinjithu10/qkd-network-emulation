# kms_server.py
# FINAL PRODUCTION VERSION (WITH BUFFER INJECTION FIX)

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import secrets
import hashlib

from config import (
    HOST,
    PORT,
    NODE_ROLE,
    NODE_ID,
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
from ack_manager import AckManager

# 🔥 IMPORTANT: import set_buffer also
from message_api import router as message_router, set_buffer


# =================================================
# CONFIG VALIDATION
# =================================================
if NODE_ID == "IITR" and NODE_ROLE != "SERVER":
    raise ValueError("Invalid config: IITR must run as SERVER")

if NODE_ID == "IITJ" and NODE_ROLE != "CLIENT":
    raise ValueError("Invalid config: IITJ must run as CLIENT")


# =================================================
# SHARED COMPONENTS
# =================================================
buffer = QBuffer()
audit = AuditLogger()

interkms_client = InterKMSClient(buffer, audit)
ack_manager = AckManager()


# =================================================
# 🔥 CRITICAL FIX: INJECT BUFFER INTO MESSAGE API
# =================================================
set_buffer(buffer)


# =================================================
# SYNC KEY GENERATOR (LOCAL MODE)
# =================================================
def generate_sync_key(index: int) -> str:
    data = f"{SYNC_SEED}-{index}".encode()
    return hashlib.sha256(data).hexdigest()


# =================================================
# PRELOAD KEYS
# =================================================
def preload_keys():

    print(f"[INFO] Preloading keys (mode={SYSTEM_MODE})")

    # SYNC MODE
    if SYSTEM_MODE == "SYNC":

        for i in range(INITIAL_KEY_POOL_SIZE):

            key_id = str(i)
            key_value = generate_sync_key(i)

            key = Key(
                key_id=key_id,
                key_value=key_value,
                key_size=KEY_SIZE,
                ttl_seconds=DEFAULT_TTL_SECONDS,
                origin_node="SYNC"
            )

            buffer.add_sync_key(key)
            print(f"[SYNC KEY] id={key_id}")

    # ETSI MODE
    else:

        # IITR generates keys
        if NODE_ID == "IITR":

            for i in range(INITIAL_KEY_POOL_SIZE):

                key_id = str(i)
                key_value = secrets.token_bytes(KEY_SIZE // 8).hex()

                key = Key(
                    key_id=key_id,
                    key_value=key_value,
                    key_size=KEY_SIZE,
                    ttl_seconds=DEFAULT_TTL_SECONDS,
                    origin_node="IITR"
                )

                buffer.add_key(key)
                print(f"[IITR KEY] id={key_id}")

        # IITJ waits for sync
        else:
            print("[IITJ] Waiting for keys from IITR...")

    print("[INFO] Preload complete")


# =================================================
# APPLICATION LIFECYCLE
# =================================================
@asynccontextmanager
async def lifespan(app: FastAPI):

    print("[SYSTEM] Starting QKD Node...")
    audit.system_start()

    preload_keys()

    # IITJ starts sync client
    if NODE_ID == "IITJ":
        interkms_client.start()
        print("[INFO] Inter-KMS client started")

    print("[SYSTEM] Node ready")

    yield

    print("[SYSTEM] Shutting down...")
    interkms_client.stop()
    audit.system_stop()


# =================================================
# FASTAPI APPLICATION
# =================================================
app = FastAPI(
    title="ETSI-Aligned QKD Node",
    version="FINAL+STABLE",
    description="QKD Key Management Node with Messaging Support",
    lifespan=lifespan
)

# ETSI API
app.include_router(create_etsi_router(buffer, audit))

# Inter-KMS API
app.include_router(create_interkms_router(buffer, audit, ack_manager))

# Message API (now has buffer access)
app.include_router(message_router)


# =================================================
# MAIN ENTRY POINT
# =================================================
if __name__ == "__main__":

    uvicorn.run(
        "kms_server:app",
        host=HOST,
        port=PORT,
        reload=False
    )