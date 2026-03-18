"""
audit.py

Advanced ETSI-aligned audit logging system.

Now supports:
- Key synchronization tracking
- Session ↔ key mapping
- Sync index debugging
- Cross-node traceability
"""

from datetime import datetime, timezone
from config import NODE_ID


class AuditLogger:

    def __init__(self):
        self.node_id = NODE_ID

    # =================================================
    # CORE LOG FUNCTION
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
    # SYSTEM EVENTS
    # =================================================

    def system_start(self):
        self.log("SYSTEM_START", "QKD Node started", plane="SYSTEM")

    def system_shutdown(self):
        self.log("SYSTEM_STOP", "QKD Node stopped", plane="SYSTEM")

    # =================================================
    # SESSION EVENTS
    # =================================================

    def session_created(self, session_id: str):
        self.log("SESSION_CREATED", f"Session ID: {session_id}", "APPLICATION")

    def session_closed(self, session_id: str):
        self.log("SESSION_CLOSED", f"Session ID: {session_id}", "APPLICATION")

    def session_expired(self, session_id: str):
        self.log("SESSION_EXPIRED", f"Session ID: {session_id}", "APPLICATION")

    #  NEW → SESSION ↔ KEY LINK
    def session_key_mapping(self, session_id: str, key_id: str):
        self.log(
            "SESSION_KEY_MAP",
            f"Session: {session_id} → Key: {key_id}",
            "APPLICATION"
        )

    # =================================================
    # KEY EVENTS
    # =================================================

    def key_added(self, key_id: str, origin: str = "LOCAL"):
        self.log(
            "KEY_ADDED",
            f"Key ID: {key_id} | Origin: {origin}",
            "LOCAL"
        )

    def key_reserved(self, key_id: str, session_id: str):
        self.log(
            "KEY_RESERVED",
            f"Key ID: {key_id} | Session: {session_id}",
            "APPLICATION"
        )

    def key_consumed(self, key_id: str):
        self.log("KEY_CONSUMED", f"Key ID: {key_id}", "APPLICATION")

    def key_expired(self, key_id: str):
        self.log("KEY_EXPIRED", f"Key ID: {key_id}", "LOCAL")

    #  NEW → KEY FETCH (ETSI API)
    def key_served(self, key_id: str):
        self.log(
            "KEY_SERVED",
            f"Key ID: {key_id} served via ETSI API",
            "APPLICATION"
        )

    # =================================================
    # INTER-KMS EVENTS
    # =================================================

    def key_shared_with_node(self, key_id: str, remote_node: str):
        self.log(
            "KEY_SHARED",
            f"Key ID: {key_id} | Sent to Node: {remote_node}",
            "INTER-KMS"
        )

    def key_received_from_node(self, key_id: str, remote_node: str):
        self.log(
            "KEY_RECEIVED",
            f"Key ID: {key_id} | Received from Node: {remote_node}",
            "INTER-KMS"
        )

    def interkms_request(self, remote_node: str):
        self.log(
            "INTERKMS_REQUEST",
            f"Request from Node: {remote_node}",
            "INTER-KMS"
        )

    #  NEW → INTER-KMS RESPONSE TRACE
    def interkms_response(self, key_id: str, remote_node: str):
        self.log(
            "INTERKMS_RESPONSE",
            f"Key ID: {key_id} sent to {remote_node}",
            "INTER-KMS"
        )

    # =================================================
    # SYNC EVENTS
    # =================================================

    def sync_key_generated(self, key_id: str):
        self.log(
            "SYNC_KEY_GENERATED",
            f"Key ID: {key_id} generated via shared seed",
            "SYNC"
        )

    def sync_key_matched(self, key_id: str):
        self.log(
            "SYNC_KEY_MATCH",
            f"Key ID: {key_id} matched across nodes",
            "SYNC"
        )

    #  NEW → SYNC INDEX TRACKING
    def sync_progress(self, index: int):
        self.log(
            "SYNC_PROGRESS",
            f"Current sync index: {index}",
            "SYNC"
        )

    # =================================================
    # CRYPTO EVENTS
    # =================================================

    def encryption(self, key_id: str, mode: str = "ETSI"):
        self.log(
            "ENCRYPTION",
            f"Key ID: {key_id} | Mode: {mode}",
            "APPLICATION"
        )

    def decryption(self, key_id: str, mode: str = "ETSI"):
        self.log(
            "DECRYPTION",
            f"Key ID: {key_id} | Mode: {mode}",
            "APPLICATION"
        )

    # =================================================
    # API EVENTS
    # =================================================

    def api_call(self, endpoint: str, plane: str):
        self.log("API_CALL", f"Endpoint: {endpoint}", plane)

    # =================================================
    # ERROR EVENTS
    # =================================================

    def error(self, message: str, plane: str = "LOCAL"):
        self.log("ERROR", message, plane)