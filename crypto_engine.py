"""
crypto_engine.py (UPDATED - RESEARCH LEVEL)

Fixes:
- AES-256 GCM (correct)
- Real authentication tag
- Data-per-key tracking
- Strong audit logging
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from audit import AuditLogger

import os


class CryptoEngine:

    def __init__(self, key_hex: str, key_id: str, mode: str = "ETSI"):
        """
        AES-256-GCM engine
        """

        if not key_id:
            raise ValueError("key_id required")

        self.key = bytes.fromhex(key_hex)
        self.key_id = key_id
        self.mode = mode

        self.audit = AuditLogger()

        if len(self.key) != 32:
            raise ValueError("AES-256 requires 32 bytes")

        self.aesgcm = AESGCM(self.key)

    # =================================================
    # ENCRYPT
    # =================================================

    def encrypt(self, data: bytes):

        if isinstance(data, str):
            data = data.encode()

        # GCM nonce (12 bytes recommended)
        iv = os.urandom(12)

        ciphertext = self.aesgcm.encrypt(iv, data, None)

        # split tag (last 16 bytes)
        tag = ciphertext[-16:]
        actual_ciphertext = ciphertext[:-16]

        self.audit.encryption(
            key_id=self.key_id,
            bytes_used=len(data),
            mode=self.mode
        )

        return iv, actual_ciphertext, tag

    # =================================================
    # DECRYPT
    # =================================================

    def decrypt(self, iv, ciphertext, tag):

        if len(iv) != 12:
            raise ValueError("Invalid IV (GCM requires 12 bytes)")

        # reconstruct full ciphertext
        full_ct = ciphertext + tag

        plaintext = self.aesgcm.decrypt(iv, full_ct, None)

        self.audit.decryption(
            key_id=self.key_id,
            bytes_used=len(plaintext),
            mode=self.mode
        )

        return plaintext