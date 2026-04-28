# ack_manager.py (UPDATED - ROBUST VERSION)

from threading import Lock


class AckManager:
    def __init__(self):
        """
        Tracks ACK status per key_id.
        Structure:
        {
            key_id: {
                "IITR": True,
                "IITJ": True
            }
        }
        """
        self._acks = {}
        self._lock = Lock()

        # Allowed nodes
        self._valid_nodes = {"IITR", "IITJ"}

    # =================================================
    # ADD ACK
    # =================================================
    def add_ack(self, key_id: str, node: str):
        """
        Add acknowledgment for a given key_id and node.
        """

        if key_id is None or node is None:
            return

        key_id = str(key_id)
        node = node.upper()

        # Ignore invalid nodes
        if node not in self._valid_nodes:
            return

        with self._lock:

            if key_id not in self._acks:
                self._acks[key_id] = {}

            self._acks[key_id][node] = True

    # =================================================
    # CHECK COMPLETE
    # =================================================
    def is_complete(self, key_id: str) -> bool:
        """
        Returns True if BOTH IITR and IITJ have acknowledged.
        """

        key_id = str(key_id)

        with self._lock:
            nodes = self._acks.get(key_id, {})

            return (
                nodes.get("IITR", False) and
                nodes.get("IITJ", False)
            )

    # =================================================
    # GET STATUS
    # =================================================
    def status(self, key_id: str) -> dict:
        """
        Returns ACK status for a key_id.
        """

        key_id = str(key_id)

        with self._lock:
            return dict(self._acks.get(key_id, {}))

    # =================================================
    # REMOVE ENTRY
    # =================================================
    def remove(self, key_id: str):
        """
        Removes ACK tracking after completion.
        """

        key_id = str(key_id)

        with self._lock:
            if key_id in self._acks:
                del self._acks[key_id]

    # =================================================
    # DEBUG
    # =================================================
    def dump_all(self) -> dict:
        """
        Returns full ACK table.
        """

        with self._lock:
            return dict(self._acks)