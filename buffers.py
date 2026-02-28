"""
buffers.py

Strict ETSI-aligned key buffer management.

Implements:
- READY key pool
- Reservation handling
- TTL enforcement
- Strict lifecycle transitions
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
    # RESERVE KEY
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

        return None  # No available key

    # =================================================
    # GET RESERVED KEY
    # =================================================

    def get_reserved_key(self, session_id: str) -> Optional[Key]:

        key = self._reserved.get(session_id)

        if not key:
            return None

        if key.is_expired():
            key.expire()
            del self._reserved[session_id]
            return None

        return key

    # =================================================
    # CONSUME KEY
    # =================================================

    def consume_key(self, session_id: str) -> Optional[Key]:

        key = self._reserved.get(session_id)

        if not key:
            return None

        key.consume()
        del self._reserved[session_id]
        return key

    # =================================================
    # RELEASE KEY (IF SESSION CLOSED WITHOUT USE)
    # =================================================

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

        # Clean ready queue
        cleaned_queue = deque()

        while self._ready_queue:
            key = self._ready_queue.popleft()
            if key.is_expired():
                key.expire()
            else:
                cleaned_queue.append(key)

        self._ready_queue = cleaned_queue

        # Clean reserved
        expired_sessions = []

        for session_id, key in self._reserved.items():
            if key.is_expired():
                key.expire()
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self._reserved[session_id]

    # =================================================
    # DEBUG / OBSERVABILITY (FOR DEMO)
    # =================================================

    def stats(self):
        return {
            "ready_keys": len(self._ready_queue),
            "reserved_keys": len(self._reserved)
        }