# buffers.py
# HYBRID QUANTUM-CLASSICAL QKD BUFFER MANAGER

from collections import deque
from threading import Lock
from typing import Optional
from datetime import datetime
import hashlib

from models import Key, KeyState
from audit import AuditLogger
from config import SYSTEM_MODE


class QBuffer:

    """
    Quantum Key Buffer

    Responsibilities
    ----------------
    - Store BB84-derived keys
    - Manage synchronized QKD sessions
    - Maintain ETSI-style rotating key pool
    - Track synchronization metadata
    - Enforce key usage policies

    IMPORTANT
    ---------
    Raw keys remain LOCAL ONLY.

    Public/classical channels exchange:
    - hashes
    - metadata
    - synchronization state

    NEVER raw key material.
    """

    def __init__(self):

        # =================================================
        # READY KEY QUEUE
        # =================================================

        self._ready_queue = deque()

        # =================================================
        # KEY STORAGE
        # =================================================

        self._known_keys = {}

        # =================================================
        # METADATA
        # =================================================

        self._metadata = {}

        # =================================================
        # USAGE TRACKING
        # =================================================

        self._key_usage = {}

        # =================================================
        # SYNCHRONIZATION INDEX
        # =================================================

        self._sync_index = 0

        # =================================================
        # THREAD SAFETY
        # =================================================

        self._lock = Lock()

        # =================================================
        # POLICY
        # =================================================

        self.MAX_BYTES_PER_KEY = 32

        # =================================================
        # AUDIT LOGGER
        # =================================================

        self.audit = AuditLogger()

    # =====================================================
    # SHA-256 HASH
    # =====================================================

    @staticmethod
    def generate_hash(key_material: str):

        return hashlib.sha256(
            key_material.encode()
        ).hexdigest()

    # =====================================================
    # CREATE METADATA
    # =====================================================

    def _create_metadata(
        self,
        key: Key,
        origin="LOCAL_BB84"
    ):

        key_id = str(key.key_id)

        self._metadata[key_id] = {

            "key_id": key_id,

            "sync_index":
                self._sync_index,

            "created_at":
                datetime.utcnow().isoformat(),

            "origin":
                origin,

            "key_hash":
                self.generate_hash(key.key),

            "verified":
                False,

            "state":
                str(key.state),

            "usage_bytes":
                0
        }

    # =====================================================
    # ADD LOCAL BB84 KEY
    # =====================================================

    def add_key(
        self,
        key: Key
    ):

        """
        Add locally generated BB84 key.
        """

        key_id = str(key.key_id)

        with self._lock:

            # ---------------------------------------------
            # DUPLICATE CHECK
            # ---------------------------------------------

            if key_id in self._known_keys:

                self.audit.error(
                    f"Duplicate key: {key_id}"
                )

                return

            # ---------------------------------------------
            # STATE VALIDATION
            # ---------------------------------------------

            if key.state != KeyState.READY:

                raise ValueError(
                    "Only READY keys allowed"
                )

            key.key_id = key_id

            # ---------------------------------------------
            # STORE
            # ---------------------------------------------

            self._ready_queue.append(key)

            self._known_keys[key_id] = key

            self._key_usage[key_id] = 0

            # ---------------------------------------------
            # UPDATE SYNC INDEX
            # ---------------------------------------------

            self._sync_index = max(
                self._sync_index,
                int(key_id) + 1
            )

            # ---------------------------------------------
            # METADATA
            # ---------------------------------------------

            self._create_metadata(
                key,
                origin="LOCAL_BB84"
            )

            # ---------------------------------------------
            # AUDIT
            # ---------------------------------------------

            self.audit.key_added(
                key_id,
                origin="LOCAL_BB84"
            )

    # =====================================================
    # ADD SYNCHRONIZED KEY
    # =====================================================

    def add_sync_key(
        self,
        key: Key
    ):

        """
        Add synchronized/reconciled key.

        This is NOT key transport.
        """

        key_id = str(key.key_id)

        with self._lock:

            # ---------------------------------------------
            # ALREADY EXISTS
            # ---------------------------------------------

            if key_id in self._known_keys:

                self.audit.sync_success(
                    key_id
                )

                return

            key.key_id = key_id

            # ---------------------------------------------
            # STORE
            # ---------------------------------------------

            self._ready_queue.append(key)

            self._known_keys[key_id] = key

            self._key_usage[key_id] = 0

            # ---------------------------------------------
            # UPDATE INDEX
            # ---------------------------------------------

            self._sync_index = max(
                self._sync_index,
                int(key_id) + 1
            )

            # ---------------------------------------------
            # METADATA
            # ---------------------------------------------

            self._create_metadata(
                key,
                origin="SYNC_BB84"
            )

            self._metadata[key_id][
                "verified"
            ] = True

            # ---------------------------------------------
            # AUDIT
            # ---------------------------------------------

            self.audit.sync_progress(
                key_id
            )

            self.audit.sync_success(
                key_id
            )

    # =====================================================
    # VERIFY HASH
    # =====================================================

    def verify_key_hash(
        self,
        key_id,
        received_hash
    ) -> bool:

        key_id = str(key_id)

        with self._lock:

            metadata = self._metadata.get(
                key_id
            )

            if not metadata:
                return False

            local_hash = metadata[
                "key_hash"
            ]

            verified = (
                local_hash == received_hash
            )

            metadata["verified"] = verified

            self.audit.hash_verification(
                key_id,
                verified
            )

            return verified

    # =====================================================
    # GET METADATA
    # =====================================================

    def get_metadata(
        self,
        key_id
    ):

        key_id = str(key_id)

        with self._lock:

            return self._metadata.get(
                key_id
            )

    # =====================================================
    # ROTATING ETSI MODE
    # =====================================================

    def peek_next_key(
        self
    ) -> Optional[Key]:

        """
        Rotating ETSI-style key access.
        """

        with self._lock:

            self._cleanup_expired_keys_locked()

            if not self._ready_queue:
                return None

            checked = 0

            while checked < len(self._ready_queue):

                key = self._ready_queue.popleft()

                if key.is_expired():

                    key.expire()

                    self.audit.key_expired(
                        key.key_id
                    )

                    checked += 1

                    continue

                self._ready_queue.append(key)

                self.audit.key_served(
                    key.key_id
                )

                return key

            return None

    # =====================================================
    # LEGACY CONSUME MODE
    # =====================================================

    def get_next_key(
        self
    ) -> Optional[Key]:

        with self._lock:

            self._cleanup_expired_keys_locked()

            while self._ready_queue:

                key = self._ready_queue.popleft()

                if key.is_expired():

                    key.expire()

                    self.audit.key_expired(
                        key.key_id
                    )

                    continue

                key.consume()

                self.audit.key_consumed(
                    key.key_id
                )

                self._sync_index = (
                    int(key.key_id) + 1
                )

                return key

            return None

    # =====================================================
    # GET KEY BY ID
    # =====================================================

    def get_key_by_id(
        self,
        key_id
    ) -> Optional[Key]:

        key_id = str(key_id)

        with self._lock:

            key = self._known_keys.get(
                key_id
            )

            if not key:

                self.audit.error(
                    f"Missing key: {key_id}"
                )

                return None

            if key.is_expired():

                key.expire()

                self.audit.key_expired(
                    key.key_id
                )

                return None

            self.audit.key_served(
                key.key_id
            )

            return key

    # =====================================================
    # USAGE TRACKING
    # =====================================================

    def use_key_bytes(
        self,
        key_id,
        byte_count
    ) -> bool:

        key_id = str(key_id)

        with self._lock:

            if key_id not in self._key_usage:
                return False

            self._key_usage[key_id] += byte_count

            if key_id in self._metadata:

                self._metadata[key_id][
                    "usage_bytes"
                ] = self._key_usage[key_id]

            self.audit.key_usage(
                key_id,
                self._key_usage[key_id]
            )

            if (
                self._key_usage[key_id]
                >= self.MAX_BYTES_PER_KEY
            ):

                self.audit.key_limit_reached(
                    key_id
                )

                return False

            return True

    # =====================================================
    # CLEANUP
    # =====================================================

    def _cleanup_expired_keys_locked(self):

        new_queue = deque()

        for key in self._ready_queue:

            if key.is_expired():

                key.expire()

                self.audit.key_expired(
                    key.key_id
                )

            else:

                new_queue.append(key)

        self._ready_queue = new_queue

    # =====================================================
    # BUFFER STATS
    # =====================================================

    def stats(self):

        with self._lock:

            verified_keys = sum(
                1
                for m in self._metadata.values()
                if m.get("verified")
            )

            return {

                "ready_keys":
                    len(self._ready_queue),

                "total_keys":
                    len(self._known_keys),

                "verified_keys":
                    verified_keys,

                "sync_index":
                    self._sync_index,

                "system_mode":
                    SYSTEM_MODE
            }

    # =====================================================
    # DEBUG
    # =====================================================

    def debug_dump(self):

        with self._lock:

            return {

                "ready_ids": [
                    k.key_id
                    for k in self._ready_queue
                ],

                "all_ids":
                    list(self._known_keys.keys()),

                "metadata":
                    self._metadata,

                "usage":
                    self._key_usage,

                "sync_index":
                    self._sync_index
            }