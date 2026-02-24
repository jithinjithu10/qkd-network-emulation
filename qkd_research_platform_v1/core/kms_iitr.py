"""
kms_iitr.py
-----------

Research-Grade Central KMS
Buffer-First | Adaptive | Mode-Switchable | Experiment-Ready
With Structured QBER Logging & Statistical Support
Optimized for High-Throughput Key Generation
"""

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import secrets
import uuid
import os
import random
import time

from qkd_research_platform_v1.core.models import Key, KeyRole
from qkd_research_platform_v1.core.buffers import QBuffer, SBuffer
from qkd_research_platform_v1.core.storage import (
    init_db,
    store_key,
    commit_batch
)
from qkd_research_platform_v1.core.audit import (
    log_event,
    log_key_event,
    log_policy_event
)
from qkd_research_platform_v1.core.policy import PolicyEngine


# =================================================
# CONFIGURATION
# =================================================

NODE_ID = os.getenv("NODE_ID", "IITR")

policy_engine = PolicyEngine()

qbuffer = QBuffer(max_capacity=1000)
sbuffer = SBuffer(max_sessions=500)

app = FastAPI(title="Research KMS - Adaptive Architecture")


# =================================================
# LIFESPAN
# =================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log_event(f"{NODE_ID} KMS started")
    yield
    log_event(f"{NODE_ID} KMS stopped")

app.router.lifespan_context = lifespan


# =================================================
# POLICY MODE CONTROL
# =================================================

@app.get("/api/v1/policy/mode")
def get_policy_mode():
    return {"policy_mode": policy_engine.mode}


@app.post("/api/v1/policy/mode")
def set_policy_mode(request: dict):

    mode = request.get("mode")

    if mode not in ["BASELINE", "ADAPTIVE", "STRESS"]:
        raise HTTPException(status_code=400, detail="Invalid mode")

    policy_engine.set_mode(mode)

    log_policy_event(
        f"Policy mode changed to {mode}",
        metadata={"mode": mode}
    )

    return {"status": "UPDATED", "policy_mode": mode}


# =================================================
# QUANTUM SIMULATION (Gaussian QBER Model)
# =================================================

def simulate_quantum_key(key_size: int):

    key_bytes = key_size // 8
    key_value = secrets.token_bytes(key_bytes).hex()

    # Gaussian QBER around 5%
    qber = abs(random.gauss(0.05, 0.02))
    entropy = random.uniform(0.85, 1.0)
    amplification = random.uniform(0.9, 1.0)
    link_quality = 1 - qber

    return key_value, qber, entropy, amplification, link_quality


# =================================================
# STATUS
# =================================================

@app.get("/api/v1/status")
def get_status():

    return {
        "node_id": NODE_ID,
        "policy_mode": policy_engine.mode,
        "qbuffer_size": qbuffer.total_size(NODE_ID),
        "sbuffer_size": sbuffer.size()
    }


# =================================================
# GENERATE KEYS (Optimized Batch Mode)
# =================================================

@app.post("/api/v1/keys/generate")
def generate_keys(request: dict):

    count = request.get("number_of_keys", 1)
    key_size = request.get("key_size", 256)
    role = KeyRole(request.get("role", "ENC"))
    app_id = request.get("app_id", "DEFAULT_APP")

    if not policy_engine.allow_request(app_id, count):
        raise HTTPException(status_code=403, detail="Quota exceeded")

    generated = []

    for _ in range(count):

        pressure = qbuffer.pressure_ratio(NODE_ID)
        policy_engine.adapt_to_buffer_pressure(pressure)

        key_value, qber, entropy, amp, link_q = simulate_quantum_key(key_size)

        key = Key(
            key_id=str(uuid.uuid4()),
            key_value=key_value,
            key_size=key_size,
            ttl_seconds=300,
            role=role,
            source_node=NODE_ID,
            bit_error_rate=qber,
            entropy_score=entropy,
            amplification_factor=amp,
            link_quality=link_q
        )

        if not qbuffer.add(NODE_ID, key):
            break

        # Insert into DB (no immediate commit)
        store_key(key, node_id=NODE_ID)

        log_key_event(
            f"Generated {key.key_id}",
            metadata={
                "qber": qber,
                "entropy": entropy,
                "pressure": pressure,
                "policy_mode": policy_engine.mode,
                "threshold": policy_engine.max_bit_error_rate
            }
        )

        generated.append({"key_id": key.key_id})

    # 🔥 Single disk commit for all inserts
    commit_batch()

    return {
        "status": "GENERATED",
        "count": len(generated),
        "policy_mode": policy_engine.mode
    }


# =================================================
# ALLOCATE KEY
# =================================================

@app.post("/api/v1/keys/allocate")
def allocate_key(request: dict):

    session_id = request.get("session_id")
    role = KeyRole(request.get("role", "ENC"))

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")

    pressure = qbuffer.pressure_ratio(NODE_ID)
    policy_engine.adapt_to_buffer_pressure(pressure)

    start_time = time.time()

    key = qbuffer.pop(NODE_ID, role)

    if not key:
        policy_engine.record_failed_allocation()
        return {"status": "NO_KEYS_AVAILABLE"}

    valid = policy_engine.filter_valid_keys([key])

    if not valid:

        log_policy_event(
            f"Key rejected {key.key_id}",
            metadata={
                "qber": key.bit_error_rate,
                "entropy": key.entropy_score,
                "threshold": policy_engine.max_bit_error_rate,
                "mode": policy_engine.mode,
                "pressure": pressure
            }
        )

        return {"status": "KEY_REJECTED_BY_POLICY"}

    if not sbuffer.reserve(key, session_id):
        return {"status": "SESSION_LIMIT_REACHED"}

    latency = time.time() - start_time

    policy_engine.record_node_allocation(NODE_ID)

    log_key_event(
        f"Allocated {key.key_id}",
        metadata={
            "latency": latency,
            "pressure": pressure,
            "policy_mode": policy_engine.mode
        }
    )

    return {
        "status": "RESERVED",
        "key_id": key.key_id,
        "latency": latency,
        "pressure": pressure,
        "policy_mode": policy_engine.mode,
        "qber_threshold": policy_engine.max_bit_error_rate
    }


# =================================================
# CONSUME KEY
# =================================================

@app.post("/api/v1/keys/consume")
def consume_key_endpoint(request: dict):

    session_id = request.get("session_id")

    key = sbuffer.consume(session_id)

    if not key:
        raise HTTPException(status_code=404, detail="Session not found")

    log_key_event(
        f"Consumed {key.key_id}",
        metadata={"policy_mode": policy_engine.mode}
    )

    return {"status": "CONSUMED", "key_id": key.key_id}


# =================================================
# METRICS
# =================================================

@app.get("/api/v1/metrics")
def get_metrics():

    return {
        "qbuffer_metrics": qbuffer.metrics(),
        "sbuffer_metrics": sbuffer.metrics(),
        "policy_metrics": policy_engine.get_policy_metrics()
    }


# =================================================
# QBER STATS ENDPOINT (Dashboard Support)
# =================================================

@app.get("/api/v1/qber/stats")
def get_qber_stats():

    return {
        "current_threshold": policy_engine.max_bit_error_rate,
        "policy_mode": policy_engine.mode
    }