"""
audit.py (FINAL - SESSION FREE, RESEARCH LEVEL)

Clean version:
- No session logic
- Full key lifecycle tracking
- Sync + Inter-KMS debugging
"""

from datetime import datetime, timezone
from config import NODE_ID


class AuditLogger:

    def __init__(self):
        self.node_id = NODE_ID

    # =================================================
    # CORE LOG
    # =================================================

    def log(self, event_type: str, message: str, plane: str = "LOCAL"):

        timestamp = datetime.now(timezone.utc).isoformat()

        print(
            f"[{timestamp}] "
            f"[NODE={self.node_id}] "
            f"[PLANE={plane}] "
            f"[{event_type}] "
            f"{message}"
        )

    # =================================================
    # SYSTEM
    # =================================================

    def system_start(self):
        self.log("SYSTEM_START", "QKD Node started", "SYSTEM")

    def system_shutdown(self):
        self.log("SYSTEM_STOP", "QKD Node stopped", "SYSTEM")

    # =================================================
    # KEY EVENTS
    # =================================================

    def key_added(self, key_id: str, origin: str = "LOCAL"):
        self.log("KEY_ADDED", f"Key ID: {key_id} | Origin: {origin}", "LOCAL")

    def key_served(self, key_id: str):
        self.log("KEY_SERVED", f"Key ID: {key_id}", "APPLICATION")

    def key_consumed(self, key_id: str):
        self.log("KEY_CONSUMED", f"Key ID: {key_id}", "APPLICATION")

    def key_expired(self, key_id: str):
        self.log("KEY_EXPIRED", f"Key ID: {key_id}", "LOCAL")

    # =================================================
    # DATA PER KEY (CRITICAL)
    # =================================================

    def key_usage(self, key_id: str, bytes_used: int):
        self.log(
            "KEY_USAGE",
            f"Key ID: {key_id} used for {bytes_used} bytes",
            "APPLICATION"
        )

    def key_limit_reached(self, key_id: str):
        self.log(
            "KEY_LIMIT",
            f"Key ID: {key_id} reached max usage",
            "APPLICATION"
        )

    # =================================================
    # KEY ROTATION
    # =================================================

    def key_rotation(self, old_key: str, new_key: str):
        self.log(
            "KEY_ROTATION",
            f"{old_key} → {new_key}",
            "SYNC"
        )

    # =================================================
    # SYNC EVENTS
    # =================================================

    def sync_key_generated(self, key_id: str):
        self.log("SYNC_KEY_GENERATED", f"Key ID: {key_id}", "SYNC")

    def sync_key_matched(self, key_id: str):
        self.log("SYNC_KEY_MATCH", f"Key ID: {key_id}", "SYNC")

    def sync_progress(self, index: int):
        self.log("SYNC_PROGRESS", f"Index: {index}", "SYNC")

    def sync_mismatch(self, expected, received):
        self.log(
            "SYNC_ERROR",
            f"Expected {expected}, got {received}",
            "SYNC"
        )

    # =================================================
    # INTER-KMS
    # =================================================

    def key_shared_with_node(self, key_id: str, remote_node: str):
        self.log(
            "KEY_SHARED",
            f"{key_id} → {remote_node}",
            "INTER-KMS"
        )

    def key_received_from_node(self, key_id: str, remote_node: str):
        self.log(
            "KEY_RECEIVED",
            f"{key_id} ← {remote_node}",
            "INTER-KMS"
        )

    def interkms_request(self, remote_node: str):
        self.log("INTERKMS_REQUEST", f"From {remote_node}", "INTER-KMS")

    def interkms_response(self, key_id: str, remote_node: str):
        self.log(
            "INTERKMS_RESPONSE",
            f"{key_id} → {remote_node}",
            "INTER-KMS"
        )

    # =================================================
    # CRYPTO
    # =================================================

    def encryption(self, key_id: str, bytes_used: int, mode: str = "ETSI"):
        self.log(
            "ENCRYPTION",
            f"Key ID: {key_id} | Bytes: {bytes_used} | Mode: {mode}",
            "APPLICATION"
        )

    def decryption(self, key_id: str, bytes_used: int, mode: str = "ETSI"):
        self.log(
            "DECRYPTION",
            f"Key ID: {key_id} | Bytes: {bytes_used} | Mode: {mode}",
            "APPLICATION"
        )

    # =================================================
    # API
    # =================================================

    def api_call(self, endpoint: str, plane: str):
        self.log("API_CALL", endpoint, plane)

    # =================================================
    # ERROR
    # =================================================

    def error(self, message: str, plane: str = "LOCAL"):
        self.log("ERROR", message, plane)