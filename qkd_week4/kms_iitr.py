"""
kms_iitr.py
------------
Central Key Management System (KMS).
Implements key generation, lifecycle management,
persistent storage, and audit logging.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import secrets
import uuid

from models import Key
from storage import init_db, store_key, fetch_ready_key, mark_consumed
from audit import log_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler.
    This replaces the deprecated @app.on_event("startup") approach.
    """
    # Startup logic
    init_db()
    log_event("Central KMS started")

    yield

    # Shutdown logic (optional, for future use)
    log_event("Central KMS stopped")


# Create FastAPI app with lifespan handler
app = FastAPI(lifespan=lifespan)


@app.get("/api/v1/status")
def get_status():
    """
    Health and capability endpoint for the Central KMS.
    """
    return {
        "status": "UP",
        "kms_id": "IITR-KMS",
        "supported_key_sizes": [128, 256],
        "max_keys_per_request": 10
    }


@app.post("/api/v1/keys/get")
def generate_keys(request: dict):
    """
    Generate and store cryptographic keys.
    """
    number_of_keys = request["number_of_keys"]
    key_size = request["key_size"]

    keys = []

    for _ in range(number_of_keys):
        # Generate cryptographically secure random key material
        key_bytes = key_size // 8
        key_value = secrets.token_bytes(key_bytes).hex()

        # Create Key object
        key = Key(
            key_id=str(uuid.uuid4()),
            key_value=key_value,
            key_size=key_size,
            created_at=datetime.now(timezone.utc).isoformat(),
            ttl_seconds=300
        )

        # Store key and record audit event
        store_key(key)
        log_event(f"Key generated: {key.key_id}")

        keys.append({
            "key_id": key.key_id,
            "key_value": key.key_value
        })

    return {"status": "SUCCESS", "keys": keys}


@app.post("/api/v1/keys/consume")
def consume_key():
    """
    Mark one READY key as CONSUMED.
    """
    key_id = fetch_ready_key()

    if not key_id:
        return {"status": "NO_KEYS_AVAILABLE"}

    mark_consumed(key_id)
    log_event(f"Key consumed: {key_id}")

    return {"status": "CONSUMED", "key_id": key_id}
