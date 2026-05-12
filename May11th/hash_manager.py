# hash_manager.py
# HYBRID QUANTUM-CLASSICAL QKD HASHING & INTEGRITY LAYER

import hashlib
import hmac
import json
import secrets
import time

from audit import AuditLogger

from config import (

    ENABLE_SHA256_SYNC,

    NODE_SHARED_SECRET,

    QKD_PROTOCOL
)


class HashManager:

    """
    Hash Manager

    Responsibilities
    ----------------
    - SHA-256 synchronization fingerprints
    - metadata integrity verification
    - HMAC authentication
    - replay protection support
    - QKD session verification

    Public Classical Channel
    ------------------------
    Exchanges:
    - hashes
    - fingerprints
    - metadata proofs

    NEVER:
    - raw quantum keys
    """

    def __init__(self):

        self.audit = AuditLogger()

        # =================================================
        # METRICS
        # =================================================

        self.generated_hashes = 0

        self.verified_hashes = 0

        self.failed_verifications = 0

    # =====================================================
    # SHA-256 HASH
    # =====================================================

    def sha256_hash(
        self,
        key_material
    ):

        """
        Generate SHA-256 synchronization fingerprint.

        Used for:
        - synchronization verification
        - metadata validation

        NEVER:
        - raw key transport
        """

        if isinstance(
            key_material,
            str
        ):

            try:

                key_material = bytes.fromhex(
                    key_material
                )

            except Exception:

                key_material = (
                    key_material.encode()
                )

        digest = hashlib.sha256(
            key_material
        ).hexdigest()

        self.generated_hashes += 1

        return digest

    # =====================================================
    # SHORT FINGERPRINT
    # =====================================================

    def short_hash(
        self,
        key_material,
        length=16
    ):

        """
        Compact synchronization fingerprint.
        """

        full = self.sha256_hash(
            key_material
        )

        return full[:length]

    # =====================================================
    # VERIFY HASH
    # =====================================================

    def verify_hash(

        self,

        key_material,

        received_hash
    ):

        """
        Verify synchronized key integrity.

        SHA-256(K_local)
            ==
        SHA-256(K_remote)
        """

        if not ENABLE_SHA256_SYNC:
            return True

        local_hash = self.sha256_hash(
            key_material
        )

        verified = hmac.compare_digest(

            local_hash,

            received_hash
        )

        if verified:

            self.verified_hashes += 1

            self.audit.log(

                "HASH_VERIFIED",

                local_hash[:16],

                "HASH"
            )

        else:

            self.failed_verifications += 1

            self.audit.log(

                "HASH_FAIL",

                local_hash[:16],

                "HASH"
            )

        return verified

    # =====================================================
    # HMAC
    # =====================================================

    def generate_hmac(
        self,
        data
    ):

        """
        HMAC integrity protection
        for metadata packets.
        """

        if isinstance(data, str):

            data = data.encode()

        digest = hmac.new(

            NODE_SHARED_SECRET.encode(),

            data,

            hashlib.sha256

        ).hexdigest()

        return digest

    # =====================================================
    # VERIFY HMAC
    # =====================================================

    def verify_hmac(

        self,

        data,

        received_hmac
    ):

        generated = self.generate_hmac(
            data
        )

        return hmac.compare_digest(

            generated,

            received_hmac
        )

    # =====================================================
    # METADATA HASH
    # =====================================================

    def metadata_hash(
        self,
        metadata
    ):

        """
        Deterministic metadata hashing.
        """

        serialized = json.dumps(

            metadata,

            sort_keys=True

        ).encode()

        return hashlib.sha256(
            serialized
        ).hexdigest()

    # =====================================================
    # SESSION HASH
    # =====================================================

    def session_hash(

        self,

        session_id,

        key_id
    ):

        """
        Session uniqueness fingerprint.
        """

        data = (
            f"{session_id}-{key_id}"
        ).encode()

        return hashlib.sha256(
            data
        ).hexdigest()

    # =====================================================
    # RANDOM NONCE
    # =====================================================

    def nonce(
        self,
        size=16
    ):

        """
        Replay-prevention nonce.
        """

        return secrets.token_hex(size)

    # =====================================================
    # COMBINED FINGERPRINT
    # =====================================================

    def combined_fingerprint(

        self,

        key_material,

        metadata
    ):

        """
        Combined synchronization fingerprint.

        Protects against:
        - replay attacks
        - metadata substitution
        - synchronization confusion
        """

        key_hash = self.sha256_hash(
            key_material
        )

        meta_hash = self.metadata_hash(
            metadata
        )

        combined = (
            key_hash + meta_hash
        ).encode()

        return hashlib.sha256(
            combined
        ).hexdigest()

    # =====================================================
    # QKD SESSION DIGEST
    # =====================================================

    def qkd_session_digest(

        self,

        session_id,

        qber,

        key_id
    ):

        """
        Research-oriented session digest.

        Useful for:
        - dashboards
        - observability
        - synchronization tracing
        """

        payload = (

            f"{QKD_PROTOCOL}|"

            f"{session_id}|"

            f"{qber}|"

            f"{key_id}"
        ).encode()

        return hashlib.sha256(
            payload
        ).hexdigest()

    # =====================================================
    # STATS
    # =====================================================

    def stats(self):

        success_rate = 0

        total = (

            self.verified_hashes
            +
            self.failed_verifications
        )

        if total > 0:

            success_rate = (

                self.verified_hashes
                /
                total

            ) * 100

        return {

            "generated_hashes":
                self.generated_hashes,

            "verified_hashes":
                self.verified_hashes,

            "failed_verifications":
                self.failed_verifications,

            "success_rate":
                success_rate
        }

    # =====================================================
    # DEBUG
    # =====================================================

    def debug_dump(self):

        return {

            "stats":
                self.stats(),

            "protocol":
                QKD_PROTOCOL
        }


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    hm = HashManager()

    key = hashlib.sha256(
        b"quantum-key"
    ).hexdigest()

    digest = hm.sha256_hash(key)

    print("\nSHA-256:")
    print(digest)

    verified = hm.verify_hash(
        key,
        digest
    )

    print("\nVerified:")
    print(verified)