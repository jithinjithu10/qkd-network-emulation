"""
buffers.py

ETSI-aligned, thread-safe key buffer.

Lifecycle:
READY → RESERVED → CONSUMED → EXPIRED

Supports:
- Atomic ETSI v2 get_key()
- Internal reservation (research mode)
- Inter-KMS concurrent safety
"""

from collections import deque
from typing import Optional
from threading import Lock
from models import Key, KeyState


class QBuffer:
    """
    Thread-safe key lifecycle manager.
    """

    def __init__(self):
        self._ready_queue = deque()
        self._reserved = {}
        self._lock = Lock()  # Critical for concurrency

    # =================================================
    # ADD NEW KEY
    # =================================================

    def add_key(self, key: Key):
        with self._lock:
            if key.state != KeyState.READY:
                raise ValueError("Only READY keys can be added")
            self._ready_queue.append(key)

    # =================================================
    # ETSI v2 ATOMIC FETCH
    # =================================================

    def get_next_key(self) -> Optional[Key]:
        """
        Atomic key retrieval.
        Immediately transitions READY → CONSUMED.
        """

        with self._lock:

            self._cleanup_expired_keys_locked()

            while self._ready_queue:

                key = self._ready_queue.popleft()

                if key.is_expired():
                    key.expire()
                    continue

                key.consume()
                return key

            return None

    # =================================================
    # INTERNAL RESERVATION (OPTIONAL)
    # =================================================

    def reserve_key(self, session_id: str) -> Optional[Key]:

        with self._lock:

            self._cleanup_expired_keys_locked()

            while self._ready_queue:

                key = self._ready_queue.popleft()

                if key.is_expired():
                    key.expire()
                    continue

                key.reserve(session_id)
                self._reserved[session_id] = key
                return key

            return None

    def get_reserved_key(self, session_id: str) -> Optional[Key]:

        with self._lock:

            key = self._reserved.get(session_id)

            if not key:
                return None

            if key.is_expired():
                key.expire()
                del self._reserved[session_id]
                return None

            return key

    def consume_key(self, session_id: str) -> Optional[Key]:

        with self._lock:

            key = self._reserved.get(session_id)

            if not key:
                return None

            key.consume()
            del self._reserved[session_id]
            return key

    def release_key(self, session_id: str):

        with self._lock:

            key = self._reserved.get(session_id)

            if not key:
                return

            if key.state == KeyState.RESERVED:
                key.state = KeyState.READY
                key.session_id = None
                self._ready_queue.appendleft(key)

            del self._reserved[session_id]

    # =================================================
    # INTERNAL CLEANUP (LOCKED VERSION)
    # =================================================

    def _cleanup_expired_keys_locked(self):

        cleaned_queue = deque()

        while self._ready_queue:
            key = self._ready_queue.popleft()
            if key.is_expired():
                key.expire()
            else:
                cleaned_queue.append(key)

        self._ready_queue = cleaned_queue

        expired_sessions = []

        for session_id, key in self._reserved.items():
            if key.is_expired():
                key.expire()
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self._reserved[session_id]

    # =================================================
    # OBSERVABILITY
    # =================================================

    def stats(self):
        with self._lock:
            return {
                "ready_keys": len(self._ready_queue),
                "reserved_keys": len(self._reserved)
            }