# secure_transfer.py
"""
Research-Grade Secure Transfer Layer
Week 9–10 Advanced Implementation
AES-GCM | OTP | Dynamic Re-keying | Metrics | Attack Simulation
"""

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import time
import random


class SecureTransfer:

    def __init__(self, key_hex, rekey_threshold=100_000):

        self.master_key = bytes.fromhex(key_hex)[:32]  # AES-256
        self.current_key = self.master_key

        self.rekey_threshold = rekey_threshold
        self.bytes_transferred = 0
        self.rekey_count = 0

        self.backend = default_backend()

        # Metrics
        self.metrics = {
            "bytes_transferred": 0,
            "encryption_time": 0,
            "decryption_time": 0,
            "rekey_count": 0,
            "throughput_mbps": 0
        }

    # =================================================
    # AES-GCM ENCRYPTION (Authenticated)
    # =================================================
    def encrypt_aes(self, plaintext: bytes):

        start = time.time()

        aesgcm = AESGCM(self.current_key)
        nonce = os.urandom(12)

        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        elapsed = time.time() - start

        self._update_metrics(len(plaintext), elapsed)

        self._check_rekey()

        return nonce + ciphertext

    # =================================================
    # AES-GCM DECRYPTION
    # =================================================
    def decrypt_aes(self, data: bytes):

        start = time.time()

        nonce = data[:12]
        ciphertext = data[12:]

        aesgcm = AESGCM(self.current_key)

        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        elapsed = time.time() - start
        self.metrics["decryption_time"] += elapsed

        return plaintext

    # =================================================
    # OTP MODE (True One-Time Pad Simulation)
    # =================================================
    def encrypt_otp(self, plaintext: bytes):

        if len(self.current_key) < len(plaintext):
            raise ValueError("Key too short for OTP")

        start = time.time()

        ciphertext = bytes(
            [plaintext[i] ^ self.current_key[i] for i in range(len(plaintext))]
        )

        elapsed = time.time() - start

        self._update_metrics(len(plaintext), elapsed)

        return ciphertext

    def decrypt_otp(self, ciphertext: bytes):

        return self.encrypt_otp(ciphertext)  # XOR reversible

    # =================================================
    # ATTACK SIMULATION (Bit Flip)
    # =================================================
    def inject_bit_flip(self, ciphertext: bytes, probability=0.01):

        corrupted = bytearray(ciphertext)

        for i in range(len(corrupted)):
            if random.random() < probability:
                corrupted[i] ^= 0x01

        return bytes(corrupted)

    # =================================================
    # METRICS UPDATE
    # =================================================
    def _update_metrics(self, byte_count, elapsed_time):

        self.bytes_transferred += byte_count

        self.metrics["bytes_transferred"] += byte_count
        self.metrics["encryption_time"] += elapsed_time

        if elapsed_time > 0:
            mbps = (byte_count * 8) / (elapsed_time * 1_000_000)
            self.metrics["throughput_mbps"] = mbps

    # =================================================
    # DYNAMIC REKEYING
    # =================================================
    def _check_rekey(self):

        if self.bytes_transferred >= self.rekey_threshold:

            self.current_key = os.urandom(32)
            self.bytes_transferred = 0
            self.rekey_count += 1

            self.metrics["rekey_count"] += 1

    # =================================================
    # METRICS EXPORT
    # =================================================
    def get_metrics(self):
        return self.metrics