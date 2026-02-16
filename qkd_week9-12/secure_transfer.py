# secure_transfer.py

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os


class SecureTransfer:

    def __init__(self, key_hex):
        self.key = bytes.fromhex(key_hex)[:32]  # AES-256
        self.backend = default_backend()

    def encrypt(self, plaintext: bytes):

        iv = os.urandom(16)

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CFB(iv),
            backend=self.backend
        )

        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        return iv + ciphertext

    def decrypt(self, ciphertext: bytes):

        iv = ciphertext[:16]
        actual_ciphertext = ciphertext[16:]

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CFB(iv),
            backend=self.backend
        )

        decryptor = cipher.decryptor()
        return decryptor.update(actual_ciphertext) + decryptor.finalize()
