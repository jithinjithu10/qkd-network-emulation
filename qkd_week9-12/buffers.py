"""
buffers.py
-----------

Advanced Buffer Layer
ETSI-aligned and Week 8–12 ready.

Implements:

- Q Buffer (READY keys)
- S Buffer (RESERVED keys per session)
- Application-side Key Store (Week 9)
- Role-aware separation (ENC / DEC)
- Node-aware separation (multi-node support)
- Thread-safe operations
- TTL enforcement
- Re-key support
- Stress metrics tracking
"""

from collections import deque, defaultdict
import threading
from datetime import datetime, timezone
from models import KeyState, KeyRole


# =================================================
# Q BUFFER (READY KEYS)
# =================================================

class QBuffer:
    """
    Stores READY quantum keys.

    ETSI-style separation:
    - Per role (ENC / DEC)
    - Per node (multi-node ready)
    """

    def __init__(self):
        self.buffers = defaultdict(lambda: {
            KeyRole.ENC: deque(),
            KeyRole.DEC: deque()
        })
        self._lock = threading.Lock()

        # Metrics (Week 11)
        self.total_added = 0
        self.total_popped = 0

    def add(self, node_id: str, key):
        with self._lock:
            key.state = KeyState.READY
            self.buffers[node_id][key.role].append(key)
            self.total_added += 1

    def pop(self, node_id: str, role: KeyRole):
        with self._lock:
            pool = self.buffers[node_id][role]

            if not pool:
                return None

            key = pool.popleft()
            self.total_popped += 1
            return key

    def size(self, node_id: str, role: KeyRole):
        with self._lock:
            return len(self.buffers[node_id][role])

    def total_size(self, node_id: str):
        with self._lock:
            return sum(len(pool) for pool in self.buffers[node_id].values())

    def metrics(self):
        return {
            "total_added": self.total_added,
            "total_popped": self.total_popped
        }


# =================================================
# S BUFFER (RESERVED KEYS PER SESSION)
# =================================================

class SBuffer:
    """
    Stores RESERVED keys mapped by session_id.

    Week 9+:
    - Tracks application ID
    - Tracks re-key count
    """

    def __init__(self):
        self.reserved = {}
        self._lock = threading.Lock()

        # Metrics
        self.total_reserved = 0
        self.total_consumed = 0

    def reserve(self, key, session_id: str, app_id: str | None = None):
        with self._lock:
            key.state = KeyState.RESERVED
            key.session_id = session_id
            key.app_id = app_id
            key.rekey_count = 0

            self.reserved[session_id] = key
            self.total_reserved += 1

    def consume(self, session_id: str):
        with self._lock:
            key = self.reserved.pop(session_id, None)
            if key:
                key.state = KeyState.CONSUMED
                self.total_consumed += 1
            return key

    def release(self, session_id: str):
        """
        Release reserved key back to READY (session failure case)
        """
        with self._lock:
            key = self.reserved.pop(session_id, None)
            if key:
                key.state = KeyState.READY
            return key

    def rekey(self, session_id: str):
        """
        Week 10: Dynamic re-keying support
        """
        with self._lock:
            key = self.reserved.get(session_id)
            if key:
                key.rekey_count += 1
            return key

    def size(self):
        with self._lock:
            return len(self.reserved)

    def metrics(self):
        return {
            "total_reserved": self.total_reserved,
            "total_consumed": self.total_consumed
        }


# =================================================
# APPLICATION KEY STORE (Week 9)
# =================================================

class ApplicationKeyStore:
    """
    Stores keys at application side.

    ETSI model:
    - Key IDs synchronized
    - Application controls usage
    """

    def __init__(self):
        self.store = defaultdict(list)
        self._lock = threading.Lock()

    def add_key(self, app_id: str, key):
        with self._lock:
            self.store[app_id].append(key)

    def get_key(self, app_id: str):
        with self._lock:
            if not self.store[app_id]:
                return None
            return self.store[app_id].pop(0)

    def size(self, app_id: str):
        with self._lock:
            return len(self.store[app_id])


# =================================================
# TTL CLEANUP (Corrected)
# =================================================

def expire_key_if_needed(key):
    """
    Proper TTL enforcement.
    """
    now = datetime.now(timezone.utc)

    if key.is_expired():
        key.state = KeyState.EXPIRED
        return True

    return False
