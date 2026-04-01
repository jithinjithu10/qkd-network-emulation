# secure_transfer.py (FINAL - WITH ACK SUPPORT)

import requests
import hashlib

from crypto_engine import CryptoEngine
from audit import AuditLogger
from config import SYSTEM_MODE, SYNC_SEED, NODE_ID


class SecureTransfer:

    def __init__(self, kms_url, token):

        self.kms_url = kms_url
        self.token = token

        self.audit = AuditLogger()

        # simple counter for SYNC mode
        self.sync_counter = 0

    # =================================================
    # GET NEW KEY (ETSI)
    # =================================================

    def get_key(self):

        try:
            response = requests.post(
                f"{self.kms_url}/etsi/v2/keys",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )

            response.raise_for_status()

        except Exception as e:
            self.audit.error(f"KMS key fetch failed: {str(e)}")
            raise Exception("Failed to get key from KMS")

        data = response.json()

        key_id = data.get("key_id")
        key = data.get("key")

        if not key_id or not key:
            raise ValueError("Invalid key response")

        return key_id, key

    # =================================================
    # GET KEY BY ID
    # =================================================

    def get_key_by_id(self, key_id):

        try:
            response = requests.get(
                f"{self.kms_url}/etsi/v2/keys/{key_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )

            response.raise_for_status()

        except Exception as e:
            self.audit.error(f"KMS fetch failed for id={key_id}: {str(e)}")
            raise Exception("Failed to fetch key")

        data = response.json()

        key = data.get("key")

        if not key:
            raise ValueError("Invalid key response")

        return key

    # =================================================
    # SYNC KEY GENERATION
    # =================================================

    def generate_sync_key(self, key_id):

        index = int(key_id)

        return hashlib.sha256(
            f"{SYNC_SEED}-{index}".encode()
        ).hexdigest()

    # =================================================
    # SEND ACK (NEW)
    # =================================================

    def send_ack(self, key_id):

        try:
            requests.post(
                f"{self.kms_url}/interkms/v1/ack",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "key_id": key_id,
                    "node": NODE_ID
                },
                timeout=3
            )
        except Exception:
            # ACK failure should not break flow
            self.audit.error(f"ACK failed for key_id={key_id}")

    # =================================================
    # SEND MESSAGE
    # =================================================

    def send_secure_message(self, message):

        # -----------------------------
        # SYNC MODE
        # -----------------------------
        if SYSTEM_MODE == "SYNC":

            key_id = str(self.sync_counter)

            key_hex = self.generate_sync_key(key_id)

            self.sync_counter += 1

            crypto = CryptoEngine(
                key_hex,
                key_id=key_id,
                mode="SYNC"
            )

            iv, ciphertext, tag = crypto.encrypt(message)

            self.audit.encrypt(key_id, len(message))

            #  SEND ACK
            self.send_ack(key_id)

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

        self.audit.encrypt(key_id, len(message))

        #  SEND ACK
        self.send_ack(key_id)

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

        self.audit.decrypt(key_id, len(plaintext))

        #  SEND ACK
        self.send_ack(key_id)

        return plaintext.decode()