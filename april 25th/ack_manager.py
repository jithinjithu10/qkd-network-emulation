# ack_manager.py
# Purpose:
# Manages acknowledgment (ACK) tracking between IITR and IITJ nodes.
# Ensures that a key_id is considered fully synchronized only when
# both nodes have acknowledged it.

from threading import Lock


class AckManager:
    def __init__(self):
        # Dictionary structure:
        # {
        #   key_id: {
        #       "IITR": True,
        #       "IITJ": True
        #   }
        # }
        self._acks = {}

        # Thread safety lock
        self._lock = Lock()

    # =================================================
    # ADD ACK
    # =================================================
    def add_ack(self, key_id: str, node: str):
        """
        Store acknowledgment from a node (IITR or IITJ)
        for a given key_id.
        """

        if not key_id or not node:
            return

        with self._lock:

            # Initialize entry if not present
            if key_id not in self._acks:
                self._acks[key_id] = {}

            # Mark node as acknowledged
            self._acks[key_id][node] = True

    # =================================================
    # CHECK COMPLETE
    # =================================================
    def is_complete(self, key_id: str) -> bool:
        """
        Returns True only if BOTH IITR and IITJ
        have acknowledged the given key_id.
        """

        with self._lock:

            nodes = self._acks.get(key_id, {})

            # Explicit boolean handling to avoid None issues
            return nodes.get("IITR", False) and nodes.get("IITJ", False)

    # =================================================
    # GET STATUS
    # =================================================
    def status(self, key_id: str) -> dict:
        """
        Returns acknowledgment status for a key_id.
        Example:
        {
            "IITR": True,
            "IITJ": False
        }
        """

        with self._lock:
            return dict(self._acks.get(key_id, {}))

    # =================================================
    # REMOVE ENTRY
    # =================================================
    def remove(self, key_id: str):
        """
        Remove ACK tracking for a key_id after completion.
        Prevents memory growth over time.
        """

        with self._lock:
            if key_id in self._acks:
                del self._acks[key_id]

    # =================================================
    # DEBUG (OPTIONAL)
    # =================================================
    def dump_all(self) -> dict:
        """
        Returns full ACK table (for debugging/monitoring).
        """

        with self._lock:
            return dict(self._acks)