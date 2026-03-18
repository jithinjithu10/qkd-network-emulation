# application/data_channel.py

import time

from qkd_research_platform_v1.application.application_layer import QKDApplicationClient
from qkd_research_platform_v1.application.secure_transfer import SecureTransfer
from qkd_research_platform_v1.config import REKEY_THRESHOLD


class SecureQKDChannel:

    def __init__(self):

        print("\n=== Initializing SecureQKDChannel ===")

        # Two logical application endpoints
        self.sender = QKDApplicationClient()
        self.receiver = QKDApplicationClient()

        # Shared session
        self.session_id = None

        # Transfer state
        self.current_cipher = None
        self.bytes_transferred = 0
        self.rekey_count = 0

        # Metrics
        self.transfer_latencies = []
        self.total_messages = 0

        print("SecureQKDChannel initialized successfully")


    # =================================================
    # Establish QKD Session
    # =================================================
    def establish_session(self):

        print("\n=== ESTABLISHING QKD SESSION ===")

        self.session_id = self.sender.create_session()
        self.receiver.session_id = self.session_id

        print("Session ID:", self.session_id)

        key_id = self.sender.request_key(role="ENC")

        if not key_id:
            print("ERROR: Failed to obtain key during session establishment")
            raise Exception("Failed to establish QKD session")

        print("Initial key obtained:", key_id)

        # Use key_id as symmetric shared key
        self.current_cipher = SecureTransfer(key_id)

        print("Cipher initialized successfully")

        return key_id


    # =================================================
    # Send Secure Message
    # =================================================
    def send(self, plaintext: bytes):

        if not self.current_cipher:
            raise Exception("Session not established")

        print("\n=== SENDING MESSAGE ===")
        print("Message size:", len(plaintext))

        start_time = time.time()

        # Encrypt
        ciphertext = self.current_cipher.encrypt(plaintext)
        print("Encryption complete")

        # Simulated transfer (loopback)
        decrypted = self.current_cipher.decrypt(ciphertext)
        print("Decryption complete")

        end_time = time.time()

        if decrypted != plaintext:
            print("ERROR: Decryption mismatch")
            raise Exception("Decryption mismatch")

        # Metrics
        latency = end_time - start_time
        self.transfer_latencies.append(latency)
        self.total_messages += 1

        self.bytes_transferred += len(plaintext)

        print("Message latency:", latency)
        print("Total bytes transferred:", self.bytes_transferred)

        # Rekey if threshold reached
        if self.bytes_transferred >= REKEY_THRESHOLD:
            print("Rekey threshold reached. Initiating rekey...")
            self._rekey()

        return {
            "latency": latency,
            "bytes": len(plaintext),
            "rekeys": self.rekey_count
        }


    # =================================================
    # Rekey Logic
    # =================================================
    def _rekey(self):

        print("\n=== REKEYING SESSION ===")

        self.sender.request_key(role="ENC")

        new_key_id = self.sender.current_key_id

        if not new_key_id:
            print("WARNING: Rekey failed (no key returned)")
            return

        print("New key obtained:", new_key_id)

        self.current_cipher = SecureTransfer(new_key_id)

        self.bytes_transferred = 0
        self.rekey_count += 1

        print("Rekey successful. Total rekeys:", self.rekey_count)


    # =================================================
    # Channel Metrics
    # =================================================
    def get_metrics(self):

        avg_latency = (
            sum(self.transfer_latencies) / len(self.transfer_latencies)
            if self.transfer_latencies else 0
        )

        metrics = {
            "total_messages": self.total_messages,
            "total_bytes": self.bytes_transferred,
            "average_latency": avg_latency,
            "rekey_count": self.rekey_count
        }

        print("\n=== CHANNEL METRICS ===")
        print(metrics)

        return metrics