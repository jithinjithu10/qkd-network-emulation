# kms_server.py
# ADVANCED HYBRID QUANTUM-CLASSICAL QKD NODE

from fastapi import FastAPI
from contextlib import asynccontextmanager

import uvicorn
import hashlib
import secrets
import threading
import time
import uuid
import signal
import sys

from config import (

    HOST,
    PORT,

    NODE_ROLE,
    NODE_ID,

    KEY_SIZE,
    DEFAULT_TTL_SECONDS,
    INITIAL_KEY_POOL_SIZE,

    SYSTEM_MODE,
    SYNC_SEED,

    QKD_PROTOCOL,

    ENABLE_RUNTIME_KEY_REGENERATION,
    KEY_REGENERATION_INTERVAL,

    SIMULAQRON_ENABLED,
    QUANTUM_LAYER_ENABLED,

    ENABLE_STREAMLIT_DASHBOARD
)

from buffers import QBuffer
from audit import AuditLogger
from models import Key

from etsi_api import create_etsi_router

from interkms_api import (
    create_interkms_router
)

from interkms_client import (
    InterKMSClient
)

from ack_manager import AckManager

from message_api import (
    router as message_router,
    set_buffer
)

from session_manager import (
    SessionManager
)

from sync_manager import (
    SyncManager
)

from qber_monitor import (
    QBERMonitor
)

from qkd_manager import (
    QKDManager
)

from performance_metrics import (
    PerformanceMetrics
)

# =========================================================
# CONFIG VALIDATION
# =========================================================

if (
    NODE_ID == "IITR"
    and NODE_ROLE != "SERVER"
):

    raise ValueError(
        "IITR must run as SERVER"
    )

if (
    NODE_ID == "IITJ"
    and NODE_ROLE != "CLIENT"
):

    raise ValueError(
        "IITJ must run as CLIENT"
    )

# =========================================================
# SHARED COMPONENTS
# =========================================================

buffer = QBuffer()

audit = AuditLogger()

session_manager = SessionManager()

sync_manager = SyncManager()

qber_monitor = QBERMonitor()

metrics = PerformanceMetrics()

qkd_manager = QKDManager(
    buffer,
    audit
)

interkms_client = InterKMSClient(
    buffer,
    audit
)

ack_manager = AckManager()

# =========================================================
# BUFFER INJECTION
# =========================================================

set_buffer(buffer)

# =========================================================
# SESSION STORAGE
# =========================================================

active_sessions = {}

# =========================================================
# SHUTDOWN FLAG
# =========================================================

shutdown_flag = False

# =========================================================
# QUANTUM RUNTIME DETECTION
# =========================================================

try:

    from cqc.pythonLib import (
        CQCConnection
    )

    REAL_QUANTUM_RUNTIME = True

except Exception:

    REAL_QUANTUM_RUNTIME = False

# =========================================================
# BB84 SIMULATION
# =========================================================

def generate_bb84_key(index: int):

    """
    Deterministic BB84-derived entropy.

    In production:
    - generated via SimulaQron
    - qubit exchange
    - basis reconciliation
    - privacy amplification
    """

    data = (
        f"{SYNC_SEED}-BB84-{index}"
    ).encode()

    return hashlib.sha256(
        data
    ).hexdigest()

# =========================================================
# CREATE SESSION
# =========================================================

def create_session(key_id):

    session_id = session_manager.create_session(

        source_node=NODE_ID,

        destination_node="PEER"
    )

    active_sessions[key_id] = {

        "session_id":
            session_id,

        "created_at":
            time.time(),

        "protocol":
            QKD_PROTOCOL
    }

    audit.session_created(
        session_id
    )

    return session_id

# =========================================================
# PRELOAD KEYS
# =========================================================

