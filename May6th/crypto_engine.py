# crypto_engine.py (FINAL STABLE VERSION)

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from audit import AuditLogger
from config import MAX_BYTES_PER_KEY

import os


class CryptoEngine:

    def __init__(self, key_hex: str, key_id: str, mode: str = "ETSI"):

        if not key_id:
            raise ValueError("key_id required")

        if not key_hex:
            raise ValueError("key_hex required")

        try:
            self.key = bytes.fromhex(key_hex)
        except Exception:
            raise ValueError("Invalid key_hex format")

        if len(self.key) != 32:
            raise ValueError("AES-256 requires 32-byte key")

        self.key_id = str(key_id)

        # Validate mode
        if mode not in ("ETSI", "SYNC"):
            raise ValueError("Invalid mode (must be ETSI or SYNC)")
        self.mode = mode

        self.audit = AuditLogger()

        # Local tracking (fallback only)
        self.bytes_used = 0

        self.aesgcm = AESGCM(self.key)

    # =================================================
    # ENCRYPT
    # =================================================
    def encrypt(self, data: bytes):

        if isinstance(data, str):
            data = data.encode()

        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("Data must be bytes or string")

        # Usage limit check (local fallback)
        if self.bytes_used + len(data) > MAX_BYTES_PER_KEY:
            self.audit.key_limit_reached(self.key_id)
            raise ValueError("Key usage limit exceeded")

        # Generate IV
        iv = os.urandom(12)

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
    def decrypt(self, iv: bytes, ciphertext: bytes, tag: bytes):

        if not isinstance(iv, (bytes, bytearray)) or len(iv) != 12:
            raise ValueError("Invalid IV (must be 12 bytes)")

        if not isinstance(ciphertext, (bytes, bytearray)):
            raise ValueError("Invalid ciphertext")

        if not isinstance(tag, (bytes, bytearray)) or len(tag) != 16:
            raise ValueError("Invalid tag (must be 16 bytes)")

        full_ct = ciphertext + tag

        aad = self.key_id.encode()

        try:
            plaintext = self.aesgcm.decrypt(iv, full_ct, aad)

        except Exception as e:
            self.audit.error(
                f"Decryption failed for key_id={self.key_id}: {str(e)}"
            )
            raise ValueError("Decryption failed (authentication error)")

        self.audit.decryption(
            key_id=self.key_id,
            bytes_used=len(plaintext),
            mode=self.mode
        )

        return plaintext