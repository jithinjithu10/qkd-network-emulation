# secure_transfer.py
# ADVANCED HYBRID QUANTUM-CLASSICAL SECURE TRANSFER LAYER

import requests
import hashlib
import uuid
import time
import hmac

from crypto_engine import CryptoEngine
from audit import AuditLogger

from config import (

    SYSTEM_MODE,
    SYNC_SEED,

    NODE_ID,

    NODE_SHARED_SECRET,

    ENABLE_SHA256_SYNC,

    QKD_PROTOCOL,

    ENABLE_REPLAY_PROTECTION
)


class SecureTransfer:

    """
    Secure Communication Layer

    Responsibilities
    ----------------
    - AES-256-GCM encryption
    - BB84 synchronized key usage
    - SHA-256 synchronization verification
    - replay protection
    - metadata synchronization
    - inter-KMS verification

    IMPORTANT
    ---------
    Quantum layer generates entropy.

    This layer:
    - encrypts/decrypts
    - synchronizes metadata
    - validates integrity
    """

    def __init__(
        self,
        kms_url,
        token
    ):

        # =================================================
        # URL
        # =================================================

        self.kms_url = kms_url.rstrip("/")

        self.token = token

        self.audit = AuditLogger()

        # =================================================
        # SESSION
        # =================================================

        self.session_id = str(
            uuid.uuid4()
        )[:8]

        self.sync_counter = 0

        self.sync_index = 0

        # =================================================
        # REPLAY TRACKING
        # =================================================

        self.used_nonces = set()

        self.message_counter = 0

        # =================================================
        # AUTH
        # =================================================

        self.auth_headers = {

            "Authorization":
                f"Bearer {self.token}"
        }

        self.interkms_headers = {

            "Authorization":
                f"Bearer {NODE_SHARED_SECRET}",

            "X-Node-ID":
                NODE_ID
        }

    # =====================================================
    # SHA-256
    # =====================================================

    def sha256_hash(
        self,
        key_material
    ):

        return hashlib.sha256(

            bytes.fromhex(key_material)

        ).hexdigest()

    # =====================================================
    # CONSTANT-TIME HASH VERIFY
    # =====================================================

    def verify_hash(

        self,

        key_material,

        received_hash
    ):

        if not ENABLE_SHA256_SYNC:
            return True

        local_hash = self.sha256_hash(
            key_material
        )

        return hmac.compare_digest(

            local_hash,

            received_hash
        )

    # =====================================================
    # REPLAY CHECK
    # =====================================================

    def verify_nonce(
        self,
        nonce
    ):

        if not ENABLE_REPLAY_PROTECTION:
            return True

        if nonce in self.used_nonces:

            self.audit.error(
                f"Replay detected nonce={nonce}"
            )

            return False

        self.used_nonces.add(nonce)

        return True

    # =====================================================
    # GET KEY
    # =====================================================

    def get_key(self):

        """
        Fetch synchronized BB84-derived key.
        """

        try:

            response = requests.post(

                f"{self.kms_url}/etsi/v2/keys",

                headers=self.auth_headers,

                timeout=5
            )

            response.raise_for_status()

        except Exception as e:

            self.audit.error(

                f"KMS key fetch failed: {str(e)}"
            )

            raise Exception(
                "Failed to fetch synchronized key"
            )

        data = response.json()

        key_id = data.get("key_id")

        key = data.get("key")

        if key_id is None or not key:

            raise ValueError(
                "Invalid synchronized key response"
            )

        self.sync_index = data.get(
            "sync_index",
            0
        )

        return (

            str(key_id),

            key,

            data
        )

    # =====================================================
    # GET KEY BY ID
    # =====================================================

    def get_key_by_id(

        self,

        key_id,

        buffer=None
    ):

        # =================================================
        # LOCAL BUFFER
        # =================================================

        if buffer is not None:

            key_obj = buffer.get_key_by_id(
                str(key_id)
            )

            if not key_obj:

                raise Exception(

                    f"Key {key_id} "
                    f"not locally available"
                )

            return key_obj.key_value

        # =================================================
        # REMOTE FETCH
        # =================================================

        try:

            response = requests.get(

                f"{self.kms_url}/etsi/v2/keys/{key_id}",

                headers=self.auth_headers,

                timeout=5
            )

            response.raise_for_status()

        except Exception as e:

            self.audit.error(

                (
                    f"KMS fetch failed "
                    f"key_id={key_id}: {str(e)}"
                )
            )

            raise Exception(
                "Failed to fetch key"
            )

        data = response.json()

        key = data.get("key")

        if not key:

            raise ValueError(
                "Invalid key response"
            )

        return key

    # =====================================================
    # GET METADATA
    # =====================================================

    def get_metadata(
        self,
        key_id
    ):

        try:

            response = requests.get(

                f"{self.kms_url}/etsi/v2/metadata/{key_id}",

                headers=self.auth_headers,

                timeout=5
            )

            response.raise_for_status()

        except Exception as e:

            self.audit.error(

                (
                    f"Metadata fetch failed "
                    f"{str(e)}"
                )
            )

            return None

        return response.json()

    # =====================================================
    # LOCAL BB84 SIMULATION
    # =====================================================

    def generate_sync_key(
        self,
        key_id
    ):

        return hashlib.sha256(

            f"{SYNC_SEED}-BB84-{key_id}".encode()

        ).hexdigest()

    # =====================================================
    # SEND VERIFICATION
    # =====================================================

    def send_verification(

        self,

        key_id,

        key_hash
    ):

        try:

            requests.post(

                f"{self.kms_url}/interkms/v1/verify",

                headers=self.interkms_headers,

                json={

                    "key_id":
                        key_id,

                    "node":
                        NODE_ID,

                    "key_hash":
                        key_hash,

                    "session_id":
                        self.session_id,

                    "timestamp":
                        time.time()
                },

                timeout=5
            )

        except Exception as e:

            self.audit.error(

                (
                    f"Verification failed "
                    f"{key_id}: {str(e)}"
                )
            )

    # =====================================================
    # ACK
    # =====================================================

    def send_ack(

        self,

        key_id,

        key_hash=None
    ):

        try:

            requests.post(

                f"{self.kms_url}/interkms/v1/ack",

                headers=self.interkms_headers,

                json={

                    "key_id":
                        key_id,

                    "node":
                        NODE_ID,

                    "key_hash":
                        key_hash,

                    "session_id":
                        self.session_id,

                    "timestamp":
                        time.time()
                },

                timeout=3
            )

        except Exception:

            self.audit.error(
                f"ACK failed for {key_id}"
            )

    # =====================================================
    # SEND SECURE MESSAGE
    # =====================================================

    def send_secure_message(
        self,
        message
    ):

        if isinstance(message, str):

            message = message.encode()

        self.message_counter += 1

        # =================================================
        # SYNC MODE
        # =================================================

        if SYSTEM_MODE == "SYNC":

            key_id = str(
                self.sync_counter
            )

            key_hex = self.generate_sync_key(
                key_id
            )

            self.sync_counter += 1

            metadata = {

                "key_id":
                    key_id,

                "session_id":
                    self.session_id,

                "sync_index":
                    self.sync_counter,

                "protocol":
                    QKD_PROTOCOL
            }

        # =================================================
        # ETSI MODE
        # =================================================

        else:

            (
                key_id,
                key_hex,
                metadata
            ) = self.get_key()

        # =================================================
        # CRYPTO
        # =================================================

        crypto = CryptoEngine(

            key_hex,

            key_id=key_id,

            mode=SYSTEM_MODE,

            session_id=
                metadata.get(
                    "session_id",
                    self.session_id
                ),

            sync_index=
                metadata.get(
                    "sync_index",
                    0
                )
        )

        # =================================================
        # AES-GCM
        # =================================================

        iv, ciphertext, tag = crypto.encrypt(
            message
        )

        # =================================================
        # NONCE
        # =================================================

        nonce = iv.hex()

        self.used_nonces.add(nonce)

        # =================================================
        # HASH
        # =================================================

        key_hash = crypto.key_hash

        # =================================================
        # AUDIT
        # =================================================

        self.audit.encryption(

            key_id,

            len(message),

            SYSTEM_MODE
        )

        # =================================================
        # VERIFY
        # =================================================

        self.send_verification(
            key_id,
            key_hash
        )

        # =================================================
        # ACK
        # =================================================

        self.send_ack(
            key_id,
            key_hash
        )

        return {

            "key_id":
                key_id,

            "iv":
                iv,

            "ciphertext":
                ciphertext,

            "tag":
                tag,

            "nonce":
                nonce,

            "message_counter":
                self.message_counter,

            "session_id":
                self.session_id
        }

    # =====================================================
    # RECEIVE SECURE MESSAGE
    # =====================================================

    def receive_secure_message(

        self,

        key_id,

        iv,

        ciphertext,

        tag,

        nonce=None,

        buffer=None
    ):

        # =================================================
        # REPLAY CHECK
        # =================================================

        if nonce:

            valid = self.verify_nonce(
                nonce
            )

            if not valid:

                raise Exception(
                    "Replay attack detected"
                )

        # =================================================
        # SYNC MODE
        # =================================================

        if SYSTEM_MODE == "SYNC":

            key_hex = self.generate_sync_key(
                key_id
            )

            metadata = {

                "session_id":
                    self.session_id,

                "sync_index":
                    0
            }

        # =================================================
        # ETSI MODE
        # =================================================

        else:

            key_hex = self.get_key_by_id(

                key_id,

                buffer=buffer
            )

            metadata = self.get_metadata(
                key_id
            )

        # =================================================
        # CRYPTO
        # =================================================

        crypto = CryptoEngine(

            key_hex,

            key_id=key_id,

            mode=SYSTEM_MODE,

            session_id=
                metadata.get(
                    "session_id",
                    self.session_id
                ),

            sync_index=
                metadata.get(
                    "sync_index",
                    0
                )
        )

        # =================================================
        # HASH VERIFY
        # =================================================

        received_hash = metadata.get(
            "key_hash"
        )

        if received_hash:

            verified = crypto.verify_hash(
                received_hash
            )

            if not verified:

                self.audit.sync_fail(
                    key_id
                )

                raise Exception(
                    "SHA-256 verification failed"
                )

            self.audit.sync_success(
                key_id
            )

        # =================================================
        # AES-GCM DECRYPT
        # =================================================

        plaintext = crypto.decrypt(

            iv,

            ciphertext,

            tag
        )

        # =================================================
        # AUDIT
        # =================================================

        self.audit.decryption(

            key_id,

            len(plaintext),

            SYSTEM_MODE
        )

        # =================================================
        # VERIFY ACK
        # =================================================

        if received_hash:

            self.send_verification(
                key_id,
                received_hash
            )

        self.send_ack(
            key_id,
            received_hash
        )

        return plaintext.decode()