# audit.py
# CENTRALIZED HYBRID QKD AUDIT LOGGER

from datetime import datetime, timezone
from config import NODE_ID, ENABLE_DEBUG_LOGS


class AuditLogger:

    """
    Centralized QKD-safe audit logger.

    IMPORTANT
    ---------
    Never log:
    - raw quantum keys
    - sifted keys
    - AES secrets
    - quantum states

    Only metadata-safe information
    should be logged.
    """

    def __init__(self):

        self.node_id = NODE_ID

    # =====================================================
    # SANITIZATION
    # =====================================================

    @staticmethod
    def _sanitize(value):

        if value is None:
            return "None"

        value = str(value)

        if len(value) > 300:
            return value[:300] + "..."

        return value.replace("\n", " ")

    # =====================================================
    # CORE LOGGER
    # =====================================================

    def log(self, event_type, message, plane="LOCAL"):

        if not ENABLE_DEBUG_LOGS:
            return

        try:

            timestamp = datetime.now(
                timezone.utc
            ).isoformat()

            event_type = self._sanitize(event_type)
            plane = self._sanitize(plane)
            message = self._sanitize(message)

            log_line = (
                f"[{timestamp}] "
                f"[NODE={self.node_id}] "
                f"[PLANE={plane}] "
                f"[{event_type}] "
                f"{message}"
            )

            print(log_line, flush=True)

        except Exception:

            print(
                "[LOG ERROR] Failed to write audit log",
                flush=True
            )

    # =====================================================
    # SYSTEM EVENTS
    # =====================================================

    def system_start(self):

        self.log(
            "SYSTEM_START",
            "Hybrid QKD node started",
            "SYSTEM"
        )

    def system_stop(self):

        self.log(
            "SYSTEM_STOP",
            "Hybrid QKD node stopped",
            "SYSTEM"
        )

    # =====================================================
    # QUANTUM EVENTS
    # =====================================================

    def quantum_channel_ready(self):

        self.log(
            "QUANTUM_CHANNEL_READY",
            "SimulaQron channel active",
            "QUANTUM"
        )

    def bb84_start(self, session_id):

        self.log(
            "BB84_START",
            f"session={session_id}",
            "QUANTUM"
        )

    def bb84_complete(self, session_id, key_id):

        self.log(
            "BB84_COMPLETE",
            f"session={session_id} key_id={key_id}",
            "QUANTUM"
        )

    def qubit_sent(self, receiver, basis):

        self.log(
            "QUBIT_SENT",
            f"receiver={receiver} basis={basis}",
            "QUANTUM"
        )

    def qubit_received(self, sender, basis):

        self.log(
            "QUBIT_RECEIVED",
            f"sender={sender} basis={basis}",
            "QUANTUM"
        )

    def basis_match(self, position):

        self.log(
            "BASIS_MATCH",
            f"position={position}",
            "QUANTUM"
        )

    def basis_mismatch(self, position):

        self.log(
            "BASIS_MISMATCH",
            f"position={position}",
            "QUANTUM"
        )

    def sifted_key_generated(self, key_id, key_length):

        self.log(
            "SIFTED_KEY",
            f"id={key_id} bits={key_length}",
            "QUANTUM"
        )

    # =====================================================
    # KMS EVENTS
    # =====================================================

    def key_added(self, key_id, origin="LOCAL"):

        self.log(
            "KEY_ADDED",
            f"id={key_id} origin={origin}",
            "KMS"
        )

    def key_served(self, key_id):

        self.log(
            "KEY_SERVED",
            f"id={key_id}",
            "KMS"
        )

    def key_used(self, key_id):

        self.log(
            "KEY_USED",
            f"id={key_id}",
            "APP"
        )

    def key_consumed(self, key_id):

        self.log(
            "KEY_CONSUMED",
            f"id={key_id}",
            "APP"
        )

    def key_expired(self, key_id):

        self.log(
            "KEY_EXPIRED",
            f"id={key_id}",
            "KMS"
        )

    def key_rotated(self, old_key, new_key):

        self.log(
            "KEY_ROTATED",
            f"old={old_key} new={new_key}",
            "KMS"
        )

    def runtime_regeneration(self, session_id):

        self.log(
            "KEY_REGENERATION",
            f"session={session_id}",
            "QUANTUM"
        )

    # =====================================================
    # SYNCHRONIZATION EVENTS
    # =====================================================

    def sync_start(self, key_id):

        self.log(
            "SYNC_START",
            f"id={key_id}",
            "SYNC"
        )

    def sync_progress(self, key_id):

        self.log(
            "SYNC_PROGRESS",
            f"id={key_id}",
            "SYNC"
        )

    def sync_success(self, key_id):

        self.log(
            "SYNC_OK",
            f"id={key_id}",
            "SYNC"
        )

    def sync_fail(self, key_id):

        self.log(
            "SYNC_FAIL",
            f"id={key_id}",
            "SYNC"
        )

    def sync_metadata(self, key_id, session_id, sync_index):

        self.log(
            "SYNC_METADATA",
            (
                f"id={key_id} "
                f"session={session_id} "
                f"sync_index={sync_index}"
            ),
            "SYNC"
        )

    def hash_verification(self, key_id, verified):

        status = (
            "MATCH"
            if verified
            else "MISMATCH"
        )

        self.log(
            "SHA256_VERIFY",
            f"id={key_id} status={status}",
            "SYNC"
        )

    def synchronization_complete(self, key_id):

        self.log(
            "SYNC_COMPLETE",
            f"id={key_id}",
            "SYNC"
        )

    # =====================================================
    # CLASSICAL CHANNEL EVENTS
    # =====================================================

    def metadata_shared(self, key_id, target):

        self.log(
            "METADATA_SHARED",
            f"id={key_id} target={target}",
            "CLASSICAL"
        )

    def session_created(self, session_id):

        self.log(
            "SESSION_CREATED",
            f"session={session_id}",
            "CLASSICAL"
        )

    def session_closed(self, session_id):

        self.log(
            "SESSION_CLOSED",
            f"session={session_id}",
            "CLASSICAL"
        )

    # =====================================================
    # INTER-KMS EVENTS
    # =====================================================

    def interkms_request(self, requester):

        self.log(
            "INTERKMS_REQUEST",
            f"from={requester}",
            "INTER-KMS"
        )

    def interkms_response(self, key_id, requester):

        self.log(
            "INTERKMS_RESPONSE",
            f"id={key_id} requester={requester}",
            "INTER-KMS"
        )

    # =====================================================
    # CRYPTO EVENTS
    # =====================================================

    def encryption(self, key_id, bytes_used, mode):

        self.log(
            "AES_GCM_ENCRYPT",
            (
                f"id={key_id} "
                f"bytes={bytes_used} "
                f"mode={mode}"
            ),
            "APP"
        )

    def decryption(self, key_id, bytes_used, mode):

        self.log(
            "AES_GCM_DECRYPT",
            (
                f"id={key_id} "
                f"bytes={bytes_used} "
                f"mode={mode}"
            ),
            "APP"
        )

    # =====================================================
    # API EVENTS
    # =====================================================

    def api(self, endpoint):

        self.log(
            "API_CALL",
            endpoint,
            "API"
        )

    def api_auth_success(self, endpoint):

        self.log(
            "API_AUTH_OK",
            endpoint,
            "API"
        )

    def api_auth_fail(self, endpoint):

        self.log(
            "API_AUTH_FAIL",
            endpoint,
            "API"
        )

    # =====================================================
    # NETWORK EVENTS
    # =====================================================

    def ngrok_connected(self, url):

        self.log(
            "NGROK_CONNECTED",
            url,
            "NETWORK"
        )

    def reverse_proxy_active(self):

        self.log(
            "REVERSE_PROXY",
            "Caddy reverse proxy active",
            "NETWORK"
        )

    def peer_connected(self, peer):

        self.log(
            "PEER_CONNECTED",
            peer,
            "NETWORK"
        )

    # =====================================================
    # SECURITY EVENTS
    # =====================================================

    def intrusion_detected(self, details):

        self.log(
            "INTRUSION_ALERT",
            details,
            "SECURITY"
        )

    def qber_alert(self, qber):

        self.log(
            "QBER_ALERT",
            f"qber={qber}",
            "SECURITY"
        )

    # =====================================================
    # ERROR EVENTS
    # =====================================================

    def error(self, msg, plane="ERROR"):

        self.log(
            "ERROR",
            msg,
            plane
        )