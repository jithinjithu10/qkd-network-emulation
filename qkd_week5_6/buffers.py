from collections import deque
from models import KeyState


class QBuffer:
    """Available quantum keys"""
    def __init__(self):
        self.buffer = deque()

    def add(self, key):
        self.buffer.append(key)

    def pop(self):
        return self.buffer.popleft() if self.buffer else None

    def size(self):
        return len(self.buffer)


class SBuffer:
    """Session-reserved keys"""
    def __init__(self):
        self.reserved = {}

    def reserve(self, key, session_id):
        key.state = KeyState.RESERVED
        self.reserved[session_id] = key

    def consume(self, session_id):
        key = self.reserved.pop(session_id, None)
        if key:
            key.state = KeyState.CONSUMED
        return key
