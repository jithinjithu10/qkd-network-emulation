# kms_server.py
# Purpose:
# Main server for QKD Key Management System.
# Handles:
# - Key generation (IITR)
# - Key synchronization (IITJ)
# - API endpoints (ETSI + InterKMS + Message API)
# - ACK tracking
#
# NOTE:
# IP and port are controlled via config.py


from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import secrets
import hashlib

from config import (
    HOST,                   # IMPORTANT: 0.0.0.0 for public access
    PORT,                   # IMPORTANT: 8000 (IITR) / 8001 (IITJ)
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

# NEW: message receiving API
from message_api import router as message_router


# =================================================
# SHARED COMPONENTS
# =================================================

buffer = QBuffer()
audit = AuditLogger()

# Inter-KMS client (only active on CLIENT node)
interkms_client = InterKMSClient(buffer, audit)

# ACK manager for tracking key confirmations
ack_manager = AckManager()


# =================================================
# SYNC KEY GENERATOR (FOR LOCAL MODE)
# =================================================

def generate_sync_key(index: int) -> str:
    """
    Deterministic key generation for SYNC mode.
    Both nodes must use same SYNC_SEED.
    """
    data = f"{SYNC_SEED}-{index}".encode()
    return hashlib.sha256(data).hexdigest()


# =================================================
# PRELOAD KEYS
# =================================================

def preload_keys():
    """
    Initialize key buffer depending on mode and node role.
    """

    print(f"[INFO] Preloading keys (mode={SYSTEM_MODE})")

    # -------------------------------
    # SYNC MODE (LOCAL TESTING)
    # -------------------------------
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

    # -------------------------------
    # ETSI MODE (REAL DEPLOYMENT)
    # -------------------------------
    else:

        # IITR generates keys
        if NODE_ID == "IITR":

            for i in range(INITIAL_KEY_POOL_SIZE):

                key_id = str(i)

                # Secure random key
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
    """
    Handles startup and shutdown events.
    """

    print("[SYSTEM] Starting QKD Node...")

    audit.system_start()

    # Initialize keys
    preload_keys()

    # Start Inter-KMS sync (only for CLIENT node)
    if NODE_ROLE == "CLIENT":
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
    version="FINAL+MESSAGE+ACK",
    description="QKD Key Management Node with Messaging Support",
    lifespan=lifespan
)

# ETSI API (client-facing)
app.include_router(create_etsi_router(buffer, audit))

# Inter-KMS API (node-to-node communication)
app.include_router(create_interkms_router(buffer, audit, ack_manager))

# NEW: Message API (for receiving encrypted messages)
app.include_router(message_router)


# =================================================
# MAIN ENTRY POINT
# =================================================

if __name__ == "__main__":

    # IMPORTANT:
    # IITR → PORT = 8000
    # IITJ → PORT = 8001
    # HOST must be 0.0.0.0 for public access

    uvicorn.run(
        "kms_server:app",
        host=HOST,
        port=PORT,
        reload=False
    )