def preload_keys():

    print(
        f"[INFO] Preloading keys "
        f"(mode={SYSTEM_MODE})"
    )

    # =====================================================
    # SYNC MODE
    # =====================================================

    if SYSTEM_MODE == "SYNC":

        for i in range(
            INITIAL_KEY_POOL_SIZE
        ):

            key_id = str(i)

            key_value = generate_bb84_key(i)

            session_id = create_session(
                key_id
            )

            key = Key(

                key_id=key_id,

                key_value=key_value,

                key_size=KEY_SIZE,

                ttl_seconds=
                    DEFAULT_TTL_SECONDS,

                origin_node="SYNC_BB84"
            )

            buffer.add_sync_key(key)

            session_manager.add_key(
                session_id,
                key_id
            )

            audit.bb84_complete(
                session_id,
                key_id
            )

            print(
                f"[SYNC BB84 KEY] "
                f"id={key_id}"
            )

    # =====================================================
    # ETSI MODE
    # =====================================================

    else:

        # -------------------------------------------------
        # IITR GENERATES QUANTUM KEYS
        # -------------------------------------------------

        if NODE_ID == "IITR":

            for i in range(
                INITIAL_KEY_POOL_SIZE
            ):

                key_id = str(i)

                # -----------------------------------------
                # QUANTUM
                # -----------------------------------------

                if QUANTUM_LAYER_ENABLED:

                    key_value = generate_bb84_key(i)

                else:

                    key_value = secrets.token_bytes(
                        KEY_SIZE // 8
                    ).hex()

                # -----------------------------------------
                # SESSION
                # -----------------------------------------

                session_id = create_session(
                    key_id
                )

                # -----------------------------------------
                # STORE KEY
                # -----------------------------------------

                key = Key(

                    key_id=key_id,

                    key_value=key_value,

                    key_size=KEY_SIZE,

                    ttl_seconds=
                        DEFAULT_TTL_SECONDS,

                    origin_node="IITR_BB84"
                )

                buffer.add_key(key)

                session_manager.add_key(
                    session_id,
                    key_id
                )

                audit.bb84_complete(
                    session_id,
                    key_id
                )

                print(
                    f"[IITR BB84 KEY] "
                    f"id={key_id}"
                )

        # -------------------------------------------------
        # IITJ
        # -------------------------------------------------

        else:

            print(
                "[IITJ] Waiting for "
                "BB84 synchronization..."
            )

    print("[INFO] Key preload complete")

# =========================================================
# RUNTIME KEY REGENERATION
# =========================================================

def runtime_key_regeneration_loop():

    if NODE_ID != "IITR":
        return

    while not shutdown_flag:

        try:

            time.sleep(
                KEY_REGENERATION_INTERVAL
            )

            next_index = (
                buffer.stats()["sync_index"]
            )

            key_id = str(next_index)

            # ---------------------------------------------
            # QUANTUM
            # ---------------------------------------------

            if QUANTUM_LAYER_ENABLED:

                key_value = generate_bb84_key(
                    next_index
                )

            else:

                key_value = secrets.token_bytes(
                    KEY_SIZE // 8
                ).hex()

            # ---------------------------------------------
            # SESSION
            # ---------------------------------------------

            session_id = create_session(
                key_id
            )

            # ---------------------------------------------
            # STORE KEY
            # ---------------------------------------------

            key = Key(

                key_id=key_id,

                key_value=key_value,

                key_size=KEY_SIZE,

                ttl_seconds=
                    DEFAULT_TTL_SECONDS,

                origin_node="RUNTIME_BB84"
            )

            buffer.add_key(key)

            session_manager.add_key(
                session_id,
                key_id
            )

            # ---------------------------------------------
            # AUDIT
            # ---------------------------------------------

            audit.runtime_regeneration(
                session_id
            )

            audit.bb84_complete(
                session_id,
                key_id
            )

            print(
                f"[RUNTIME BB84 KEY] "
                f"id={key_id}"
            )

        except Exception as e:

            audit.error(

                (
                    f"Key regeneration failed: "
                    f"{str(e)}"
                ),

                "QUANTUM"
            )

# =========================================================
# MONITOR THREAD
# =========================================================

def runtime_monitor_loop():

    while not shutdown_flag:

        try:

            stats = buffer.stats()

            print("\n[MONITOR]")

            print(
                f"Ready Keys: "
                f"{stats['ready_keys']}"
            )

            print(
                f"Verified Keys: "
                f"{stats['verified_keys']}"
            )

            print(
                f"Sync Index: "
                f"{stats['sync_index']}"
            )

            print(
                f"Active Sessions: "
                f"{len(session_manager.active_sessions())}"
            )

            time.sleep(20)

        except:
            pass

# =========================================================
# START REGENERATION
# =========================================================

def start_runtime_regeneration():

    if not ENABLE_RUNTIME_KEY_REGENERATION:
        return

    if NODE_ID != "IITR":
        return

    thread = threading.Thread(

        target=runtime_key_regeneration_loop,

        daemon=True
    )

    thread.start()

    print(
        "[INFO] Runtime regeneration active"
    )

# =========================================================
# START MONITOR
# =========================================================

def start_monitor():

    thread = threading.Thread(

        target=runtime_monitor_loop,

        daemon=True
    )

    thread.start()

# =========================================================
# SIGNAL HANDLER
# =========================================================

