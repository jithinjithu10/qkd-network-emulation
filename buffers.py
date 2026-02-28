"""
buffers.py

Hybrid ETSI-aligned key buffer management.

Internal lifecycle:
READY → RESERVED → CONSUMED

Externally supports:
- Atomic ETSI get_key()
"""

from collections import deque
from typing import Optional
from models import Key, KeyState


class QBuffer:
    """
    Manages key lifecycle inside KMS.
    """

    def __init__(self):
        self._ready_queue = deque()
        self._reserved = {}

    # =================================================
    # ADD NEW KEY (INTERNAL USE ONLY)
    # =================================================

    def add_key(self, key: Key):
        if key.state != KeyState.READY:
            raise ValueError("Only READY keys can be added to buffer")
        self._ready_queue.append(key)

    # =================================================
    # ETSI ATOMIC FETCH (v2 compliant)
    # =================================================

    def get_next_key(self) -> Optional[Key]:
        """
        ETSI-compliant atomic key retrieval.
        Removes key from READY and marks CONSUMED immediately.
        """

        self._cleanup_expired_keys()

        while self._ready_queue:
            key = self._ready_queue.popleft()

            if key.is_expired():
                key.expire()
                continue

            key.consume()
            return key

        return None

    # =================================================
    # INTERNAL RESERVATION (kept for research logic)
    # =================================================

    def reserve_key(self, session_id: str) -> Optional[Key]:

        self._cleanup_expired_keys()

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

        key = self._reserved.get(session_id)

        if not key:
            return None

        if key.is_expired():
            key.expire()
            del self._reserved[session_id]
            return None

        return key

    def consume_key(self, session_id: str) -> Optional[Key]:

        key = self._reserved.get(session_id)

        if not key:
            return None

        key.consume()
        del self._reserved[session_id]
        return key

    def release_key(self, session_id: str):

        key = self._reserved.get(session_id)

        if not key:
            return

        if key.state == KeyState.RESERVED:
            key.state = KeyState.READY
            key.session_id = None
            self._ready_queue.appendleft(key)

        del self._reserved[session_id]

    # =================================================
    # CLEANUP EXPIRED KEYS
    # =================================================

    def _cleanup_expired_keys(self):

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
    # DEBUG / DEMO
    # =================================================

    def stats(self):
        return {
            "ready_keys": len(self._ready_queue),
            "reserved_keys": len(self._reserved)
        }