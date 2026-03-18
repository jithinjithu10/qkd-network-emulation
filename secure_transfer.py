"""
secure_transfer.py

FINAL VERSION (SESSION + SYNC + ETSI CORRECT)

This is the core integration layer.
"""

import requests
import hashlib
import uuid

from crypto_engine import CryptoEngine
from audit import AuditLogger

from config import SYSTEM_MODE, SYNC_SEED


class SecureTransfer:

    def __init__(self, kms_url, token):

        self.kms_url = kms_url
        self.token = token

        self.audit = AuditLogger()

    # =================================================
    # GET KEY VIA SESSION (ETSI MODE)
    # =================================================

    def reserve_key(self):

        session_id = str(uuid.uuid4())

        response = requests.post(
            f"{self.kms_url}/etsi/v2/reserve",
            params={"session_id": session_id},
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        if response.status_code != 200:
            raise Exception("Failed to reserve key")

        data = response.json()

        self.audit.session_created(session_id)
        self.audit.session_key_mapping(session_id, data["key_ID"])

        return session_id, data["key_ID"]

    # =================================================
    # FETCH RESERVED KEY
    # =================================================

    def get_reserved_key(self, session_id):

        response = requests.get(
            f"{self.kms_url}/etsi/v2/reserved/{session_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        if response.status_code != 200:
            raise Exception("Failed to fetch reserved key")

        return response.json()

    # =================================================
    # SYNC KEY GENERATION
    # =================================================

    def generate_sync_key(self, key_id):

        index = int(key_id.split("-")[1])

        key_value = hashlib.sha256(
            f"{SYNC_SEED}-{index}".encode()
        ).hexdigest()

        return key_value

    # =================================================
    # SEND MESSAGE
    # =================================================

    def send_secure_message(self, message):

        # -----------------------------------------
        # SYNC MODE
        # -----------------------------------------
        if SYSTEM_MODE == "SYNC":

            key_id = "sync-0"  # simple demo (aligned with buffer)

            key_hex = self.generate_sync_key(key_id)

            crypto = CryptoEngine(
                key_hex,
                key_id=key_id,
                mode="SYNC"
            )

            iv, ciphertext, tag = crypto.encrypt(message)

            return key_id, iv, ciphertext, tag

        # -----------------------------------------
        # ETSI MODE (SESSION-BASED)
        # -----------------------------------------

        session_id, key_id = self.reserve_key()

        key_data = self.get_reserved_key(session_id)

        key_hex = key_data["key"]

        crypto = CryptoEngine(
            key_hex,
            key_id=key_id,
            mode="ETSI"
        )

        iv, ciphertext, tag = crypto.encrypt(message)

        return session_id, iv, ciphertext, tag

    # =================================================
    # RECEIVE MESSAGE
    # =================================================

    def receive_secure_message(self, session_id, iv, ciphertext, tag):

        # -----------------------------------------
        # SYNC MODE
        # -----------------------------------------
        if SYSTEM_MODE == "SYNC":

            key_hex = self.generate_sync_key(session_id)

            crypto = CryptoEngine(
                key_hex,
                key_id=session_id,
                mode="SYNC"
            )

            plaintext = crypto.decrypt(iv, ciphertext, tag)

            return plaintext.decode()

        # -----------------------------------------
        # ETSI MODE
        # -----------------------------------------

        key_data = self.get_reserved_key(session_id)

        key_hex = key_data["key"]

        crypto = CryptoEngine(
            key_hex,
            key_id=session_id,
            mode="ETSI"
        )

        plaintext = crypto.decrypt(iv, ciphertext, tag)

        return plaintext.decode()