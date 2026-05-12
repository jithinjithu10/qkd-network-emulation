# crypto_engine.py
# HYBRID QUANTUM-CLASSICAL QKD CRYPTO ENGINE

import hashlib
import os
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from audit import AuditLogger

from config import (
    MAX_BYTES_PER_KEY,
    ENCRYPTION_ALGORITHM,
    SYSTEM_MODE,
    ENABLE_SHA256_SYNC
)


class CryptoEngine:

    """
    AES-GCM Secure Communication Engine

    Responsibilities
    ----------------
    - Use BB84-derived synchronized keys
    - Provide AES-256-GCM encryption
    - Bind metadata using AAD
    - Verify synchronization integrity

    IMPORTANT
    ---------
    This module belongs to:
        Secure Communication Layer

    NOT:
        Quantum Layer

    BB84 generates keys.
    This module ONLY consumes keys.
    """

    def __init__(
        self,
        key_hex: str,
        key_id: str,
        mode: str = SYSTEM_MODE,
        session_id: str = None,
        sync_index: int = None
    ):

        # =================================================
        # VALIDATION
        # =================================================

        if not key_id:
            raise ValueError(
                "key_id required"
            )

        if not key_hex:
            raise ValueError(
                "key_hex required"
            )

        # =================================================
        # CONVERT HEX KEY
        # =================================================

        try:

            self.key = bytes.fromhex(
                key_hex
            )

        except Exception:

            raise ValueError(
                "Invalid key_hex format"
            )

        # =================================================
        # AES-256 VALIDATION
        # =================================================

        if len(self.key) != 32:

            raise ValueError(
                "AES-256 requires 32-byte key"
            )

        # =================================================
        # SESSION DETAILS
        # =================================================

        self.key_id = str(key_id)

        self.session_id = (
            session_id
            if session_id
            else f"SESSION-{int(time.time())}"
        )

        self.sync_index = (
            sync_index
            if sync_index is not None
            else 0
        )

        # =================================================
        # MODE VALIDATION
        # =================================================

        valid_modes = (
            "ETSI",
            "SYNC",
            "QKD"
        )

        if mode not in valid_modes:

            raise ValueError(
                f"Invalid mode: {mode}"
            )

        self.mode = mode

        # =================================================
        # AUDIT
        # =================================================

        self.audit = AuditLogger()

        # =================================================
        # USAGE TRACKING
        # =================================================

        self.bytes_used = 0

        # =================================================
        # AES-GCM ENGINE
        # =================================================

        self.aesgcm = AESGCM(self.key)

        # =================================================
        # KEY FINGERPRINT
        # =================================================

        self.key_hash = self.generate_hash()

        # =================================================
        # AUDIT
        # =================================================

        self.audit.log(

            "CRYPTO_INIT",

            (
                f"key_id={self.key_id} "
                f"session={self.session_id} "
                f"mode={self.mode}"
            ),

            "CRYPTO"
        )

    # =====================================================
    # SHA-256 HASH
    # =====================================================

    def generate_hash(self):

        """
        Generate SHA-256 synchronization fingerprint.

        Used ONLY for:
        - synchronization verification
        - metadata validation

        NEVER for:
        - quantum key transport
        """

        return hashlib.sha256(
            self.key.hex().encode()
        ).hexdigest()

    # =====================================================
    # BUILD AAD
    # =====================================================

    def build_aad(self):

        """
        Additional Authenticated Data.

        Authenticates:
        - key_id
        - session_id
        - sync_index
        """

        aad_string = (
            f"{self.key_id}|"
            f"{self.session_id}|"
            f"{self.sync_index}"
        )

        return aad_string.encode()

    # =====================================================
    # ENCRYPT
    # =====================================================

    def encrypt(
        self,
        data: bytes
    ):

        # =================================================
        # INPUT VALIDATION
        # =================================================

        if isinstance(data, str):

            data = data.encode()

        if not isinstance(
            data,
            (bytes, bytearray)
        ):

            raise ValueError(
                "Data must be bytes/string"
            )

        # =================================================
        # KEY USAGE LIMIT
        # =================================================

        if (
            self.bytes_used + len(data)
            > MAX_BYTES_PER_KEY
        ):

            self.audit.key_limit_reached(
                self.key_id
            )

            raise ValueError(
                "Key usage limit exceeded"
            )

        # =================================================
        # RANDOM IV
        # =================================================

        iv = os.urandom(12)

        # =================================================
        # BUILD AAD
        # =================================================

        aad = self.build_aad()

        # =================================================
        # AES-GCM ENCRYPTION
        # =================================================

        full_cipher = self.aesgcm.encrypt(
            iv,
            data,
            aad
        )

        tag = full_cipher[-16:]

        ciphertext = full_cipher[:-16]

        # =================================================
        # TRACK USAGE
        # =================================================

        self.bytes_used += len(data)

        # =================================================
        # AUDIT
        # =================================================

        self.audit.encryption(

            key_id=self.key_id,

            bytes_used=self.bytes_used,

            mode=self.mode
        )

        self.audit.log(

            "AES_GCM_PACKET",

            (
                f"key_id={self.key_id} "
                f"session={self.session_id} "
                f"sync_index={self.sync_index}"
            ),

            "CRYPTO"
        )

        # =================================================
        # RETURN PACKET
        # =================================================

        return (
            iv,
            ciphertext,
            tag
        )

    # =====================================================
    # DECRYPT
    # =====================================================

    def decrypt(
        self,
        iv: bytes,
        ciphertext: bytes,
        tag: bytes
    ):

        # =================================================
        # VALIDATION
        # =================================================

        if (
            not isinstance(
                iv,
                (bytes, bytearray)
            )
            or len(iv) != 12
        ):

            raise ValueError(
                "Invalid IV "
                "(12 bytes required)"
            )

        if not isinstance(
            ciphertext,
            (bytes, bytearray)
        ):

            raise ValueError(
                "Invalid ciphertext"
            )

        if (
            not isinstance(
                tag,
                (bytes, bytearray)
            )
            or len(tag) != 16
        ):

            raise ValueError(
                "Invalid tag"
            )

        # =================================================
        # REBUILD CIPHERTEXT
        # =================================================

        full_ct = ciphertext + tag

        # =================================================
        # REBUILD AAD
        # =================================================

        aad = self.build_aad()

        # =================================================
        # AES-GCM DECRYPTION
        # =================================================

        try:

            plaintext = self.aesgcm.decrypt(
                iv,
                full_ct,
                aad
            )

        except Exception as e:

            self.audit.error(

                (
                    f"Decryption failed "
                    f"key_id={self.key_id} "
                    f"error={str(e)}"
                ),

                "CRYPTO"
            )

            raise ValueError(
                "AES-GCM authentication failed"
            )

        # =================================================
        # AUDIT
        # =================================================

        self.audit.decryption(

            key_id=self.key_id,

            bytes_used=len(plaintext),

            mode=self.mode
        )

        return plaintext

    # =====================================================
    # EXPORT METADATA
    # =====================================================

    def export_metadata(self):

        """
        Export PUBLIC synchronization metadata.

        ONLY metadata is exchanged publicly.
        NEVER raw quantum keys.
        """

        return {

            "key_id":
                self.key_id,

            "session_id":
                self.session_id,

            "sync_index":
                self.sync_index,

            "key_hash":
                self.key_hash,

            "algorithm":
                ENCRYPTION_ALGORITHM,

            "mode":
                self.mode
        }

    # =====================================================
    # VERIFY HASH
    # =====================================================

    def verify_hash(
        self,
        received_hash
    ):

        """
        Verify synchronized key consistency.
        """

        if not ENABLE_SHA256_SYNC:
            return True

        verified = (
            self.key_hash == received_hash
        )

        self.audit.hash_verification(
            self.key_id,
            verified
        )

        return verified

    # =====================================================
    # SESSION INFO
    # =====================================================

    def session_info(self):

        return {

            "session_id":
                self.session_id,

            "key_id":
                self.key_id,

            "sync_index":
                self.sync_index,

            "mode":
                self.mode,

            "bytes_used":
                self.bytes_used
        }