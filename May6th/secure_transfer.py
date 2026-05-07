# secure_transfer.py
# FINAL PRODUCTION VERSION (NGROK SAFE - NETWORK FIXED)

import requests
import hashlib

from crypto_engine import CryptoEngine
from audit import AuditLogger
from config import SYSTEM_MODE, SYNC_SEED, NODE_ID, NODE_SHARED_SECRET


class SecureTransfer:

    def __init__(self, kms_url, token):

        # 🔧 FIX: sanitize URL (important for ngrok)
        self.kms_url = kms_url.rstrip("/")
        self.token = token

        self.audit = AuditLogger()

        # fallback counter for SYNC mode
        self.sync_counter = 0

        # 🔧 Central headers
        self.auth_headers = {
            "Authorization": f"Bearer {self.token}"
        }

        self.interkms_headers = {
            "Authorization": f"Bearer {NODE_SHARED_SECRET}"
        }


    # =================================================
    # GET NEXT KEY (ETSI MODE - NON-DESTRUCTIVE)
    # =================================================
    def get_key(self):

        try:
            response = requests.post(
                f"{self.kms_url}/etsi/v2/keys",
                headers=self.auth_headers,
                timeout=5
            )

            response.raise_for_status()

        except Exception as e:
            self.audit.error(f"KMS key fetch failed: {str(e)}")
            raise Exception("Failed to get key from KMS")

        data = response.json()

        key_id = data.get("key_id")
        key = data.get("key")

        if key_id is None or not key:
            raise ValueError("Invalid key response")

        return str(key_id), key


    # =================================================
    # GET KEY BY ID
    # =================================================
    def get_key_by_id(self, key_id, buffer=None):

        if buffer is not None:
            key_obj = buffer.get_key_by_id(str(key_id))

            if not key_obj:
                raise Exception(f"Key {key_id} not found locally")

            return key_obj.key_value

        try:
            response = requests.get(
                f"{self.kms_url}/etsi/v2/keys/{key_id}",
                headers=self.auth_headers,
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

        return hashlib.sha256(
            f"{SYNC_SEED}-{key_id}".encode()
        ).hexdigest()


    # =================================================
    # SEND ACK
    # =================================================
    def send_ack(self, key_id):

        try:
            requests.post(
                f"{self.kms_url}/interkms/v1/ack",
                headers=self.interkms_headers,
                json={
                    "key_id": key_id,
                    "node": NODE_ID
                },
                timeout=3
            )

        except Exception:
            self.audit.error(f"ACK failed for key_id={key_id}")


    # =================================================
    # SEND MESSAGE
    # =================================================
    def send_secure_message(self, message):

        if isinstance(message, str):
            message = message.encode()

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

            self.audit.encryption(key_id, len(message), "SYNC")
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

        self.audit.encryption(key_id, len(message), "ETSI")
        self.send_ack(key_id)

        return key_id, iv, ciphertext, tag


    # =================================================
    # RECEIVE MESSAGE
    # =================================================
    def receive_secure_message(self, key_id, iv, ciphertext, tag, buffer=None):

        if SYSTEM_MODE == "SYNC":
            key_hex = self.generate_sync_key(key_id)
        else:
            key_hex = self.get_key_by_id(key_id, buffer=buffer)

        crypto = CryptoEngine(
            key_hex,
            key_id=key_id,
            mode=SYSTEM_MODE
        )

        plaintext = crypto.decrypt(iv, ciphertext, tag)

        self.audit.decryption(key_id, len(plaintext), SYSTEM_MODE)
        self.send_ack(key_id)

        return plaintext.decode()