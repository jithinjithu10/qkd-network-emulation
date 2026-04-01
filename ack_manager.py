# ack_manager.py (FINAL - SIMPLE + EFFECTIVE)

from threading import Lock


class AckManager:

    def __init__(self):

        self._acks = {}
        self._lock = Lock()

    # =================================================
    # ADD ACK
    # =================================================

    def add_ack(self, key_id, node):

        with self._lock:

            if key_id not in self._acks:
                self._acks[key_id] = {}

            self._acks[key_id][node] = True

    # =================================================
    # CHECK COMPLETE
    # =================================================

    def is_complete(self, key_id):

        with self._lock:

            nodes = self._acks.get(key_id, {})

            return nodes.get("IITR") and nodes.get("IITJ")

    # =================================================
    # GET STATUS
    # =================================================

    def status(self, key_id):

        with self._lock:

            return self._acks.get(key_id, {})

    # =================================================
    # CLEANUP (optional)
    # =================================================

    def remove(self, key_id):

        with self._lock:

            if key_id in self._acks:
                del self._acks[key_id]