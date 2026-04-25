# buffers.py
# Purpose:
# Key buffer management system for QKD KMS.
# Handles:
# - Key storage
# - Sync ordering (IITR ↔ IITJ)
# - Key lifecycle (READY → CONSUMED → EXPIRED)
# - Usage tracking per key
#
# NOTE:
# No IP changes required in this file.


from collections import deque
from typing import Optional
from threading import Lock

from models import Key, KeyState
from audit import AuditLogger
from config import SYSTEM_MODE


class QBuffer:

    def __init__(self):

        # Queue for READY keys
        self._ready_queue = deque()

        # Thread safety
        self._lock = Lock()

        # key_id → Key object
        self._known_keys = {}

        # Used only in SYNC mode (strict ordering)
        self._sync_index = 0

        # key_id → bytes used
        self._key_usage = {}

        # IMPORTANT: should match config.MAX_BYTES_PER_KEY
        self.MAX_BYTES_PER_KEY = 32

        self.audit = AuditLogger()

    # =================================================
    # ADD KEY (LOCAL GENERATION - IITR SIDE)
    # =================================================
    def add_key(self, key: Key):

        with self._lock:

            # Prevent duplicates
            if key.key_id in self._known_keys:
                self.audit.error(f"Duplicate key: {key.key_id}")
                return

            # Only READY keys allowed
            if key.state != KeyState.READY:
                raise ValueError("Only READY keys allowed")

            self._ready_queue.append(key)
            self._known_keys[key.key_id] = key
            self._key_usage[key.key_id] = 0

            self.audit.key_added(key.key_id)

    # =================================================
    # ADD SYNC KEY (IITJ SIDE)
    # =================================================
    def add_sync_key(self, key: Key):

        with self._lock:

            expected_id = str(len(self._known_keys))

            # -------------------------------
            # STRICT ORDER CHECK
            # -------------------------------
            if key.key_id != expected_id:
                self.audit.sync_mismatch(
                    expected=expected_id,
                    received=key.key_id
                )
                return

            # -------------------------------
            # DUPLICATE CHECK
            # -------------------------------
            if key.key_id in self._known_keys:
                self.audit.sync_key_matched(key.key_id)
                return

            # -------------------------------
            # ADD KEY
            # -------------------------------
            self._ready_queue.append(key)
            self._known_keys[key.key_id] = key
            self._key_usage[key.key_id] = 0

            self.audit.sync_key_generated(key.key_id)
            self.audit.sync_success(key.key_id)

    # =================================================
    # GET NEXT KEY
    # =================================================
    def get_next_key(self) -> Optional[Key]:

        with self._lock:

            # Clean expired keys before processing
            self._cleanup_expired_keys_locked()

            # -------------------------------
            # SYNC MODE (STRICT ORDER)
            # -------------------------------
            if SYSTEM_MODE == "SYNC":

                expected_key_id = str(self._sync_index)

                key = self._known_keys.get(expected_key_id)

                if not key:
                    self.audit.sync_mismatch(
                        expected=expected_key_id,
                        received=list(self._known_keys.keys())
                    )
                    return None

                if key.is_expired():
                    key.expire()
                    self.audit.key_expired(key.key_id)
                    return None

                # Mark key as used
                key.consume()
                self.audit.key_consumed(key.key_id)

                # Move sync index forward
                self._sync_index += 1
                self.audit.sync_progress(self._sync_index)

                return key

            # -------------------------------
            # NORMAL MODE (QUEUE BASED)
            # -------------------------------
            else:

                while self._ready_queue:

                    key = self._ready_queue.popleft()

                    if key.is_expired():
                        key.expire()
                        self.audit.key_expired(key.key_id)
                        continue

                    key.consume()
                    self.audit.key_consumed(key.key_id)

                    return key

                return None

    # =================================================
    # GET KEY BY ID (CRITICAL FOR APPLICATION)
    # =================================================
    def get_key_by_id(self, key_id: str) -> Optional[Key]:

        with self._lock:

            key = self._known_keys.get(key_id)

            if not key:
                self.audit.error(f"Key not found: {key_id}")
                return None

            if key.is_expired():
                key.expire()
                self.audit.key_expired(key.key_id)
                return None

            self.audit.key_served(key_id)
            return key

    # =================================================
    # DATA USAGE PER KEY
    # =================================================
    def use_key_bytes(self, key_id: str, byte_count: int) -> bool:

        with self._lock:

            if key_id not in self._key_usage:
                return False

            self._key_usage[key_id] += byte_count

            self.audit.key_usage(key_id, self._key_usage[key_id])

            # Enforce usage limit
            if self._key_usage[key_id] >= self.MAX_BYTES_PER_KEY:
                self.audit.key_limit_reached(key_id)
                return False

            return True

    # =================================================
    # CLEANUP EXPIRED KEYS
    # =================================================
    def _cleanup_expired_keys_locked(self):

        cleaned_queue = deque()

        while self._ready_queue:

            key = self._ready_queue.popleft()

            if key.is_expired():
                key.expire()
                self.audit.key_expired(key.key_id)
            else:
                cleaned_queue.append(key)

        self._ready_queue = cleaned_queue

    # =================================================
    # STATS (USED BY API / GUI)
    # =================================================
    def stats(self):

        with self._lock:

            return {
                "ready_keys": len(self._ready_queue),
                "total_keys": len(self._known_keys),
                "sync_index": self._sync_index
            }

    # =================================================
    # DEBUG (FOR TESTING / GUI)
    # =================================================
    def debug_dump(self):

        with self._lock:

            return {
                "ready_ids": [k.key_id for k in self._ready_queue],
                "all_ids": list(self._known_keys.keys()),
                "sync_index": self._sync_index,
                "usage": self._key_usage
            }