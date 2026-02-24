"""
Optimized In-Memory Buffer Layer
Performance + Debug Version
"""

from collections import deque, defaultdict
import threading
from datetime import datetime, timezone

from qkd_research_platform_v1.core.models import KeyState, KeyRole
from qkd_research_platform_v1.config import (
    DEFAULT_TTL,
    MIN_FRESHNESS_SCORE,
    QBER_THRESHOLD
)


# =================================================
# Q BUFFER
# =================================================

class QBuffer:

    def __init__(self, max_capacity=1000):

        print("\nInitializing QBuffer")

        self.max_capacity = max_capacity

        self.buffers = defaultdict(lambda: {
            KeyRole.ENC: deque(),
            KeyRole.DEC: deque()
        })

        # 🔥 Optimized size tracking
        self.node_sizes = defaultdict(int)

        self._lock = threading.Lock()

        self.total_added = 0
        self.total_popped = 0
        self.total_expired = 0


    # -------------------------------------------------
    # ADD KEY
    # -------------------------------------------------
    def add(self, node_id: str, key):

        with self._lock:

            if self.node_sizes[node_id] >= self.max_capacity:
                print("QBuffer capacity full")
                return False

            key.state = KeyState.READY
            self.buffers[node_id][key.role].append(key)

            self.node_sizes[node_id] += 1
            self.total_added += 1

            return True


    # -------------------------------------------------
    # POP KEY
    # -------------------------------------------------
    def pop(self, node_id: str, role: KeyRole):

        with self._lock:

            pool = self.buffers[node_id][role]

            while pool:

                key = pool.popleft()

                if key.is_expired():
                    key.state = KeyState.EXPIRED
                    self.total_expired += 1
                    self.node_sizes[node_id] -= 1
                    continue

                if key.freshness_score < MIN_FRESHNESS_SCORE:
                    self.node_sizes[node_id] -= 1
                    continue

                self.total_popped += 1
                self.node_sizes[node_id] -= 1

                return key

            return None


    # -------------------------------------------------
    # SIZE
    # -------------------------------------------------
    def size(self, node_id: str, role: KeyRole):

        with self._lock:
            return len(self.buffers[node_id][role])


    def total_size(self, node_id: str):

        with self._lock:
            return self.node_sizes[node_id]


    # -------------------------------------------------
    # PRESSURE
    # -------------------------------------------------
    def pressure_ratio(self, node_id: str):

        current = self.node_sizes[node_id]
        return current / self.max_capacity


    # -------------------------------------------------
    # CLEANUP
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
                        self.node_sizes[node_id] -= 1
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
# S BUFFER
# =================================================

class SBuffer:

    def __init__(self, max_sessions=500):

        print("Initializing SBuffer")

        self.max_sessions = max_sessions
        self.reserved = {}
        self._lock = threading.Lock()

        self.total_reserved = 0
        self.total_consumed = 0
        self.total_rekeys = 0


    # -------------------------------------------------
    # RESERVE
    # -------------------------------------------------
    def reserve(self, key, session_id: str):

        with self._lock:

            if len(self.reserved) >= self.max_sessions:
                print("SBuffer session limit reached")
                return False

            key.state = KeyState.RESERVED
            key.session_id = session_id
            key.rekey_count = 0

            self.reserved[session_id] = key
            self.total_reserved += 1

            return True


    # -------------------------------------------------
    # CONSUME
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