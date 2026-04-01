# kms_server.py (FINAL - WITH ACK SUPPORT)

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

#  NEW
from ack_manager import AckManager


# =================================================
# SHARED
# =================================================

buffer = QBuffer()
audit = AuditLogger()

interkms_client = InterKMSClient(buffer, audit)

#  ACK MANAGER
ack_manager = AckManager()


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

    else:

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

        else:
            print("[IITJ] Waiting for keys from IITR...")

    print(f"[INFO] Preload complete")


# =================================================
# LIFESPAN
# =================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("[SYSTEM] Starting QKD Node...")

    audit.system_start()

    preload_keys()

    if NODE_ROLE == "CLIENT":
        interkms_client.start()
        print("[INFO] Inter-KMS client started")

    print("[SYSTEM] Node ready")

    yield

    print("[SYSTEM] Shutting down...")

    interkms_client.stop()
    audit.system_stop()


# =================================================
# APP
# =================================================

app = FastAPI(
    title="ETSI-Aligned QKD Node",
    version="FINAL+ACK",
    description="QKD Key Management Node",
    lifespan=lifespan
)

app.include_router(create_etsi_router(buffer, audit))

#  PASS ACK MANAGER HERE
app.include_router(create_interkms_router(buffer, audit, ack_manager))


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