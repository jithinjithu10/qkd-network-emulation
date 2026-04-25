# audit.py
# Purpose:
# Centralized logging system for:
# - System events
# - Key lifecycle
# - Sync operations (IITR ↔ IITJ)
# - Crypto operations
# - API usage
# - Errors
#
# NOTE:
# No IP changes required in this file.


from datetime import datetime, timezone
from config import NODE_ID


class AuditLogger:

    def __init__(self):
        self.node_id = NODE_ID

    # =================================================
    # CORE LOG FUNCTION
    # =================================================
    def log(self, event_type, message, plane="LOCAL"):
        """
        Base logging function used by all events.
        """

        timestamp = datetime.now(timezone.utc).isoformat()

        print(
            f"[{timestamp}] "
            f"[NODE={self.node_id}] "
            f"[PLANE={plane}] "
            f"[{event_type}] "
            f"{message}"
        )

    # =================================================
    # SYSTEM EVENTS
    # =================================================
    def system_start(self):
        self.log("SYSTEM_START", "Node started", "SYSTEM")

    def system_stop(self):
        self.log("SYSTEM_STOP", "Node stopped", "SYSTEM")

    # =================================================
    # KEY EVENTS
    # =================================================
    def key_added(self, key_id, origin="LOCAL"):
        self.log("KEY_ADDED", f"id={key_id} from {origin}")

    def key_served(self, key_id):
        self.log("KEY_SERVED", f"id={key_id}", "APP")

    def key_used(self, key_id):
        self.log("KEY_USED", f"id={key_id}", "APP")

    def key_consumed(self, key_id):
        self.log("KEY_CONSUMED", f"id={key_id}", "APP")

    def key_expired(self, key_id):
        self.log("KEY_EXPIRED", f"id={key_id}", "APP")

    def key_usage(self, key_id, bytes_used):
        self.log("KEY_USAGE", f"id={key_id} bytes_used={bytes_used}", "APP")

    def key_limit_reached(self, key_id):
        self.log("KEY_LIMIT", f"id={key_id} usage exceeded", "APP")

    # =================================================
    # SYNC EVENTS (CRITICAL)
    # =================================================
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

    def sync_mismatch(self, expected, received):
        self.log(
            "SYNC_MISMATCH",
            f"expected={expected} received={received}",
            "SYNC"
        )

    def sync_key_generated(self, key_id):
        self.log("SYNC_KEY_GENERATED", f"id={key_id}", "SYNC")

    def sync_key_matched(self, key_id):
        self.log("SYNC_KEY_MATCHED", f"id={key_id}", "SYNC")

    # =================================================
    # INTER-KMS EVENTS
    # =================================================
    def key_sent(self, key_id, remote):
        self.log("KEY_SENT", f"id={key_id} → {remote}", "INTER-KMS")

    def key_received(self, key_id, remote):
        self.log("KEY_RECEIVED", f"id={key_id} ← {remote}", "INTER-KMS")

    def key_shared_with_node(self, key_id, node):
        self.log("KEY_SHARED", f"id={key_id} → {node}", "INTER-KMS")

    def interkms_request(self, requester):
        self.log("INTERKMS_REQUEST", f"from {requester}", "INTER-KMS")

    def interkms_response(self, key_id, requester):
        self.log("INTERKMS_RESPONSE", f"id={key_id} → {requester}", "INTER-KMS")

    # =================================================
    # CRYPTO EVENTS
    # =================================================
    def encrypt(self, key_id, size):
        self.log("ENCRYPT", f"id={key_id} bytes={size}", "APP")

    def decrypt(self, key_id, size):
        self.log("DECRYPT", f"id={key_id} bytes={size}", "APP")

    # (Compatibility with crypto_engine naming)
    def encryption(self, key_id, bytes_used, mode):
        self.log(
            "ENCRYPT",
            f"id={key_id} total_bytes={bytes_used} mode={mode}",
            "APP"
        )

    def decryption(self, key_id, bytes_used, mode):
        self.log(
            "DECRYPT",
            f"id={key_id} bytes={bytes_used} mode={mode}",
            "APP"
        )

    # =================================================
    # API EVENTS
    # =================================================
    def api(self, endpoint):
        self.log("API", endpoint, "API")

    # =================================================
    # ERROR EVENTS
    # =================================================
    def error(self, msg, plane="ERROR"):
        self.log("ERROR", msg, plane)