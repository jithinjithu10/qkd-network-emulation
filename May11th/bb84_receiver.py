# bb84_receiver.py
# QUANTUM LAYER - BOB (RECEIVER)

from cqc.pythonLib import CQCConnection
from cqc.pythonLib.util import CQCTimeoutError

import random
import time

from audit import AuditLogger
from config import BB84_NUM_QUBITS, QKD_PROTOCOL


class BB84Receiver:

    """
    BB84 Quantum Receiver (Bob)

    Responsibilities
    ----------------
    - Receive qubits
    - Choose random bases
    - Measure qubits
    - Generate receiver-side raw key
    - Basis reconciliation
    - QBER estimation
    """

    def __init__(self):

        self.audit = AuditLogger()

        self.bob_bases = []
        self.bob_results = []

        self.received_qubits = 0

    # =====================================================
    # RESET SESSION
    # =====================================================

    def reset(self):

        self.bob_bases.clear()
        self.bob_results.clear()

        self.received_qubits = 0

    # =====================================================
    # RANDOM BASIS
    # =====================================================

    def random_basis(self):

        return random.randint(0, 1)

    # =====================================================
    # MEASURE QUBIT
    # =====================================================

    def measure_qubit(self, q, basis):

        """
        Basis 0 -> Z basis
        Basis 1 -> X basis
        """

        if basis == 1:
            q.H()

        return q.measure()

    # =====================================================
    # RECEIVE SINGLE QUBIT
    # =====================================================

    def receive_qubit(self, connection, index):

        """
        SimulaQron-safe receive loop.
        """

        while True:

            try:

                q = connection.recvQubit()

                return q

            except CQCTimeoutError:

                print(
                    f"[BOB] Waiting for qubit {index}..."
                )

                time.sleep(1)

            except Exception as e:

                print(
                    f"[BOB] Receive error: {e}"
                )

                time.sleep(1)

    # =====================================================
    # RUN RECEIVER
    # =====================================================

    def run(self):

        self.reset()

        print("\n" + "=" * 60)
        print(" BB84 RECEIVER (BOB)")
        print("=" * 60)

        self.audit.log(
            "BB84_RECEIVER_START",
            "Waiting for qubits",
            "QUANTUM"
        )

        with CQCConnection("Bob") as Bob:

            for i in range(BB84_NUM_QUBITS):

                # -----------------------------------------
                # RANDOM BASIS
                # -----------------------------------------

                basis = self.random_basis()

                self.bob_bases.append(basis)

                # -----------------------------------------
                # RECEIVE
                # -----------------------------------------

                q = self.receive_qubit(
                    Bob,
                    i
                )

                # -----------------------------------------
                # MEASURE
                # -----------------------------------------

                result = self.measure_qubit(
                    q,
                    basis
                )

                self.bob_results.append(result)

                self.received_qubits += 1

                # -----------------------------------------
                # AUDIT
                # -----------------------------------------

                self.audit.qubit_received(
                    "Alice",
                    basis
                )

                # -----------------------------------------
                # DEBUG
                # -----------------------------------------

                print(
                    f"[BOB] Qubit {i} | "
                    f"basis={basis} "
                    f"result={result}"
                )

                # -----------------------------------------
                # BACKEND STABILITY
                # -----------------------------------------

                time.sleep(0.05)

        # =================================================
        # COMPLETE
        # =================================================

        self.audit.log(
            "BB84_RECEIVER_COMPLETE",
            f"received={self.received_qubits}",
            "QUANTUM"
        )

        print("\nReception Complete")
        print(f"Received Qubits: {self.received_qubits}")

        return {
            "bases": self.bob_bases,
            "results": self.bob_results,
            "count": self.received_qubits
        }

    # =====================================================
    # RAW KEY
    # =====================================================

    def raw_key(self):

        return "".join(
            str(bit)
            for bit in self.bob_results
        )

    # =====================================================
    # BASIS RECONCILIATION
    # =====================================================

    def reconcile(self, alice_bases):

        """
        Keep only matching basis positions.
        """

        sifted_key = []

        for i in range(
            min(
                len(alice_bases),
                len(self.bob_bases)
            )
        ):

            if alice_bases[i] == self.bob_bases[i]:

                sifted_key.append(
                    self.bob_results[i]
                )

                self.audit.basis_match(i)

            else:

                self.audit.basis_mismatch(i)

        return sifted_key

    # =====================================================
    # QBER
    # =====================================================

    def calculate_qber(
        self,
        alice_bits,
        alice_bases
    ):

        compared = 0
        errors = 0

        for i in range(
            min(
                len(alice_bits),
                len(self.bob_results)
            )
        ):

            if alice_bases[i] == self.bob_bases[i]:

                compared += 1

                if alice_bits[i] != self.bob_results[i]:
                    errors += 1

        if compared == 0:
            return 1.0

        qber = errors / compared

        if qber > 0.15:

            self.audit.qber_alert(qber)

        return qber

    # =====================================================
    # DEBUG DUMP
    # =====================================================

    def debug_dump(self):

        return {
            "bob_bases": self.bob_bases,
            "bob_results": self.bob_results,
            "received_qubits": self.received_qubits,
            "protocol": QKD_PROTOCOL
        }


# =========================================================
# STANDALONE EXECUTION
# =========================================================

if __name__ == "__main__":

    receiver = BB84Receiver()

    results = receiver.run()

    print("\nRaw Receiver Key:")
    print(receiver.raw_key())