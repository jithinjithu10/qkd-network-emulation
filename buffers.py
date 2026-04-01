# buffers.py (FINAL - SYNC FIXED + CLEAN)

from collections import deque
from typing import Optional
from threading import Lock

from models import Key, KeyState
from audit import AuditLogger
from config import SYSTEM_MODE


class QBuffer:

    def __init__(self):

        self._ready_queue = deque()
        self._lock = Lock()
        self._known_keys = {}

        self._sync_index = 0

        self._key_usage = {}
        self.MAX_BYTES_PER_KEY = 32

        self.audit = AuditLogger()

    # =================================================
    # ADD KEY (LOCAL GENERATION - IITR)
    # =================================================

    def add_key(self, key: Key):

        with self._lock:

            if key.key_id in self._known_keys:
                self.audit.error(f"Duplicate key: {key.key_id}")
                return

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

                # USE KEY
                key.consume()
                self.audit.key_consumed(key.key_id)

                # MOVE INDEX
                self._sync_index += 1

                self.audit.sync_progress(self._sync_index)

                return key

            # -------------------------------
            # NORMAL MODE
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
    # GET KEY BY ID (CRITICAL FOR APP)
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

    def use_key_bytes(self, key_id: str, byte_count: int):

        with self._lock:

            if key_id not in self._key_usage:
                return False

            self._key_usage[key_id] += byte_count

            self.audit.key_usage(key_id, self._key_usage[key_id])

            if self._key_usage[key_id] >= self.MAX_BYTES_PER_KEY:
                self.audit.key_limit_reached(key_id)
                return False

            return True

    # =================================================
    # CLEANUP
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
    # STATS
    # =================================================

    def stats(self):

        with self._lock:

            return {
                "ready_keys": len(self._ready_queue),
                "total_keys": len(self._known_keys),
                "sync_index": self._sync_index
            }

    # =================================================
    # DEBUG
    # =================================================

    def debug_dump(self):

        with self._lock:

            return {
                "ready_ids": [k.key_id for k in self._ready_queue],
                "all_ids": list(self._known_keys.keys()),
                "sync_index": self._sync_index,
                "usage": self._key_usage
            }