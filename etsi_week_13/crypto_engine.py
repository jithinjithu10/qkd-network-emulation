"""
crypto_engine.py

Implements encryption and decryption using
QKD-generated keys.

Uses AES-256 for secure data transmission.
"""

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
import os


class CryptoEngine:

    def __init__(self, key_hex: str):
        """
        Initialize AES-256 engine using QKD key.
        """

        self.key = bytes.fromhex(key_hex)

    # =================================================
    # ENCRYPT
    # =================================================

    def encrypt(self, plaintext: str):

        iv = os.urandom(16)

        padder = PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )

        encryptor = cipher.encryptor()

        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return iv, ciphertext

    # =================================================
    # DECRYPT
    # =================================================

    def decrypt(self, iv, ciphertext):

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )

        decryptor = cipher.decryptor()

        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = PKCS7(128).unpadder()

        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext.decode()