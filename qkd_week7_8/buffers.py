"""
buffers.py
-----------
Implements in-memory buffer abstraction for:

- Q Buffer (READY keys)
- S Buffer (RESERVED keys per session)
- Role-aware separation (ENC / DEC)
- Thread-safe operations
- Monitoring support
"""

from collections import deque
import threading
from datetime import datetime, timezone, timedelta
from models import KeyState, KeyRole


# =================================================
# Q BUFFER (READY KEYS)
# =================================================
class QBuffer:
    """
    Stores READY quantum keys.
    Maintains separate pools for ENC and DEC roles.
    Thread-safe.
    """

    def __init__(self):
        self.buffers = {
            KeyRole.ENC: deque(),
            KeyRole.DEC: deque()
        }
        self._lock = threading.Lock()

    def add(self, key):
        """
        Add key to READY pool based on role.
        """
        with self._lock:
            key.state = KeyState.READY
            self.buffers[key.role].append(key)

    def pop(self, role: KeyRole):
        """
        Retrieve oldest READY key for specific role.
        """
        with self._lock:
            if self.buffers[role]:
                return self.buffers[role].popleft()
            return None

    def size(self, role: KeyRole):
        """
        Number of READY keys for a role.
        """
        with self._lock:
            return len(self.buffers[role])

    def total_size(self):
        """
        Total READY keys across all roles.
        """
        with self._lock:
            return sum(len(buf) for buf in self.buffers.values())


# =================================================
# S BUFFER (RESERVED KEYS PER SESSION)
# =================================================
class SBuffer:
    """
    Stores RESERVED keys mapped by session_id.
    Thread-safe.
    """

    def __init__(self):
        self.reserved = {}
        self._lock = threading.Lock()

    def reserve(self, key, session_id):
        """
        Move key from READY → RESERVED
        """
        with self._lock:
            key.state = KeyState.RESERVED
            key.session_id = session_id
            self.reserved[session_id] = key

    def consume(self, session_id):
        """
        RESERVED → CONSUMED
        """
        with self._lock:
            key = self.reserved.pop(session_id, None)
            if key:
                key.state = KeyState.CONSUMED
            return key

    def release(self, session_id):
        """
        Release reserved key back to READY
        (useful if session fails)
        """
        with self._lock:
            key = self.reserved.pop(session_id, None)
            if key:
                key.state = KeyState.READY
            return key

    def size(self):
        """
        Number of active reserved sessions.
        """
        with self._lock:
            return len(self.reserved)


# =================================================
# TTL CLEANUP (Optional Week 7+)
# =================================================
def expire_key_if_needed(key):
    """
    Check TTL expiry for in-memory key.
    """
    now = datetime.now(timezone.utc)

    if now > key.created_at + timedelta(seconds=key.ttl_seconds):
        key.state = KeyState.EXPIRED
        return True

    return False
