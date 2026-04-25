# crypto_engine.py
# Purpose:
# Handles encryption and decryption using AES-256-GCM.
# Ensures:
# - Authenticated encryption
# - Key usage limits
# - Binding of key_id using AAD
#
# NOTE:
# No IP or network changes required in this file.


from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from audit import AuditLogger
from config import MAX_BYTES_PER_KEY

import os


class CryptoEngine:

    def __init__(self, key_hex: str, key_id: str, mode: str = "ETSI"):
        """
        Initialize crypto engine with:
        - key_hex: 64 hex chars (32 bytes)
        - key_id: identifier used for AAD binding
        - mode: ETSI or SYNC
        """

        # Validate inputs
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
        self.mode = mode

        self.audit = AuditLogger()

        # Track total bytes encrypted with this key
        self.bytes_used = 0

        # AES-GCM instance
        self.aesgcm = AESGCM(self.key)

    # =================================================
    # ENCRYPT
    # =================================================
    def encrypt(self, data: bytes):
        """
        Encrypt data using AES-256-GCM.

        Returns:
        - iv (12 bytes)
        - ciphertext
        - tag (16 bytes)
        """

        # Allow string input
        if isinstance(data, str):
            data = data.encode()

        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("Data must be bytes or string")

        # -------------------------------
        # DATA LIMIT CHECK (CRITICAL)
        # -------------------------------
        if self.bytes_used + len(data) > MAX_BYTES_PER_KEY:
            self.audit.key_limit_reached(self.key_id)
            raise ValueError("Key usage limit exceeded")

        # Generate secure random IV (12 bytes recommended for GCM)
        iv = os.urandom(12)

        # AAD binds key_id → prevents key misuse across sessions
        aad = self.key_id.encode()

        # Encrypt (returns ciphertext + tag combined)
        full_cipher = self.aesgcm.encrypt(iv, data, aad)

        # Split ciphertext and tag
        tag = full_cipher[-16:]
        ciphertext = full_cipher[:-16]

        # Update usage
        self.bytes_used += len(data)

        # Audit log
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
        """
        Decrypt AES-GCM encrypted data.

        Requires:
        - Same key
        - Same key_id (AAD)
        - Correct IV and tag
        """

        # Validate IV
        if not isinstance(iv, (bytes, bytearray)) or len(iv) != 12:
            raise ValueError("Invalid IV (must be 12 bytes)")

        if not isinstance(ciphertext, (bytes, bytearray)):
            raise ValueError("Invalid ciphertext")

        if not isinstance(tag, (bytes, bytearray)) or len(tag) != 16:
            raise ValueError("Invalid tag (must be 16 bytes)")

        # Reconstruct full ciphertext
        full_ct = ciphertext + tag

        # Same AAD must be used
        aad = self.key_id.encode()

        try:
            plaintext = self.aesgcm.decrypt(iv, full_ct, aad)

        except Exception:
            # Authentication failure (tampering or wrong key)
            self.audit.error(f"Decryption failed for key_id={self.key_id}")
            raise ValueError("Decryption failed (authentication error)")

        # Audit log
        self.audit.decryption(
            key_id=self.key_id,
            bytes_used=len(plaintext),
            mode=self.mode
        )

        return plaintext