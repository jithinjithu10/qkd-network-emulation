# secure_transfer.py
"""
Research-Grade Secure Transfer Layer
Debug Instrumented Version
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import time
import random
import hashlib


class SecureTransfer:

    def __init__(self, key_hex, rekey_threshold=100_000):

        print("\n=== SecureTransfer Initialization ===")
        print("Input key_hex:", key_hex)

        # --------------------------------------------------
        # SAFETY FIX:
        # UUID is not valid hex key → hash it to 32 bytes
        # --------------------------------------------------
        if "-" in key_hex:
            print("Key appears to be UUID. Hashing to derive AES key.")
            derived = hashlib.sha256(key_hex.encode()).digest()
            self.master_key = derived
        else:
            self.master_key = bytes.fromhex(key_hex)[:32]

        print("Derived key length:", len(self.master_key))

        self.current_key = self.master_key

        self.rekey_threshold = rekey_threshold
        self.bytes_transferred = 0
        self.rekey_count = 0

        # Metrics
        self.metrics = {
            "bytes_transferred": 0,
            "encryption_time": 0,
            "decryption_time": 0,
            "rekey_count": 0,
            "throughput_mbps": 0
        }

        print("SecureTransfer initialized successfully")


    # =================================================
    # AES-GCM ENCRYPTION
    # =================================================
    def encrypt(self, plaintext: bytes):

        print("\nEncrypting message of size:", len(plaintext))

        start = time.time()

        aesgcm = AESGCM(self.current_key)
        nonce = os.urandom(12)

        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        elapsed = time.time() - start

        print("Encryption time:", elapsed)

        self._update_metrics(len(plaintext), elapsed)
        self._check_rekey()

        return nonce + ciphertext


    # =================================================
    # AES-GCM DECRYPTION
    # =================================================
    def decrypt(self, data: bytes):

        print("Decrypting message")

        start = time.time()

        nonce = data[:12]
        ciphertext = data[12:]

        aesgcm = AESGCM(self.current_key)

        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        elapsed = time.time() - start

        print("Decryption time:", elapsed)

        self.metrics["decryption_time"] += elapsed

        return plaintext


    # =================================================
    # ATTACK SIMULATION
    # =================================================
    def inject_bit_flip(self, ciphertext: bytes, probability=0.01):

        print("Injecting bit flips with probability:", probability)

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

            print("Rekey threshold reached. Generating new key.")

            self.current_key = os.urandom(32)
            self.bytes_transferred = 0
            self.rekey_count += 1

            self.metrics["rekey_count"] += 1


    # =================================================
    # METRICS EXPORT
    # =================================================
    def get_metrics(self):
        return self.metrics