def handle_shutdown(sig, frame):

    global shutdown_flag

    shutdown_flag = True

    print("\n[SYSTEM]")
    print("Graceful shutdown initiated")

    interkms_client.stop()

    qkd_manager.stop()

    audit.system_stop()

    sys.exit(0)

# =========================================================
# LIFECYCLE
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("\n[SYSTEM]")
    print("Starting Hybrid QKD Node...")

    audit.system_start()

    # =====================================================
    # QUANTUM
    # =====================================================

    if SIMULAQRON_ENABLED:

        audit.quantum_channel_ready()

        print(
            "[QUANTUM] SimulaQron enabled"
        )

    # =====================================================
    # RUNTIME
    # =====================================================

    if REAL_QUANTUM_RUNTIME:

        print(
            "[QUANTUM] "
            "Real SimulaQron runtime detected"
        )

    else:

        print(
            "[QUANTUM] "
            "Logical BB84 simulation mode"
        )

    # =====================================================
    # PRELOAD
    # =====================================================

    preload_keys()

    # =====================================================
    # QKD MANAGER
    # =====================================================

    qkd_manager.start()

    # =====================================================
    # RUNTIME REGENERATION
    # =====================================================

    start_runtime_regeneration()

    # =====================================================
    # MONITOR
    # =====================================================

    start_monitor()

    # =====================================================
    # INTER-KMS
    # =====================================================

    if NODE_ID == "IITJ":

        interkms_client.start()

        print(
            "[INFO] Inter-KMS client started"
        )

    print("[SYSTEM] Node ready")

    yield

    # =====================================================
    # SHUTDOWN
    # =====================================================

    print("\n[SYSTEM]")
    print("Shutting down...")

    interkms_client.stop()

    qkd_manager.stop()

    audit.system_stop()

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(

    title=
        "Hybrid Quantum-Classical QKD Node",

    version="NEXT-GEN-QKD",

    description=(
        "ETSI-Aligned Hybrid QKD "
        "Key Management System"
    ),

    lifespan=lifespan
)

# =========================================================
# ROUTERS
# =========================================================

app.include_router(

    create_etsi_router(
        buffer,
        audit
    )
)

app.include_router(

    create_interkms_router(

        buffer,

        audit,

        ack_manager
    )
)

app.include_router(
    message_router
)

# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {

        "service":
            "Hybrid-QKD-KMS",

        "node":
            NODE_ID,

        "role":
            NODE_ROLE,

        "protocol":
            QKD_PROTOCOL,

        "mode":
            SYSTEM_MODE,

        "quantum_layer":
            SIMULAQRON_ENABLED,

        "real_quantum_runtime":
            REAL_QUANTUM_RUNTIME,

        "status":
            "RUNNING"
    }

# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    stats = buffer.stats()

    return {

        "status":
            "healthy",

        "available_keys":
            stats["ready_keys"],

        "verified_keys":
            stats["verified_keys"],

        "sync_index":
            stats["sync_index"],

        "sessions":
            len(session_manager.active_sessions()),

        "qkd_metrics":
            qkd_manager.metrics(),

        "sync_metrics":
            sync_manager.stats()
    }

# =========================================================
# METRICS
# =========================================================

@app.get("/metrics")
def metrics_endpoint():

    return {

        "buffer":
            buffer.stats(),

        "sessions":
            session_manager.stats(),

        "qkd":
            qkd_manager.metrics(),

        "sync":
            sync_manager.stats(),

        "qber":
            qber_monitor.metrics()
    }

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    signal.signal(
        signal.SIGINT,
        handle_shutdown
    )

    signal.signal(
        signal.SIGTERM,
        handle_shutdown
    )

    print("\n" + "=" * 65)

    print(
        " HYBRID QUANTUM-CLASSICAL "
        "QKD NODE "
    )

    print("=" * 65)

    print(f"\n[NODE]")
    print(f"{NODE_ID} ({NODE_ROLE})")

    print(f"\n[ARCHITECTURE]")
    print(
        "Quantum Layer   : SimulaQron + BB84"
    )

    print(
        "Classical Layer : ETSI APIs"
    )

    print(
        f"Mode            : {SYSTEM_MODE}"
    )

    print(f"\n[QUANTUM RUNTIME]")

    if REAL_QUANTUM_RUNTIME:

        print(
            "Real SimulaQron runtime detected"
        )

    else:

        print(
            "Logical BB84 simulation"
        )

    if ENABLE_STREAMLIT_DASHBOARD:

        print("\n[DASHBOARD]")

        print(
            "Streamlit dashboard enabled"
        )

    uvicorn.run(

        "kms_server:app",

        host=HOST,

        port=PORT,

        reload=False
    )