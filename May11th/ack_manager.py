# ack_manager.py
# QKD METADATA SYNCHRONIZATION MANAGER

from threading import Lock
from datetime import datetime, timezone
from copy import deepcopy
import hashlib


class AckManager:

    """
    QKD Synchronization ACK Manager

    Responsibilities
    ----------------
    - Synchronization tracking
    - Metadata verification
    - Hash consistency validation
    - ACK management
    - Session verification

    IMPORTANT
    ---------
    This belongs to the PUBLIC CLASSICAL CHANNEL.

    Raw quantum keys must NEVER be exchanged here.
    """

    def __init__(self):

        self._acks = {}
        self._lock = Lock()

        self._valid_nodes = {"IITR", "IITJ"}

    # =====================================================
    # HASH GENERATION
    # =====================================================

    @staticmethod
    def generate_hash(key_material: str) -> str:

        if not isinstance(key_material, str):
            raise ValueError("key_material must be string")

        return hashlib.sha256(
            key_material.encode()
        ).hexdigest()

    # =====================================================
    # HASH VALIDATION
    # =====================================================

    @staticmethod
    def _valid_hash(value: str) -> bool:

        if not isinstance(value, str):
            return False

        if len(value) != 64:
            return False

        try:
            int(value, 16)
            return True

        except Exception:
            return False

    # =====================================================
    # CREATE ENTRY
    # =====================================================

    def create_entry(self, key_id: str, session_id: str, sync_index: int):

        key_id = str(key_id)

        with self._lock:

            if key_id in self._acks:
                return

            self._acks[key_id] = {

                "session_id": session_id,
                "sync_index": sync_index,

                "created_at": datetime.now(
                    timezone.utc
                ).isoformat(),

                "verified": False,
                "mismatch": False,

                "IITR": {
                    "hash": None,
                    "ack": False,
                    "timestamp": None
                },

                "IITJ": {
                    "hash": None,
                    "ack": False,
                    "timestamp": None
                }
            }

    # =====================================================
    # ADD ACK
    # =====================================================

    def add_ack(self, key_id: str, node: str, key_hash: str):

        if not key_id or not node or not key_hash:
            return

        key_id = str(key_id)
        node = node.upper()

        if node not in self._valid_nodes:
            return

        if not self._valid_hash(key_hash):
            return

        with self._lock:

            if key_id not in self._acks:
                return

            entry = self._acks[key_id]

            entry[node]["hash"] = key_hash
            entry[node]["ack"] = True

            entry[node]["timestamp"] = datetime.now(
                timezone.utc
            ).isoformat()

            self._verify_hash_match(key_id)

    # =====================================================
    # HASH VERIFICATION
    # =====================================================

    def _verify_hash_match(self, key_id: str):

        entry = self._acks.get(key_id)

        if not entry:
            return

        iitr_hash = entry["IITR"]["hash"]
        iitj_hash = entry["IITJ"]["hash"]

        if iitr_hash is None or iitj_hash is None:
            return

        if iitr_hash == iitj_hash:

            entry["verified"] = True
            entry["mismatch"] = False

        else:

            entry["verified"] = False
            entry["mismatch"] = True

    # =====================================================
    # CHECK COMPLETE
    # =====================================================

    def is_complete(self, key_id: str) -> bool:

        key_id = str(key_id)

        with self._lock:

            if key_id not in self._acks:
                return False

            entry = self._acks[key_id]

            return (
                entry["IITR"]["ack"] and
                entry["IITJ"]["ack"]
            )

    # =====================================================
    # CHECK VERIFIED
    # =====================================================

    def is_verified(self, key_id: str) -> bool:

        key_id = str(key_id)

        with self._lock:

            if key_id not in self._acks:
                return False

            return self._acks[key_id]["verified"]

    # =====================================================
    # CHECK MISMATCH
    # =====================================================

    def has_mismatch(self, key_id: str) -> bool:

        key_id = str(key_id)

        with self._lock:

            if key_id not in self._acks:
                return False

            return self._acks[key_id]["mismatch"]

    # =====================================================
    # STATUS
    # =====================================================

    def status(self, key_id: str) -> dict:

        key_id = str(key_id)

        with self._lock:

            if key_id not in self._acks:
                return {}

            return deepcopy(self._acks[key_id])

    # =====================================================
    # REMOVE
    # =====================================================

    def remove(self, key_id: str):

        key_id = str(key_id)

        with self._lock:

            if key_id in self._acks:
                del self._acks[key_id]

    # =====================================================
    # CLEAR ALL
    # =====================================================

    def clear(self):

        with self._lock:
            self._acks.clear()

    # =====================================================
    # DUMP ALL
    # =====================================================

    def dump_all(self) -> dict:

        with self._lock:
            return deepcopy(self._acks)

    # =====================================================
    # VERIFIED KEYS
    # =====================================================

    def get_verified_keys(self) -> list:

        verified = []

        with self._lock:

            for key_id, entry in self._acks.items():

                if entry["verified"]:
                    verified.append(key_id)

        return verified

    # =====================================================
    # UNVERIFIED KEYS
    # =====================================================

    def get_unverified_keys(self) -> list:

        failed = []

        with self._lock:

            for key_id, entry in self._acks.items():

                complete = (
                    entry["IITR"]["ack"] and
                    entry["IITJ"]["ack"]
                )

                if complete and not entry["verified"]:
                    failed.append(key_id)

        return failed