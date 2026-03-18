"""
secure_transfer.py

Implements secure message transfer using
QKD keys retrieved from ETSI KMS.
"""

import requests
from crypto_engine import CryptoEngine


class SecureTransfer:

    def __init__(self, kms_url, token):

        self.kms_url = kms_url
        self.token = token

    # =================================================
    # GET QKD KEY FROM KMS
    # =================================================

    def get_qkd_key(self):

        response = requests.post(
            f"{self.kms_url}/etsi/v2/keys",
            headers={
                "Authorization": f"Bearer {self.token}"
            },
            timeout=5
        )

        if response.status_code != 200:
            raise Exception("Failed to retrieve key")

        data = response.json()

        return data["key"]

    # =================================================
    # SEND SECURE MESSAGE
    # =================================================

    def send_secure_message(self, message):

        key = self.get_qkd_key()

        crypto = CryptoEngine(key)

        iv, ciphertext = crypto.encrypt(message)

        return key, iv, ciphertext

    # =================================================
    # RECEIVE MESSAGE
    # =================================================

    def receive_secure_message(self, key, iv, ciphertext):

        crypto = CryptoEngine(key)

        plaintext = crypto.decrypt(iv, ciphertext)

        return plaintext