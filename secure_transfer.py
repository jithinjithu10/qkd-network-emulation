"""
secure_transfer.py (UPDATED - FINAL RESEARCH VERSION)

Fixes:
- Removed session system
- Uses key_id directly
- Correct ETSI flow
- AES-GCM compatible
"""

import requests
import hashlib

from crypto_engine import CryptoEngine
from audit import AuditLogger
from config import SYSTEM_MODE, SYNC_SEED


class SecureTransfer:

    def __init__(self, kms_url, token):

        self.kms_url = kms_url
        self.token = token

        self.audit = AuditLogger()

    # =================================================
    # GET NEW KEY (ETSI)
    # =================================================

    def get_key(self):

        response = requests.post(
            f"{self.kms_url}/etsi/v2/keys",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        if response.status_code != 200:
            raise Exception("Failed to get key")

        data = response.json()

        return data["key_id"], data["key"]

    # =================================================
    # GET KEY BY ID
    # =================================================

    def get_key_by_id(self, key_id):

        response = requests.get(
            f"{self.kms_url}/etsi/v2/keys/{key_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        if response.status_code != 200:
            raise Exception("Failed to fetch key")

        return response.json()["key"]

    # =================================================
    # SYNC KEY GENERATION
    # =================================================

    def generate_sync_key(self, key_id):

        index = int(key_id)   # FIXED (no "sync-")

        return hashlib.sha256(
            f"{SYNC_SEED}-{index}".encode()
        ).hexdigest()

    # =================================================
    # SEND MESSAGE
    # =================================================

    def send_secure_message(self, message):

        # -----------------------------
        # SYNC MODE
        # -----------------------------
        if SYSTEM_MODE == "SYNC":

            key_id = "0"   # demo start

            key_hex = self.generate_sync_key(key_id)

            crypto = CryptoEngine(
                key_hex,
                key_id=key_id,
                mode="SYNC"
            )

            iv, ciphertext, tag = crypto.encrypt(message)

            return key_id, iv, ciphertext, tag

        # -----------------------------
        # ETSI MODE
        # -----------------------------

        key_id, key_hex = self.get_key()

        crypto = CryptoEngine(
            key_hex,
            key_id=key_id,
            mode="ETSI"
        )

        iv, ciphertext, tag = crypto.encrypt(message)

        return key_id, iv, ciphertext, tag

    # =================================================
    # RECEIVE MESSAGE
    # =================================================

    def receive_secure_message(self, key_id, iv, ciphertext, tag):

        # -----------------------------
        # SYNC MODE
        # -----------------------------
        if SYSTEM_MODE == "SYNC":

            key_hex = self.generate_sync_key(key_id)

        # -----------------------------
        # ETSI MODE
        # -----------------------------
        else:

            key_hex = self.get_key_by_id(key_id)

        crypto = CryptoEngine(
            key_hex,
            key_id=key_id,
            mode=SYSTEM_MODE
        )

        plaintext = crypto.decrypt(iv, ciphertext, tag)

        return plaintext.decode()