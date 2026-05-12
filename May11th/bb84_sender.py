# bb84_sender.py
# QUANTUM LAYER - ALICE (SENDER)

from cqc.pythonLib import CQCConnection, qubit
from cqc.pythonLib.util import CQCNoQubitError

import random
import time

from audit import AuditLogger
from config import BB84_NUM_QUBITS, SIMULAQRON_ENABLED, QKD_PROTOCOL


class BB84Sender:

    """
    BB84 Quantum Sender (Alice)

    Responsibilities
    ----------------
    - Generate random bits
    - Generate random bases
    - Encode qubits
    - Send qubits via quantum channel
    - Produce raw quantum key
    """

    def __init__(self):

        self.audit = AuditLogger()

        self.alice_bits = []
        self.alice_bases = []

        self.sent_qubits = 0

    # =====================================================
    # RESET SESSION
    # =====================================================

    def reset(self):

        self.alice_bits.clear()
        self.alice_bases.clear()

        self.sent_qubits = 0

    # =====================================================
    # RANDOM BIT
    # =====================================================

    def random_bit(self):

        return random.randint(0, 1)

    # =====================================================
    # RANDOM BASIS
    # =====================================================

    def random_basis(self):

        return random.randint(0, 1)

    # =====================================================
    # ENCODE QUBIT
    # =====================================================

    def encode_qubit(
        self,
        connection,
        bit,
        basis
    ):

        """
        Basis 0 -> Z basis
        Basis 1 -> X basis
        """

        q = qubit(connection)

        # -----------------------------------------
        # BIT ENCODING
        # -----------------------------------------

        if bit == 1:
            q.X()

        # -----------------------------------------
        # BASIS ENCODING
        # -----------------------------------------

        if basis == 1:
            q.H()

        return q

    # =====================================================
    # SEND SINGLE QUBIT
    # =====================================================

    def send_single_qubit(
        self,
        connection,
        receiver_name,
        bit,
        basis
    ):

        """
        SimulaQron-safe sender.
        """

        while True:

            try:

                q = self.encode_qubit(
                    connection,
                    bit,
                    basis
                )

                connection.sendQubit(
                    q,
                    receiver_name
                )

                self.sent_qubits += 1

                return

            except CQCNoQubitError:

                print(
                    "[ALICE] "
                    "No qubits available, retrying..."
                )

                time.sleep(1)

            except Exception as e:

                print(
                    f"[ALICE] Send error: {e}"
                )

                time.sleep(1)

    # =====================================================
    # RUN TRANSMISSION
    # =====================================================

    def run(self, receiver_name="Bob"):

        self.reset()

        print("\n" + "=" * 60)
        print(" BB84 SENDER (ALICE)")
        print("=" * 60)

        self.audit.log(
            "BB84_SENDER_START",
            f"receiver={receiver_name}",
            "QUANTUM"
        )

        with CQCConnection("Alice") as Alice:

            for i in range(BB84_NUM_QUBITS):

                # -----------------------------------------
                # RANDOM VALUES
                # -----------------------------------------

                bit = self.random_bit()
                basis = self.random_basis()

                # -----------------------------------------
                # STORE
                # -----------------------------------------

                self.alice_bits.append(bit)
                self.alice_bases.append(basis)

                # -----------------------------------------
                # SEND
                # -----------------------------------------

                self.send_single_qubit(
                    Alice,
                    receiver_name,
                    bit,
                    basis
                )

                # -----------------------------------------
                # AUDIT
                # -----------------------------------------

                self.audit.qubit_sent(
                    receiver_name,
                    basis
                )

                # -----------------------------------------
                # DEBUG
                # -----------------------------------------

                print(
                    f"[ALICE] Qubit {i} | "
                    f"bit={bit} "
                    f"basis={basis}"
                )

                # -----------------------------------------
                # BACKEND STABILITY
                # -----------------------------------------

                time.sleep(0.05)

        # =================================================
        # COMPLETE
        # =================================================

        self.audit.log(
            "BB84_SENDER_COMPLETE",
            f"sent={self.sent_qubits}",
            "QUANTUM"
        )

        print("\nTransmission Complete")
        print(f"Sent Qubits: {self.sent_qubits}")

        return {
            "bits": self.alice_bits,
            "bases": self.alice_bases,
            "count": self.sent_qubits
        }

    # =====================================================
    # RAW KEY
    # =====================================================

    def raw_key(self):

        return "".join(
            str(bit)
            for bit in self.alice_bits
        )

    # =====================================================
    # DEBUG DUMP
    # =====================================================

    def debug_dump(self):

        return {
            "alice_bits": self.alice_bits,
            "alice_bases": self.alice_bases,
            "sent_qubits": self.sent_qubits,
            "protocol": QKD_PROTOCOL
        }


# =========================================================
# STANDALONE EXECUTION
# =========================================================

if __name__ == "__main__":

    sender = BB84Sender()

    results = sender.run()

    print("\nRaw Sender Key:")
    print(sender.raw_key())