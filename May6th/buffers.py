# buffers.py
# FINAL PRODUCTION VERSION (ETSI SAFE - NO KEY LOSS)

from collections import deque
from typing import Optional
from threading import Lock

from models import Key, KeyState
from audit import AuditLogger
from config import SYSTEM_MODE


class QBuffer:

    def __init__(self):

        self._ready_queue = deque()
        self._known_keys = {}

        self._lock = Lock()

        self._sync_index = 0
        self._key_usage = {}

        self.MAX_BYTES_PER_KEY = 32

        self.audit = AuditLogger()

    # =================================================
    # ADD KEY (IITR - LOCAL GENERATION)
    # =================================================
    def add_key(self, key: Key):

        key_id = str(key.key_id)

        with self._lock:

            if key_id in self._known_keys:
                self.audit.error(f"Duplicate key: {key_id}")
                return

            if key.state != KeyState.READY:
                raise ValueError("Only READY keys allowed")

            key.key_id = key_id

            self._ready_queue.append(key)
            self._known_keys[key_id] = key
            self._key_usage[key_id] = 0

            # update sync index
            self._sync_index = max(self._sync_index, int(key_id) + 1)

            self.audit.key_added(key_id)

    # =================================================
    # ADD SYNC KEY (IITJ - FROM PEER)
    # =================================================
    def add_sync_key(self, key: Key):

        key_id = str(key.key_id)

        with self._lock:

            if key_id in self._known_keys:
                self.audit.sync_success(key_id)
                return

            key.key_id = key_id

            self._ready_queue.append(key)
            self._known_keys[key_id] = key
            self._key_usage[key_id] = 0

            # update sync index correctly
            self._sync_index = max(self._sync_index, int(key_id) + 1)

            self.audit.sync_progress(key_id)
            self.audit.sync_success(key_id)

    # =================================================
    # PEEK NEXT KEY (ROTATING ETSI MODE)
    # =================================================
    def peek_next_key(self) -> Optional[Key]:
        """
        Returns next key WITHOUT deleting it,
        but rotates queue so next request gets next key.
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
                    self.audit.key_expired(key.key_id)
                    checked += 1
                    continue

                # rotate key to end
                self._ready_queue.append(key)

                self.audit.key_served(key.key_id)

                return key

            return None

    # =================================================
    # GET NEXT KEY (CONSUME - NOT USED IN ETSI)
    # =================================================
    def get_next_key(self) -> Optional[Key]:
        """
        Removes key from buffer.
        Only for legacy / non-ETSI usage.
        """

        with self._lock:

            self._cleanup_expired_keys_locked()

            while self._ready_queue:

                key = self._ready_queue.popleft()

                if key.is_expired():
                    key.expire()
                    self.audit.key_expired(key.key_id)
                    continue

                key.consume()
                self.audit.key_consumed(key.key_id)

                self._sync_index = int(key.key_id) + 1
                self.audit.sync_progress(self._sync_index)

                return key

            return None

    # =================================================
    # GET KEY BY ID (NO CONSUMPTION)
    # =================================================
    def get_key_by_id(self, key_id: str) -> Optional[Key]:

        key_id = str(key_id)

        with self._lock:

            key = self._known_keys.get(key_id)

            if not key:
                self.audit.error(f"No key {key_id} for sync")
                return None

            if key.is_expired():
                key.expire()
                self.audit.key_expired(key.key_id)
                return None

            self.audit.key_served(key.key_id)

            return key

    # =================================================
    # KEY USAGE TRACKING
    # =================================================
    def use_key_bytes(self, key_id: str, byte_count: int) -> bool:

        key_id = str(key_id)

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
    # CLEANUP EXPIRED KEYS
    # =================================================
    def _cleanup_expired_keys_locked(self):

        new_queue = deque()

        for key in self._ready_queue:

            if key.is_expired():
                key.expire()
                self.audit.key_expired(key.key_id)
            else:
                new_queue.append(key)

        self._ready_queue = new_queue

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