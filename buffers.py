"""
buffers.py

FINAL VERSION (ETSI + SYNC SAFE)

Supports:
- Deterministic sync mode (controlled)
- ETSI mode (API-driven)
- Session-safe reservation
- Proper separation of concerns
"""

from collections import deque
from typing import Optional
from threading import Lock

from models import Key, KeyState
from audit import AuditLogger
from config import SYSTEM_MODE


class QBuffer:

    def __init__(self):

        self._ready_queue = deque()
        self._reserved = {}

        self._lock = Lock()

        self._known_keys = set()

        #  Only used in SYNC mode
        self._sync_index = 0

        self.audit = AuditLogger()

    # =================================================
    # ADD LOCAL KEY
    # =================================================

    def add_key(self, key: Key):

        with self._lock:

            if key.key_id in self._known_keys:
                self.audit.error(f"Duplicate key detected: {key.key_id}")
                return

            if key.state != KeyState.READY:
                raise ValueError("Only READY keys can be added")

            self._ready_queue.append(key)
            self._known_keys.add(key.key_id)

            self.audit.key_added(key.key_id, origin="LOCAL")

    # =================================================
    # ADD REMOTE KEY
    # =================================================

    def add_remote_key(self, key: Key, remote_node: str):

        with self._lock:

            if key.key_id in self._known_keys:
                self.audit.sync_key_matched(key.key_id)
                return

            key.state = KeyState.READY

            self._ready_queue.append(key)
            self._known_keys.add(key.key_id)

            self.audit.key_received_from_node(key.key_id, remote_node)

    # =================================================
    # ADD SYNC KEY
    # =================================================

    def add_sync_key(self, key: Key):

        with self._lock:

            if key.key_id in self._known_keys:
                self.audit.sync_key_matched(key.key_id)
                return

            self._ready_queue.append(key)
            self._known_keys.add(key.key_id)

            self.audit.sync_key_generated(key.key_id)

    # =================================================
    #  KEY FETCH (SMART HANDLING)
    # =================================================

    def get_next_key(self) -> Optional[Key]:

        with self._lock:

            self._cleanup_expired_keys_locked()

            # -----------------------------------------
            # SYNC MODE → deterministic
            # -----------------------------------------
            if SYSTEM_MODE == "SYNC":

                expected_key_id = f"sync-{self._sync_index}"

                for key in self._ready_queue:

                    if key.key_id == expected_key_id:

                        self._ready_queue.remove(key)

                        if key.is_expired():
                            key.expire()
                            self.audit.key_expired(key.key_id)
                            return None

                        key.consume()
                        self.audit.key_consumed(key.key_id)

                        #  sync progression log
                        self._sync_index += 1
                        self.audit.sync_progress(self._sync_index)

                        return key

                self.audit.error(f"[SYNC ERROR] Missing key: {expected_key_id}")
                return None

            # -----------------------------------------
            # ETSI MODE → normal queue
            # -----------------------------------------
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
    # RESERVATION
    # =================================================

    def reserve_key(self, session_id: str) -> Optional[Key]:

        with self._lock:

            self._cleanup_expired_keys_locked()

            if SYSTEM_MODE == "SYNC":

                expected_key_id = f"sync-{self._sync_index}"

                for key in self._ready_queue:

                    if key.key_id == expected_key_id:

                        self._ready_queue.remove(key)

                        key.reserve(session_id)
                        self._reserved[session_id] = key

                        self.audit.key_reserved(key.key_id, session_id)

                        self._sync_index += 1
                        self.audit.sync_progress(self._sync_index)

                        return key

                self.audit.error(f"[SYNC ERROR] Reservation failed: {expected_key_id}")
                return None

            # ETSI MODE
            else:

                while self._ready_queue:

                    key = self._ready_queue.popleft()

                    if key.is_expired():
                        key.expire()
                        self.audit.key_expired(key.key_id)
                        continue

                    key.reserve(session_id)
                    self._reserved[session_id] = key

                    self.audit.key_reserved(key.key_id, session_id)

                    return key

                return None

    # =================================================
    # RESERVED ACCESS
    # =================================================

    def get_reserved_key(self, session_id: str) -> Optional[Key]:

        with self._lock:

            key = self._reserved.get(session_id)

            if not key:
                return None

            if key.is_expired():
                key.expire()
                self.audit.key_expired(key.key_id)

                del self._reserved[session_id]
                return None

            return key

    def consume_key(self, session_id: str) -> Optional[Key]:

        with self._lock:

            key = self._reserved.get(session_id)

            if not key:
                return None

            key.consume()
            self.audit.key_consumed(key.key_id)

            del self._reserved[session_id]

            return key

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
                "reserved_keys": len(self._reserved),
                "total_known_keys": len(self._known_keys),
                "sync_index": self._sync_index
            }

    # =================================================
    # DEBUG
    # =================================================

    def debug_dump(self):

        with self._lock:

            return {
                "ready_ids": [k.key_id for k in self._ready_queue],
                "reserved_ids": list(self._reserved.keys()),
                "sync_index": self._sync_index
            }