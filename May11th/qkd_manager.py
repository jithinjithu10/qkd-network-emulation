# qkd_manager.py
# HYBRID QUANTUM-CLASSICAL QKD ORCHESTRATION LAYER
# UPDATED WITH REAL SIMULAQRON BB84 SUPPORT

import threading
import time
import hashlib
import random
import uuid

from models import Key
from audit import AuditLogger

from config import (

    NODE_ID,

    KEY_SIZE,
    DEFAULT_TTL_SECONDS,

    QKD_PROTOCOL,

    ENABLE_RUNTIME_KEY_REGENERATION,
    KEY_REGENERATION_INTERVAL,

    BB84_NUM_QUBITS,

    MAX_QBER_THRESHOLD,

    QUANTUM_LAYER_ENABLED,

    SIMULAQRON_ENABLED
)

# =========================================================
# OPTIONAL SIMULAQRON IMPORT
# =========================================================

try:

    from cqc.pythonLib import (
        CQCConnection,
        qubit
    )

    SIMULAQRON_AVAILABLE = True

except Exception:

    SIMULAQRON_AVAILABLE = False


class QKDManager:

    """
    QKD MANAGER

    Responsibilities
    ----------------
    - BB84 execution
    - basis reconciliation
    - QBER analysis
    - key regeneration
    - distributed synchronization
    - AES-256 key derivation

    Modes
    -----
    1. Logical BB84 Simulation
    2. Real SimulaQron Runtime
    """

    def __init__(
        self,
        buffer,
        audit: AuditLogger
    ):

        self.buffer = buffer

        self.audit = audit

        self.running = False

        self.thread = None

        # =================================================
        # KEY TRACKING
        # =================================================

        self.current_key_index = 0

        # =================================================
        # SESSION TRACKING
        # =================================================

        self.active_sessions = {}

        # =================================================
        # METRICS
        # =================================================

        self.generated_keys = 0

        self.failed_sessions = 0

        self.total_qber = []

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(

            target=self._runtime_loop,

            daemon=True
        )

        self.thread.start()

        print(
            "[QKD MANAGER] Started"
        )

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

        self.running = False

        if self.thread:

            self.thread.join(timeout=2)

        print(
            "[QKD MANAGER] Stopped"
        )

    # =====================================================
    # MAIN LOOP
    # =====================================================

    def _runtime_loop(self):

        while self.running:

            try:

                self.generate_qkd_session()

            except Exception as e:

                self.failed_sessions += 1

                self.audit.error(

                    f"QKD session failed: {str(e)}",

                    plane="QKD"
                )

            time.sleep(
                KEY_REGENERATION_INTERVAL
            )

    # =====================================================
    # GENERATE SESSION
    # =====================================================

    def generate_qkd_session(self):

        session_id = str(
            uuid.uuid4()
        )[:8]

        self.active_sessions[session_id] = {

            "started":
                time.time(),

            "status":
                "RUNNING"
        }

        self.audit.log(

            "QKD_SESSION_START",

            f"session={session_id}",

            "QKD"
        )

        # =================================================
        # BB84 EXECUTION
        # =================================================

        (
            alice_bits,
            alice_bases,

            bob_results,
            bob_bases
        ) = self.run_bb84()

        # =================================================
        # BASIS RECONCILIATION
        # =================================================

        shared_key_bits = self.reconcile_bases(

            alice_bits,
            alice_bases,

            bob_results,
            bob_bases
        )

        # =================================================
        # QBER
        # =================================================

        qber = self.calculate_qber(

            alice_bits,
            bob_results,

            alice_bases,
            bob_bases
        )

        self.total_qber.append(qber)

        # =================================================
        # QBER ALERT
        # =================================================

        if qber > MAX_QBER_THRESHOLD:

            self.failed_sessions += 1

            self.audit.log(

                "QBER_ALERT",

                (
                    f"session={session_id} "
                    f"qber={qber:.4f}"
                ),

                "QKD"
            )

            self.active_sessions[
                session_id
            ]["status"] = "FAILED"

            return

        # =================================================
        # FINAL AES-256 KEY
        # =================================================

        final_key = self.generate_final_key(
            shared_key_bits
        )

        # =================================================
        # STORE KEY
        # =================================================

        key_id = str(
            self.current_key_index
        )

        key = Key(

            key_id=key_id,

            key_value=final_key,

            key_size=KEY_SIZE,

            ttl_seconds=
                DEFAULT_TTL_SECONDS,

            origin_node=
                f"{NODE_ID}_BB84",

            protocol=QKD_PROTOCOL,

            session_id=session_id,

            sync_index=
                self.current_key_index
        )

        self.buffer.add_key(key)

        # =================================================
        # METADATA
        # =================================================

        self.generated_keys += 1

        self.current_key_index += 1

        self.active_sessions[
            session_id
        ]["status"] = "COMPLETED"

        self.audit.log(

            "QKD_KEY_GENERATED",

            (
                f"session={session_id} "
                f"key_id={key_id}"
            ),

            "QKD"
        )

        print(

            f"[QKD] Generated key "

            f"{key_id} "

            f"(QBER={qber:.4f})"
        )

    # =====================================================
    # BB84 EXECUTION
    # =====================================================

    def run_bb84(self):

        """
        BB84 Execution

        Uses:
        - Real SimulaQron if available
        - Logical simulation otherwise
        """

        if (

            SIMULAQRON_ENABLED
            and
            SIMULAQRON_AVAILABLE
        ):

            return self.run_bb84_simulaqron()

        return self.run_bb84_simulation()

    # =====================================================
    # LOGICAL BB84
    # =====================================================

    def run_bb84_simulation(self):

        alice_bits = []

        alice_bases = []

        bob_results = []

        bob_bases = []

        for _ in range(
            BB84_NUM_QUBITS
        ):

            # ---------------------------------------------
            # Alice random bit
            # ---------------------------------------------

            bit = random.randint(0, 1)

            basis = random.randint(0, 1)

            alice_bits.append(bit)

            alice_bases.append(basis)

            # ---------------------------------------------
            # Bob random basis
            # ---------------------------------------------

            bob_basis = random.randint(0, 1)

            bob_bases.append(bob_basis)

            # ---------------------------------------------
            # Simulated measurement
            # ---------------------------------------------

            if basis == bob_basis:

                bob_results.append(bit)

            else:

                bob_results.append(
                    random.randint(0, 1)
                )

        return (

            alice_bits,
            alice_bases,

            bob_results,
            bob_bases
        )

    # =====================================================
    # REAL SIMULAQRON BB84
    # =====================================================

    def run_bb84_simulaqron(self):

        """
        Real qubit-based BB84.

        Requires:
        - Alice node
        - Bob node
        - SimulaQron network
        """

        alice_bits = []

        alice_bases = []

        bob_results = []

        bob_bases = []

        with CQCConnection("Alice") as Alice:

            with CQCConnection("Bob") as Bob:

                for _ in range(
                    BB84_NUM_QUBITS
                ):

                    # -------------------------------------
                    # Alice
                    # -------------------------------------

                    bit = random.randint(0, 1)

                    basis = random.randint(0, 1)

                    alice_bits.append(bit)

                    alice_bases.append(basis)

                    q = qubit(Alice)

                    # -------------------------------------
                    # Encode bit
                    # -------------------------------------

                    if bit == 1:

                        q.X()

                    # -------------------------------------
                    # Encode basis
                    # -------------------------------------

                    if basis == 1:

                        q.H()

                    # -------------------------------------
                    # Send qubit
                    # -------------------------------------

                    Alice.sendQubit(
                        q,
                        "Bob"
                    )

                    # -------------------------------------
                    # Bob
                    # -------------------------------------

                    bob_basis = random.randint(0, 1)

                    bob_bases.append(
                        bob_basis
                    )

                    q_recv = Bob.recvQubit()

                    # -------------------------------------
                    # Bob measurement basis
                    # -------------------------------------

                    if bob_basis == 1:

                        q_recv.H()

                    measurement = (
                        q_recv.measure()
                    )

                    bob_results.append(
                        measurement
                    )

        return (

            alice_bits,
            alice_bases,

            bob_results,
            bob_bases
        )

    # =====================================================
    # BASIS RECONCILIATION
    # =====================================================

    def reconcile_bases(

        self,

        alice_bits,
        alice_bases,

        bob_results,
        bob_bases
    ):

        """
        Public classical channel operation.

        Only basis information exchanged.
        """

        shared_bits = []

        for i in range(
            len(alice_bits)
        ):

            if alice_bases[i] == bob_bases[i]:

                shared_bits.append(
                    alice_bits[i]
                )

        return shared_bits

    # =====================================================
    # FINAL KEY
    # =====================================================

    def generate_final_key(
        self,
        shared_bits
    ):

        """
        Convert sifted bits
        into AES-256 key.
        """

        bit_string = "".join(

            str(b)
            for b in shared_bits
        )

        return hashlib.sha256(

            bit_string.encode()

        ).hexdigest()

    # =====================================================
    # QBER
    # =====================================================

    def calculate_qber(

        self,

        alice_bits,
        bob_results,

        alice_bases,
        bob_bases
    ):

        compared = 0

        errors = 0

        for i in range(
            len(alice_bits)
        ):

            if alice_bases[i] == bob_bases[i]:

                compared += 1

                if alice_bits[i] != bob_results[i]:

                    errors += 1

        if compared == 0:
            return 1.0

        return errors / compared

    # =====================================================
    # SESSION STATS
    # =====================================================

    def session_stats(self):

        avg_qber = 0

        if self.total_qber:

            avg_qber = (

                sum(self.total_qber)

                /

                len(self.total_qber)
            )

        return {

            "generated_keys":
                self.generated_keys,

            "failed_sessions":
                self.failed_sessions,

            "active_sessions":
                len(self.active_sessions),

            "average_qber":
                avg_qber
        }

    # =====================================================
    # METRICS
    # =====================================================

    def metrics(self):

        stats = self.session_stats()

        return {

            "protocol":
                QKD_PROTOCOL,

            "generated_keys":
                stats["generated_keys"],

            "failed_sessions":
                stats["failed_sessions"],

            "average_qber":
                stats["average_qber"],

            "quantum_layer":
                QUANTUM_LAYER_ENABLED,

            "simulaqron":
                SIMULAQRON_ENABLED,

            "real_quantum_runtime":
                SIMULAQRON_AVAILABLE
        }

    # =====================================================
    # DEBUG
    # =====================================================

    def debug_dump(self):

        return {

            "running":
                self.running,

            "current_key_index":
                self.current_key_index,

            "generated_keys":
                self.generated_keys,

            "failed_sessions":
                self.failed_sessions,

            "sessions":
                self.active_sessions
        }