# metadata_manager.py
# ADVANCED HYBRID QUANTUM-CLASSICAL QKD METADATA LAYER

import time
import uuid
import hashlib
import hmac

from audit import AuditLogger

from config import (

    NODE_ID,

    QKD_PROTOCOL,

    SYSTEM_MODE,

    ENABLE_SHA256_SYNC,

    ENABLE_REPLAY_PROTECTION
)


class MetadataManager:

    """
    Metadata Manager

    Responsibilities
    ----------------
    - metadata generation
    - synchronization metadata
    - session lifecycle
    - replay protection
    - distributed integrity validation
    - metadata consistency tracking

    Public Classical Channel
    ------------------------
    Exchanges ONLY:
    - metadata
    - hashes
    - synchronization information

    NEVER:
    - raw BB84 quantum bits
    """

    def __init__(self):

        self.audit = AuditLogger()

        # =================================================
        # STORAGE
        # =================================================

        self.sessions = {}

        self.metadata_store = {}

        self.session_map = {}

        # =================================================
        # SYNCHRONIZATION
        # =================================================

        self.sync_counter = 0

        self.last_verified_key = None

        # =================================================
        # REPLAY TRACKING
        # =================================================

        self.used_nonces = set()

        self.used_message_ids = set()

        # =================================================
        # METRICS
        # =================================================

        self.created_metadata = 0

        self.verified_metadata = 0

        self.failed_metadata = 0

        self.replay_attempts = 0

        self.expired_metadata = 0

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
    # SESSION DIGEST
    # =====================================================

    def session_digest(
        self,
        session_id
    ):

        return hashlib.sha256(

            (
                f"{session_id}-"
                f"{NODE_ID}-"
                f"{QKD_PROTOCOL}"
            ).encode()

        ).hexdigest()

    # =====================================================
    # CONSTANT-TIME VERIFY
    # =====================================================

    def verify_hash(

        self,

        local_hash,

        remote_hash
    ):

        return hmac.compare_digest(

            local_hash,

            remote_hash
        )

    # =====================================================
    # VERIFY NONCE
    # =====================================================

    def verify_nonce(
        self,
        nonce
    ):

        if not ENABLE_REPLAY_PROTECTION:
            return True

        if not nonce:
            return False

        if nonce in self.used_nonces:

            self.replay_attempts += 1

            self.audit.error(

                f"Replay nonce {nonce}",

                "METADATA"
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

                "METADATA"
            )

            return False

        self.used_message_ids.add(
            message_id
        )

        return True

    # =====================================================
    # CREATE SESSION
    # =====================================================

    def create_session(self):

        session_id = str(
            uuid.uuid4()
        )[:8]

        digest = self.session_digest(
            session_id
        )

        self.sessions[session_id] = {

            "created_at":
                time.time(),

            "status":
                "ACTIVE",

            "node":
                NODE_ID,

            "digest":
                digest,

            "messages":
                0,

            "keys":
                []
        }

        self.audit.log(

            "SESSION_CREATED",

            (
                f"session={session_id}"
            ),

            "METADATA"
        )

        return session_id

    # =====================================================
    # CLOSE SESSION
    # =====================================================

    def close_session(
        self,
        session_id
    ):

        if session_id in self.sessions:

            self.sessions[
                session_id
            ]["status"] = "CLOSED"

            self.sessions[
                session_id
            ]["closed_at"] = time.time()

            self.audit.log(

                "SESSION_CLOSED",

                (
                    f"session={session_id}"
                ),

                "METADATA"
            )

    # =====================================================
    # BUILD METADATA
    # =====================================================

    def build_metadata(

        self,

        key_id,

        key_material,

        session_id=None,

        sync_index=None,

        nonce=None,

        message_id=None
    ):

        start = time.perf_counter()

        # =================================================
        # SESSION
        # =================================================

        if session_id is None:

            session_id = self.create_session()

        # =================================================
        # SYNC INDEX
        # =================================================

        if sync_index is None:

            sync_index = self.sync_counter

            self.sync_counter += 1

        # =================================================
        # NONCE
        # =================================================

        if nonce is None:

            nonce = str(
                uuid.uuid4()
            )[:12]

        # =================================================
        # MESSAGE ID
        # =================================================

        if message_id is None:

            message_id = str(
                uuid.uuid4()
            )[:8]

        # =================================================
        # HASH
        # =================================================

        key_hash = None

        if ENABLE_SHA256_SYNC:

            key_hash = self.sha256_hash(
                key_material
            )

        # =================================================
        # METADATA
        # =================================================

        metadata = {

            "key_id":
                str(key_id),

            "session_id":
                session_id,

            "sync_index":
                sync_index,

            "protocol":
                QKD_PROTOCOL,

            "mode":
                SYSTEM_MODE,

            "node_id":
                NODE_ID,

            "timestamp":
                time.time(),

            "nonce":
                nonce,

            "message_id":
                message_id,

            "key_hash":
                key_hash,

            "verified":
                False,

            "digest":
                self.session_digest(
                    session_id
                )
        }

        # =================================================
        # STORE
        # =================================================

        self.metadata_store[
            str(key_id)
        ] = metadata

        if session_id not in self.session_map:

            self.session_map[
                session_id
            ] = []

        self.session_map[
            session_id
        ].append(str(key_id))

        self.sessions[
            session_id
        ]["messages"] += 1

        self.sessions[
            session_id
        ]["keys"].append(
            str(key_id)
        )

        self.created_metadata += 1

        latency = (
            time.perf_counter()
            - start
        )

        self.sync_latencies.append(
            latency
        )

        self.audit.log(

            "METADATA_CREATED",

            (
                f"key_id={key_id} "
                f"session={session_id}"
            ),

            "METADATA"
        )

        return metadata

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

            current = time.time()

            drift = abs(
                current - float(timestamp)
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

        start = time.perf_counter()

        required_fields = [

            "key_id",

            "session_id",

            "sync_index",

            "protocol",

            "timestamp",

            "nonce",

            "message_id"
        ]

        for field in required_fields:

            if field not in metadata:

                self.failed_metadata += 1

                self.audit.error(

                    (
                        f"Missing metadata "
                        f"{field}"
                    ),

                    "METADATA"
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

            self.failed_metadata += 1

            self.audit.error(

                "Protocol mismatch",

                "METADATA"
            )

            return False

        # =================================================
        # TIMESTAMP
        # =================================================

        if not self.verify_timestamp(
            metadata
        ):

            self.failed_metadata += 1

            self.audit.error(

                "Expired metadata",

                "METADATA"
            )

            return False

        # =================================================
        # NONCE
        # =================================================

        nonce = metadata.get(
            "nonce"
        )

        if not self.verify_nonce(
            nonce
        ):

            self.failed_metadata += 1

            return False

        # =================================================
        # MESSAGE ID
        # =================================================

        message_id = metadata.get(
            "message_id"
        )

        if not self.verify_message_id(
            message_id
        ):

            self.failed_metadata += 1

            return False

        # =================================================
        # VERIFIED
        # =================================================

        self.verified_metadata += 1

        self.last_verified_key = (
            metadata["key_id"]
        )

        latency = (
            time.perf_counter()
            - start
        )

        self.sync_latencies.append(
            latency
        )

        return True

    # =====================================================
    # MARK VERIFIED
    # =====================================================

    def mark_verified(
        self,
        key_id
    ):

        key_id = str(key_id)

        if key_id in self.metadata_store:

            self.metadata_store[
                key_id
            ]["verified"] = True

            self.metadata_store[
                key_id
            ]["verified_at"] = time.time()

            self.audit.log(

                "METADATA_VERIFIED",

                (
                    f"key_id={key_id}"
                ),

                "METADATA"
            )

    # =====================================================
    # GET METADATA
    # =====================================================

    def get_metadata(
        self,
        key_id
    ):

        return self.metadata_store.get(
            str(key_id)
        )

    # =====================================================
    # SESSION INFO
    # =====================================================

    def session_info(
        self,
        session_id
    ):

        return self.sessions.get(
            session_id
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
    # REMOVE METADATA
    # =====================================================

    def remove_metadata(
        self,
        key_id
    ):

        key_id = str(key_id)

        if key_id in self.metadata_store:

            del self.metadata_store[
                key_id
            ]

            self.audit.log(

                "METADATA_REMOVED",

                (
                    f"key_id={key_id}"
                ),

                "METADATA"
            )

    # =====================================================
    # AVERAGE LATENCY
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

        verified = 0

        for item in self.metadata_store.values():

            if item.get("verified"):

                verified += 1

        return {

            "stored_metadata":
                len(self.metadata_store),

            "verified_metadata":
                verified,

            "created_metadata":
                self.created_metadata,

            "failed_metadata":
                self.failed_metadata,

            "replay_attempts":
                self.replay_attempts,

            "expired_metadata":
                self.expired_metadata,

            "active_sessions":
                len(self.sessions),

            "sync_counter":
                self.sync_counter,

            "average_latency":
                self.average_latency(),

            "last_verified_key":
                self.last_verified_key
        }

    # =====================================================
    # EXPORT
    # =====================================================

    def export_all(self):

        return {

            "sessions":
                self.sessions,

            "metadata":
                self.metadata_store,

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
# =========================================================

if __name__ == "__main__":

    mm = MetadataManager()

    metadata = mm.build_metadata(

        key_id="0",

        key_material=
            "68656c6c6f"
    )

    print("\nMETADATA")

    print(metadata)

    result = mm.verify_metadata(
        metadata
    )

    print("\nVERIFIED")

    print(result)

    print("\nSTATS")

    print(mm.stats())