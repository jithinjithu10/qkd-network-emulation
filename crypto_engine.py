# crypto_engine.py (FINAL - SECURE + SYNC SAFE)

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from audit import AuditLogger
from config import MAX_BYTES_PER_KEY

import os


class CryptoEngine:

    def __init__(self, key_hex: str, key_id: str, mode: str = "ETSI"):

        if not key_id:
            raise ValueError("key_id required")

        self.key = bytes.fromhex(key_hex)
        self.key_id = key_id
        self.mode = mode

        self.audit = AuditLogger()

        # track usage
        self.bytes_used = 0

        if len(self.key) != 32:
            raise ValueError("AES-256 requires 32 bytes")

        self.aesgcm = AESGCM(self.key)

    # =================================================
    # ENCRYPT
    # =================================================

    def encrypt(self, data: bytes):

        if isinstance(data, str):
            data = data.encode()

        # -------------------------------
        # DATA LIMIT CHECK (IMPORTANT)
        # -------------------------------
        if self.bytes_used + len(data) > MAX_BYTES_PER_KEY:
            self.audit.key_limit_reached(self.key_id)
            raise ValueError("Key usage limit exceeded")

        iv = os.urandom(12)

        # AAD binds key_id → prevents misuse
        aad = self.key_id.encode()

        full_cipher = self.aesgcm.encrypt(iv, data, aad)

        tag = full_cipher[-16:]
        ciphertext = full_cipher[:-16]

        self.bytes_used += len(data)

        self.audit.encryption(
            key_id=self.key_id,
            bytes_used=self.bytes_used,
            mode=self.mode
        )

        return iv, ciphertext, tag

    # =================================================
    # DECRYPT
    # =================================================

    def decrypt(self, iv, ciphertext, tag):

        if len(iv) != 12:
            raise ValueError("Invalid IV (must be 12 bytes)")

        full_ct = ciphertext + tag

        # same AAD used
        aad = self.key_id.encode()

        try:
            plaintext = self.aesgcm.decrypt(iv, full_ct, aad)

        except Exception:
            self.audit.error(f"Decryption failed for key_id={self.key_id}")
            raise ValueError("Decryption failed (auth error)")

        self.audit.decryption(
            key_id=self.key_id,
            bytes_used=len(plaintext),
            mode=self.mode
        )

        return plaintext