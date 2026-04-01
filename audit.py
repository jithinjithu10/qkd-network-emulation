# audit.py (FINAL - IMPROVED FOR KMS SYNC)

from datetime import datetime, timezone
from config import NODE_ID


class AuditLogger:

    def __init__(self):
        self.node_id = NODE_ID

    # -------------------------------
    # CORE LOG
    # -------------------------------
    def log(self, event_type, message, plane="LOCAL"):

        timestamp = datetime.now(timezone.utc).isoformat()

        print(
            f"[{timestamp}] "
            f"[NODE={self.node_id}] "
            f"[PLANE={plane}] "
            f"[{event_type}] "
            f"{message}"
        )

    # -------------------------------
    # SYSTEM
    # -------------------------------
    def system_start(self):
        self.log("SYSTEM_START", "Node started", "SYSTEM")

    def system_stop(self):
        self.log("SYSTEM_STOP", "Node stopped", "SYSTEM")

    # -------------------------------
    # KEY EVENTS
    # -------------------------------
    def key_added(self, key_id, origin="LOCAL"):
        self.log("KEY_ADDED", f"id={key_id} from {origin}")

    def key_served(self, key_id):
        self.log("KEY_SERVED", f"id={key_id}", "APP")

    def key_used(self, key_id):
        self.log("KEY_USED", f"id={key_id}", "APP")

    # -------------------------------
    # SYNC EVENTS (VERY IMPORTANT)
    # -------------------------------

    def sync_send(self, key_id, target):
        self.log("SYNC_SEND", f"id={key_id} → {target}", "SYNC")

    def sync_receive(self, key_id, source):
        self.log("SYNC_RECEIVE", f"id={key_id} ← {source}", "SYNC")

    def sync_success(self, key_id):
        self.log("SYNC_OK", f"id={key_id} matched", "SYNC")

    def sync_fail(self, key_id):
        self.log("SYNC_FAIL", f"id={key_id} mismatch", "SYNC")

    def sync_compare(self, key_id, local_hash, remote_hash):
        self.log(
            "SYNC_COMPARE",
            f"id={key_id} local={local_hash[:6]} remote={remote_hash[:6]}",
            "SYNC"
        )

    def sync_progress(self, key_id):
        self.log("SYNC_PROGRESS", f"id={key_id}", "SYNC")

    # -------------------------------
    # INTER-KMS
    # -------------------------------
    def key_sent(self, key_id, remote):
        self.log("KEY_SENT", f"id={key_id} → {remote}", "INTER-KMS")

    def key_received(self, key_id, remote):
        self.log("KEY_RECEIVED", f"id={key_id} ← {remote}", "INTER-KMS")

    # -------------------------------
    # CRYPTO
    # -------------------------------
    def encrypt(self, key_id, size):
        self.log("ENCRYPT", f"id={key_id} bytes={size}", "APP")

    def decrypt(self, key_id, size):
        self.log("DECRYPT", f"id={key_id} bytes={size}", "APP")

    # -------------------------------
    # API
    # -------------------------------
    def api(self, endpoint):
        self.log("API", endpoint, "API")

    # -------------------------------
    # ERROR
    # -------------------------------
    def error(self, msg):
        self.log("ERROR", msg, "ERROR")