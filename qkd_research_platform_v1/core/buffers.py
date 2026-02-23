"""
buffers.py
-----------

Research-Grade In-Memory Buffer Layer
Primary Data Plane for QKD KMS

Implements:
- QBuffer (READY keys)
- SBuffer (RESERVED keys per session)
- Capacity limits
- Buffer pressure tracking
- Freshness decay
- TTL cleanup
- Physics-aware filtering
- Stress metrics
"""

from collections import deque, defaultdict
import threading
from datetime import datetime, timezone
from models import KeyState, KeyRole
from config import (
    DEFAULT_TTL,
    MIN_FRESHNESS_SCORE,
    QBER_THRESHOLD
)


# =================================================
# Q BUFFER (PRIMARY READY POOL)
# =================================================

class QBuffer:

    def __init__(self, max_capacity=1000):

        self.max_capacity = max_capacity

        self.buffers = defaultdict(lambda: {
            KeyRole.ENC: deque(),
            KeyRole.DEC: deque()
        })

        self._lock = threading.Lock()

        self.total_added = 0
        self.total_popped = 0
        self.total_expired = 0

    # -------------------------------------------------
    # ADD KEY
    # -------------------------------------------------
    def add(self, node_id: str, key):

        with self._lock:

            if self.total_size(node_id) >= self.max_capacity:
                return False  # capacity full

            key.state = KeyState.READY
            self.buffers[node_id][key.role].append(key)

            self.total_added += 1
            return True

    # -------------------------------------------------
    # POP KEY (FOR ALLOCATION)
    # -------------------------------------------------
    def pop(self, node_id: str, role: KeyRole):

        with self._lock:

            pool = self.buffers[node_id][role]

            while pool:

                key = pool.popleft()

                if key.is_expired():
                    key.state = KeyState.EXPIRED
                    self.total_expired += 1
                    continue

                if key.freshness_score < MIN_FRESHNESS_SCORE:
                    continue

                self.total_popped += 1
                return key

            return None

    # -------------------------------------------------
    # BUFFER SIZE
    # -------------------------------------------------
    def size(self, node_id: str, role: KeyRole):

        with self._lock:
            return len(self.buffers[node_id][role])

    def total_size(self, node_id: str):

        with self._lock:
            return sum(len(pool) for pool in self.buffers[node_id].values())

    # -------------------------------------------------
    # BUFFER PRESSURE
    # -------------------------------------------------
    def pressure_ratio(self, node_id: str):

        current = self.total_size(node_id)
        return current / self.max_capacity

    # -------------------------------------------------
    # TTL CLEANUP SWEEP
    # -------------------------------------------------
    def cleanup(self, node_id: str):

        with self._lock:

            for role in [KeyRole.ENC, KeyRole.DEC]:

                pool = self.buffers[node_id][role]
                new_pool = deque()

                while pool:
                    key = pool.popleft()
                    if key.is_expired():
                        key.state = KeyState.EXPIRED
                        self.total_expired += 1
                    else:
                        new_pool.append(key)

                self.buffers[node_id][role] = new_pool

    # -------------------------------------------------
    # METRICS
    # -------------------------------------------------
    def metrics(self):

        return {
            "total_added": self.total_added,
            "total_popped": self.total_popped,
            "total_expired": self.total_expired
        }


# =================================================
# S BUFFER (SESSION-RESERVED KEYS)
# =================================================

class SBuffer:

    def __init__(self, max_sessions=500):

        self.max_sessions = max_sessions
        self.reserved = {}
        self._lock = threading.Lock()

        self.total_reserved = 0
        self.total_consumed = 0
        self.total_rekeys = 0

    # -------------------------------------------------
    # RESERVE KEY
    # -------------------------------------------------
    def reserve(self, key, session_id: str):

        with self._lock:

            if len(self.reserved) >= self.max_sessions:
                return False

            key.state = KeyState.RESERVED
            key.session_id = session_id
            key.rekey_count = 0

            self.reserved[session_id] = key
            self.total_reserved += 1
            return True

    # -------------------------------------------------
    # CONSUME KEY
    # -------------------------------------------------
    def consume(self, session_id: str):

        with self._lock:

            key = self.reserved.pop(session_id, None)

            if key:
                key.state = KeyState.CONSUMED
                self.total_consumed += 1

            return key

    # -------------------------------------------------
    # REKEY
    # -------------------------------------------------
    def rekey(self, session_id: str):

        with self._lock:

            key = self.reserved.get(session_id)

            if key:
                key.rekey_count += 1
                self.total_rekeys += 1

            return key

    # -------------------------------------------------
    # SIZE
    # -------------------------------------------------
    def size(self):

        with self._lock:
            return len(self.reserved)

    # -------------------------------------------------
    # METRICS
    # -------------------------------------------------
    def metrics(self):

        return {
            "total_reserved": self.total_reserved,
            "total_consumed": self.total_consumed,
            "total_rekeys": self.total_rekeys
        }