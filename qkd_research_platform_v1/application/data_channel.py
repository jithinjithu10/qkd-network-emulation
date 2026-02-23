# application/data_channel.py

import time
from application_layer import QKDApplicationClient
from secure_transfer import SecureTransfer
from config import REKEY_THRESHOLD


class SecureQKDChannel:

    def __init__(self):

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


    # =================================================
    # Establish QKD Session
    # =================================================
    def establish_session(self):

        self.session_id = self.sender.create_session()
        self.receiver.session_id = self.session_id

        key_id = self.sender.request_key(role="ENC")

        if not key_id:
            raise Exception("Failed to establish QKD session")

        # Use key_id as symmetric shared key
        self.current_cipher = SecureTransfer(key_id)

        return key_id


    # =================================================
    # Send Secure Message
    # =================================================
    def send(self, plaintext: bytes):

        if not self.current_cipher:
            raise Exception("Session not established")

        start_time = time.time()

        # Encrypt
        ciphertext = self.current_cipher.encrypt(plaintext)

        # Simulated transfer delay
        decrypted = self.current_cipher.decrypt(ciphertext)

        end_time = time.time()

        if decrypted != plaintext:
            raise Exception("Decryption mismatch")

        # Metrics
        latency = end_time - start_time
        self.transfer_latencies.append(latency)
        self.total_messages += 1

        self.bytes_transferred += len(plaintext)

        # Rekey if threshold reached
        if self.bytes_transferred >= REKEY_THRESHOLD:
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

        self.sender.request_key(role="ENC")

        new_key_id = self.sender.current_key_id

        if not new_key_id:
            return

        self.current_cipher = SecureTransfer(new_key_id)

        self.bytes_transferred = 0
        self.rekey_count += 1


    # =================================================
    # Channel Metrics
    # =================================================
    def get_metrics(self):

        avg_latency = (
            sum(self.transfer_latencies) / len(self.transfer_latencies)
            if self.transfer_latencies else 0
        )

        return {
            "total_messages": self.total_messages,
            "total_bytes": self.bytes_transferred,
            "average_latency": avg_latency,
            "rekey_count": self.rekey_count
        }