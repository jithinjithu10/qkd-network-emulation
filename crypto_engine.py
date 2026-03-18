"""
crypto_engine.py

FINAL VERSION (ETSI + SYNC READY)

Enhancements:
- IV validation
- Optional integrity protection
- Strict key_id enforcement
- Improved audit logging
"""

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend

from config import AES_BLOCK_SIZE
from audit import AuditLogger

import os
import hashlib


class CryptoEngine:

    def __init__(self, key_hex: str, key_id: str, mode: str = "ETSI"):
        """
        Initialize AES-256 engine using QKD key.
        """

        if not key_id:
            raise ValueError("key_id is required for audit tracking")

        self.key = bytes.fromhex(key_hex)
        self.key_id = key_id
        self.mode = mode

        self.audit = AuditLogger()

        # Validate key length (256-bit)
        if len(self.key) != 32:
            raise ValueError("Invalid key size: AES-256 requires 32 bytes")

    # =================================================
    # ENCRYPT
    # =================================================

    def encrypt(self, data):
        """
        Supports:
        - string
        - bytes
        """

        if isinstance(data, str):
            data = data.encode()

        iv = os.urandom(AES_BLOCK_SIZE)

        padder = PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )

        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        #  Simple integrity tag (NOT full MAC, but useful for demo)
        tag = hashlib.sha256(iv + ciphertext).digest()[:16]

        self.audit.encryption(self.key_id, mode=self.mode)

        return iv, ciphertext, tag

    # =================================================
    # DECRYPT
    # =================================================

    def decrypt(self, iv, ciphertext, tag=None):

        #  Validate IV length
        if len(iv) != AES_BLOCK_SIZE:
            raise ValueError("Invalid IV size")

        #  Validate integrity (if tag provided)
        if tag:
            expected_tag = hashlib.sha256(iv + ciphertext).digest()[:16]
            if expected_tag != tag:
                raise ValueError("Integrity check failed")

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )

        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        self.audit.decryption(self.key_id, mode=self.mode)

        return plaintext