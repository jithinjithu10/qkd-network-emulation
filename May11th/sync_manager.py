# sync_manager.py
# ADVANCED HYBRID QKD SYNCHRONIZATION LAYER

import hashlib
import time
import hmac

from threading import Lock

from audit import AuditLogger

from config import (

    ENABLE_SHA256_SYNC,

    MAX_SYNC_DRIFT,

    QKD_PROTOCOL
)


class SyncManager:

    """
    Synchronization Manager

    Responsibilities
    ----------------
    - distributed key synchronization
    - metadata verification
    - replay prevention
    - synchronization ordering
    - session consistency
    - inter-node integrity validation

    NEVER transfers:
    - raw BB84 bits
    - quantum entropy
    - AES plaintext
    """

    def __init__(self):

        self.audit = AuditLogger()

        self.lock = Lock()

        # =================================================
        # SYNCHRONIZATION STATE
        # =================================================

        self.sync_index = 0

        self.last_verified_key = None

        self.last_session_id = None

        self.last_sync_timestamp = None

        # =================================================
        # TRACKING
        # =================================================

        self.verified_keys = {}

        self.failed_keys = {}

        self.session_map = {}

        self.used_nonces = set()

        self.used_message_ids = set()

        self.session_digests = {}

        # =================================================
        # METRICS
        # =================================================

        self.sync_success = 0

        self.sync_failures = 0

        self.replay_attempts = 0

        self.invalid_metadata = 0

        self.expired_metadata = 0

        self.order_failures = 0

        self.sync_latencies = []

    # =====================================================
    # SHA-256
    # =====================================================

    def sha256_hash(
        self,
        key_material
    ):

        return hashlib.sha256(

            bytes.fromhex(
                key_material
            )

        ).hexdigest()

    # =====================================================
    # CONSTANT-TIME HASH VERIFY
    # =====================================================

    def verify_hash(

        self,

        local_key,

        received_hash
    ):

        if not ENABLE_SHA256_SYNC:
            return True

        local_hash = self.sha256_hash(
            local_key
        )

        return hmac.compare_digest(

            local_hash,

            received_hash
        )

    # =====================================================
    # SESSION DIGEST
    # =====================================================

    def session_digest(
        self,
        session_id
    ):

        return hashlib.sha256(

            f"{session_id}-{QKD_PROTOCOL}".encode()

        ).hexdigest()

    # =====================================================
    # VERIFY ORDER
    # =====================================================

    def verify_order(
        self,
        key_id
    ):

        try:

            key_num = int(key_id)

        except:

            self.order_failures += 1

            return False

        expected = self.sync_index

        if abs(key_num - expected) > MAX_SYNC_DRIFT:

            self.order_failures += 1

            self.audit.log(

                "SYNC_ORDER_FAIL",

                (
                    f"expected={expected} "
                    f"received={key_num}"
                ),

                "SYNC"
            )

            return False

        return True

    # =====================================================
    # VERIFY NONCE
    # =====================================================

    def verify_nonce(
        self,
        nonce
    ):

        if not nonce:
            return False

        if nonce in self.used_nonces:

            self.replay_attempts += 1

            self.audit.error(

                f"Replay nonce detected {nonce}",

                "SYNC"
            )

            return False

        self.used_nonces.add(
            nonce
        )

        return True

    # =====================================================
    # VERIFY MESSAGE ID
    # =====================================================

    def verify_message_id(
        self,
        message_id
    ):

        if not message_id:
            return False

        if message_id in self.used_message_ids:

            self.replay_attempts += 1

            self.audit.error(

                (
                    f"Replay message_id "
                    f"{message_id}"
                ),

                "SYNC"
            )

            return False

        self.used_message_ids.add(
            message_id
        )

        return True

    # =====================================================
    # VERIFY SESSION
    # =====================================================

    def verify_session(

        self,

        session_id,

        key_id
    ):

        with self.lock:

            if session_id not in self.session_map:

                self.session_map[
                    session_id
                ] = []

            self.session_map[
                session_id
            ].append(key_id)

            digest = self.session_digest(
                session_id
            )

            self.session_digests[
                session_id
            ] = digest

        return True

    # =====================================================
    # VERIFY TIMESTAMP
    # =====================================================

    def verify_timestamp(
        self,
        metadata
    ):

        timestamp = metadata.get(
            "timestamp"
        )

        if not timestamp:
            return False

        try:

            now = time.time()

            drift = abs(
                now - float(timestamp)
            )

            if drift > 120:

                self.expired_metadata += 1

                return False

        except:

            return False

        return True

    # =====================================================
    # VERIFY METADATA
    # =====================================================

    def verify_metadata(
        self,
        metadata
    ):

        required_fields = [

            "key_id",

            "session_id",

            "sync_index",

            "protocol"
        ]

        for field in required_fields:

            if field not in metadata:

                self.invalid_metadata += 1

                self.audit.error(

                    (
                        f"Missing metadata "
                        f"{field}"
                    ),

                    "SYNC"
                )

                return False

        # =================================================
        # PROTOCOL
        # =================================================

        if (

            metadata["protocol"]
            !=
            QKD_PROTOCOL
        ):

            self.invalid_metadata += 1

            self.audit.error(

                (
                    f"Protocol mismatch "
                    f"{metadata['protocol']}"
                ),

                "SYNC"
            )

            return False

        # =================================================
        # TIMESTAMP
        # =================================================

        if not self.verify_timestamp(
            metadata
        ):

            self.audit.error(

                "Expired metadata",

                "SYNC"
            )

            return False

        return True

    # =====================================================
    # FULL SYNCHRONIZATION VERIFY
    # =====================================================

    def verify_sync(

        self,

        key_id,

        local_key,

        metadata
    ):

        start = time.perf_counter()

        with self.lock:

            # ---------------------------------------------
            # REPLAY
            # ---------------------------------------------

            if self.is_replay(key_id):

                self.replay_attempts += 1

                self.audit.error(

                    f"Replay key {key_id}",

                    "SYNC"
                )

                return False

            # ---------------------------------------------
            # METADATA
            # ---------------------------------------------

            if not self.verify_metadata(
                metadata
            ):

                self.sync_failures += 1

                return False

            # ---------------------------------------------
            # ORDER
            # ---------------------------------------------

            if not self.verify_order(
                key_id
            ):

                self.sync_failures += 1

                return False

            # ---------------------------------------------
            # HASH
            # ---------------------------------------------

            received_hash = metadata.get(
                "key_hash"
            )

            if received_hash:

                verified = self.verify_hash(

                    local_key,

                    received_hash
                )

                if not verified:

                    self.failed_keys[
                        key_id
                    ] = {

                        "reason":
                            "HASH_MISMATCH",

                        "time":
                            time.time()
                    }

                    self.sync_failures += 1

                    self.audit.sync_fail(
                        key_id
                    )

                    return False

            # ---------------------------------------------
            # NONCE
            # ---------------------------------------------

            nonce = metadata.get(
                "nonce"
            )

            if nonce:

                if not self.verify_nonce(
                    nonce
                ):

                    self.sync_failures += 1

                    return False

            # ---------------------------------------------
            # MESSAGE ID
            # ---------------------------------------------

            message_id = metadata.get(
                "message_id"
            )

            if message_id:

                if not self.verify_message_id(
                    message_id
                ):

                    self.sync_failures += 1

                    return False

            # ---------------------------------------------
            # SESSION
            # ---------------------------------------------

            session_id = metadata.get(
                "session_id"
            )

            self.verify_session(

                session_id,

                key_id
            )

            # ---------------------------------------------
            # VERIFIED
            # ---------------------------------------------

            self.verified_keys[
                key_id
            ] = {

                "session_id":
                    session_id,

                "verified_at":
                    time.time(),

                "metadata":
                    metadata
            }

            self.last_verified_key = (
                key_id
            )

            self.last_session_id = (
                session_id
            )

            self.last_sync_timestamp = (
                time.time()
            )

            self.sync_index += 1

            self.sync_success += 1

            latency = (

                time.perf_counter()
                -
                start
            )

            self.sync_latencies.append(
                latency
            )

            self.audit.sync_success(
                key_id
            )

            return True

    # =====================================================
    # REPLAY CHECK
    # =====================================================

    def is_replay(
        self,
        key_id
    ):

        return (
            key_id
            in
            self.verified_keys
        )

    # =====================================================
    # SESSION KEYS
    # =====================================================

    def session_keys(
        self,
        session_id
    ):

        return self.session_map.get(
            session_id,
            []
        )

    # =====================================================
    # VERIFIED
    # =====================================================

    def verified(
        self,
        key_id
    ):

        return (
            key_id
            in
            self.verified_keys
        )

    # =====================================================
    # FAILED
    # =====================================================

    def failed(
        self,
        key_id
    ):

        return (
            key_id
            in
            self.failed_keys
        )

    # =====================================================
    # AVG LATENCY
    # =====================================================

    def average_latency(
        self
    ):

        if not self.sync_latencies:
            return 0

        return (

            sum(self.sync_latencies)

            /

            len(self.sync_latencies)
        )

    # =====================================================
    # STATS
    # =====================================================

    def stats(self):

        return {

            "sync_index":
                self.sync_index,

            "verified_keys":
                len(self.verified_keys),

            "failed_keys":
                len(self.failed_keys),

            "sync_success":
                self.sync_success,

            "sync_failures":
                self.sync_failures,

            "replay_attempts":
                self.replay_attempts,

            "invalid_metadata":
                self.invalid_metadata,

            "expired_metadata":
                self.expired_metadata,

            "order_failures":
                self.order_failures,

            "average_latency":
                self.average_latency(),

            "last_verified_key":
                self.last_verified_key,

            "last_session_id":
                self.last_session_id
        }

    # =====================================================
    # EXPORT
    # =====================================================

    def export_all(self):

        return {

            "verified_keys":
                self.verified_keys,

            "failed_keys":
                self.failed_keys,

            "session_map":
                self.session_map,

            "stats":
                self.stats()
        }

    # =====================================================
    # DEBUG
    # =====================================================

    def debug_dump(self):

        return self.export_all()


# =========================================================
# STANDALONE TEST
# =====================================================

if __name__ == "__main__":

    sm = SyncManager()

    metadata = {

        "key_id":
            "0",

        "session_id":
            "TEST123",

        "sync_index":
            0,

        "protocol":
            QKD_PROTOCOL,

        "timestamp":
            time.time(),

        "key_hash":
            hashlib.sha256(
                b"hello"
            ).hexdigest()
    }

    result = sm.verify_sync(

        key_id="0",

        local_key=
            "68656c6c6f",

        metadata=metadata
    )

    print("\nSYNC RESULT")

    print(result)

    print("\nSTATS")

    print(sm.stats())