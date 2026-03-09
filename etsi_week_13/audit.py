"""
audit.py

ETSI-aligned audit logging system.

Implements:
- Node-aware logging
- Plane-aware logging
- Key lifecycle logging
- API operation logging
- Encryption / Decryption logging
- Inter-node communication logging
- Structured UTC timestamps
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
        """
        Generic structured logger.
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
        self.log(
            "SYSTEM_START",
            "QKD Node started",
            plane="SYSTEM"
        )

    def system_shutdown(self):
        self.log(
            "SYSTEM_STOP",
            "QKD Node stopped",
            plane="SYSTEM"
        )

    # =================================================
    # SESSION EVENTS
    # =================================================

    def session_created(self, session_id: str):
        self.log(
            "SESSION_CREATED",
            f"Session ID: {session_id}",
            plane="APPLICATION"
        )

    def session_closed(self, session_id: str):
        self.log(
            "SESSION_CLOSED",
            f"Session ID: {session_id}",
            plane="APPLICATION"
        )

    def session_expired(self, session_id: str):
        self.log(
            "SESSION_EXPIRED",
            f"Session ID: {session_id}",
            plane="APPLICATION"
        )

    # =================================================
    # KEY EVENTS
    # =================================================

    def key_added(self, key_id: str):
        self.log(
            "KEY_ADDED",
            f"Key ID: {key_id}",
            plane="LOCAL"
        )

    def key_reserved(self, key_id: str, session_id: str):
        self.log(
            "KEY_RESERVED",
            f"Key ID: {key_id} | Session: {session_id}",
            plane="APPLICATION"
        )

    def key_consumed(self, key_id: str):
        self.log(
            "KEY_CONSUMED",
            f"Key ID: {key_id}",
            plane="APPLICATION"
        )

    def key_expired(self, key_id: str):
        self.log(
            "KEY_EXPIRED",
            f"Key ID: {key_id}",
            plane="LOCAL"
        )

    # =================================================
    # INTER-KMS EVENTS
    # =================================================

    def key_shared_with_node(self, key_id: str, remote_node: str):
        self.log(
            "KEY_SHARED",
            f"Key ID: {key_id} | Sent to Node: {remote_node}",
            plane="INTER-KMS"
        )

    def key_received_from_node(self, key_id: str, remote_node: str):
        self.log(
            "KEY_RECEIVED",
            f"Key ID: {key_id} | Received from Node: {remote_node}",
            plane="INTER-KMS"
        )

    def interkms_request(self, remote_node: str):
        self.log(
            "INTERKMS_REQUEST",
            f"Request received from Node: {remote_node}",
            plane="INTER-KMS"
        )

    # =================================================
    # CRYPTO EVENTS (FOR DATA TRANSFER DEMO)
    # =================================================

    def encryption(self, key_id: str):
        self.log(
            "ENCRYPTION",
            f"Message encrypted using Key ID: {key_id}",
            plane="APPLICATION"
        )

    def decryption(self, key_id: str):
        self.log(
            "DECRYPTION",
            f"Message decrypted using Key ID: {key_id}",
            plane="APPLICATION"
        )

    # =================================================
    # API EVENTS
    # =================================================

    def api_call(self, endpoint: str, plane: str):
        self.log(
            "API_CALL",
            f"Endpoint: {endpoint}",
            plane=plane
        )

    # =================================================
    # ERROR EVENTS
    # =================================================

    def error(self, message: str, plane: str = "LOCAL"):
        self.log(
            "ERROR",
            message,
            plane=plane
        )