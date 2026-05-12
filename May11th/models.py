# models.py
# UPDATED FOR DISTRIBUTED HYBRID QUANTUM-CLASSICAL QKD ARCHITECTURE

from enum import Enum

from datetime import (
    datetime,
    timezone,
    timedelta
)

import hashlib
import hmac
import secrets
import uuid


# =========================================================
# HELPERS
# =========================================================

def time_now():

    return datetime.now(
        timezone.utc
    ).isoformat()


# =========================================================
# KEY STATES
# =========================================================

class KeyState(str, Enum):

    READY = "READY"

    SYNCHRONIZED = "SYNCHRONIZED"

    VERIFIED = "VERIFIED"

    CONSUMED = "CONSUMED"

    EXPIRED = "EXPIRED"


# =========================================================
# SESSION STATES
# =========================================================

class SessionState(str, Enum):

    ACTIVE = "ACTIVE"

    VERIFIED = "VERIFIED"

    CLOSED = "CLOSED"

    EXPIRED = "EXPIRED"


# =========================================================
# QUANTUM KEY MODEL
# =========================================================

class Key:

    """
    Distributed Hybrid QKD Session Key

    Responsibilities
    ----------------
    - BB84-derived key representation
    - synchronization lifecycle tracking
    - ETSI-style metadata abstraction
    - AES-GCM session coordination
    - distributed verification state

    IMPORTANT
    ---------
    Public classical channels MUST NEVER expose:
    - raw key material
    - BB84 entropy
    - quantum state information
    """

    def __init__(

        self,

        key_id: str,

        key_value: str,

        key_size: int = 256,

        ttl_seconds: int = 3600,

        origin_node: str = "LOCAL_BB84",

        protocol: str = "BB84",

        session_id: str = None,

        sync_index: int = 0,

        epoch: int = 0
    ):

        # =================================================
        # KEY ID VALIDATION
        # =================================================

        if key_id is None:

            raise ValueError(
                "key_id required"
            )

        key_id = str(key_id)

        if not key_id.isdigit():

            raise ValueError(

                "key_id must be numeric "
                "for deterministic synchronization"
            )

        # =================================================
        # KEY MATERIAL VALIDATION
        # =================================================

        if not key_value:

            raise ValueError(
                "key_value required"
            )

        if not isinstance(key_value, str):

            raise ValueError(
                "key_value must be hex string"
            )

        try:

            key_bytes = bytes.fromhex(
                key_value
            )

        except Exception:

            raise ValueError(
                "Invalid hexadecimal key"
            )

        # =================================================
        # AES-256 VALIDATION
        # =================================================

        if len(key_bytes) != 32:

            raise ValueError(

                "AES-256 requires exactly "
                "32-byte key material"
            )

        # =================================================
        # BASIC IDENTITY
        # =================================================

        self.key_id = key_id

        self.key_value = key_value

        self.key_size = key_size

        self.origin_node = origin_node

        self.protocol = protocol

        self.sync_index = sync_index

        self.epoch = epoch

        # =================================================
        # SESSION INFO
        # =================================================

        self.session_id = (

            session_id

            if session_id

            else str(uuid.uuid4())[:8]
        )

        self.session_state = (
            SessionState.ACTIVE
        )

        # =================================================
        # TIMESTAMPS
        # =================================================

        self.created_at = datetime.now(
            timezone.utc
        )

        self.ttl = timedelta(
            seconds=ttl_seconds
        )

        self.expires_at = (
            self.created_at + self.ttl
        )

        self.used_at = None

        self.synchronized_at = None

        self.verified_at = None

        self.closed_at = None

        # =================================================
        # KEY STATE
        # =================================================

        self.state = KeyState.READY

        self.verified = False

        # =================================================
        # USAGE TRACKING
        # =================================================

        self.bytes_used = 0

        self.max_bytes = 32

        self.message_counter = 0

        # =================================================
        # REPLAY PROTECTION
        # =================================================

        self.last_nonce = None

        self.last_activity = time_now()

        # =================================================
        # FINGERPRINTS
        # =================================================

        self.fingerprint = (
            self._compute_fingerprint()
        )

        self.short_fingerprint = (
            self.fingerprint[:16]
        )

        self.session_digest = (
            self._compute_session_digest()
        )

    # =====================================================
    # SHA-256 FINGERPRINT
    # =====================================================

    def _compute_fingerprint(self):

        """
        SHA-256 synchronization fingerprint.

        NEVER expose raw key material.
        """

        return hashlib.sha256(

            bytes.fromhex(
                self.key_value
            )

        ).hexdigest()

    # =====================================================
    # SESSION DIGEST
    # =====================================================

    def _compute_session_digest(self):

        payload = (

            f"{self.protocol}|"
            f"{self.session_id}|"
            f"{self.key_id}|"
            f"{self.sync_index}|"
            f"{self.origin_node}|"
            f"{self.epoch}"

        ).encode()

        return hashlib.sha256(
            payload
        ).hexdigest()

    # =====================================================
    # CONSTANT-TIME HASH VERIFY
    # =====================================================

    def verify_hash(
        self,
        received_hash
    ):

        verified = hmac.compare_digest(

            self.fingerprint,

            received_hash
        )

        if verified:

            self.mark_verified()

        return verified

    # =====================================================
    # MATCH TWO KEYS
    # =====================================================

    def matches(
        self,
        other_key
    ):

        if not other_key:
            return False

        return hmac.compare_digest(

            self.fingerprint,

            other_key.fingerprint
        )

    # =====================================================
    # SYNCHRONIZATION
    # =====================================================

    def mark_synchronized(self):

        self.state = KeyState.SYNCHRONIZED

        self.synchronized_at = datetime.now(
            timezone.utc
        )

        self.last_activity = time_now()

    # =====================================================
    # VERIFICATION
    # =====================================================

    def mark_verified(self):

        self.state = KeyState.VERIFIED

        self.session_state = (
            SessionState.VERIFIED
        )

        self.verified = True

        self.verified_at = datetime.now(
            timezone.utc
        )

        self.last_activity = time_now()

    # =====================================================
    # CONSUME KEY
    # =====================================================

    def consume(self):

        if self.is_expired():

            self.expire()

            raise ValueError(
                f"Key {self.key_id} expired"
            )

        if self.state not in [
            KeyState.READY,
            KeyState.SYNCHRONIZED,
            KeyState.VERIFIED
        ]:

            raise ValueError(

                f"Key {self.key_id} "
                f"not usable "
                f"(state={self.state})"
            )

        self.state = KeyState.CONSUMED

        self.used_at = datetime.now(
            timezone.utc
        )

        self.last_activity = time_now()

    # =====================================================
    # EXPIRE KEY
    # =====================================================

    def expire(self):

        self.state = KeyState.EXPIRED

        self.session_state = (
            SessionState.EXPIRED
        )

        self.last_activity = time_now()

    # =====================================================
    # SESSION CLOSE
    # =====================================================

    def close_session(self):

        self.session_state = (
            SessionState.CLOSED
        )

        self.closed_at = datetime.now(
            timezone.utc
        )

        self.last_activity = time_now()

    # =====================================================
    # EXPIRY CHECK
    # =====================================================

    def is_expired(self):

        return (
            datetime.now(timezone.utc)
            > self.expires_at
        )

    # =====================================================
    # BYTE USAGE
    # =====================================================

    def add_usage(
        self,
        count
    ):

        self.bytes_used += count

        self.last_activity = time_now()

    # =====================================================
    # MESSAGE TRACKING
    # =====================================================

    def increment_message_counter(self):

        self.message_counter += 1

        self.last_activity = time_now()

    # =====================================================
    # NONCE TRACKING
    # =====================================================

    def register_nonce(
        self,
        nonce=None
    ):

        if nonce is None:

            nonce = secrets.token_hex(16)

        self.last_nonce = nonce

        self.last_activity = time_now()

        return nonce

    # =====================================================
    # USAGE LIMIT
    # =====================================================

    def usage_exceeded(self):

        return (
            self.bytes_used
            >= self.max_bytes
        )

    # =====================================================
    # SAFE PUBLIC METADATA
    # =====================================================

    def safe_metadata(self):

        """
        Public classical channel metadata.

        NEVER expose raw quantum key material.
        """

        return {

            "key_id":
                self.key_id,

            "protocol":
                self.protocol,

            "session_id":
                self.session_id,

            "sync_index":
                self.sync_index,

            "epoch":
                self.epoch,

            "verified":
                self.verified,

            "fingerprint":
                self.short_fingerprint,

            "session_digest":
                self.session_digest[:16],

            "origin":
                self.origin_node,

            "state":
                self.state,

            "session_state":
                self.session_state
        }

    # =====================================================
    # INTERNAL SERIALIZATION
    # =====================================================

    def to_dict(self):

        """
        Internal serialization.

        WARNING:
        Contains raw key material.
        NEVER expose publicly.
        """

        return {

            # ---------------------------------------------
            # KEY INFO
            # ---------------------------------------------

            "key_id":
                self.key_id,

            "key":
                self.key_value,

            "size":
                self.key_size,

            # ---------------------------------------------
            # PROTOCOL
            # ---------------------------------------------

            "protocol":
                self.protocol,

            "origin":
                self.origin_node,

            # ---------------------------------------------
            # SESSION
            # ---------------------------------------------

            "session_id":
                self.session_id,

            "session_state":
                self.session_state,

            "session_digest":
                self.session_digest,

            # ---------------------------------------------
            # SYNCHRONIZATION
            # ---------------------------------------------

            "sync_index":
                self.sync_index,

            "epoch":
                self.epoch,

            "verified":
                self.verified,

            # ---------------------------------------------
            # HASHES
            # ---------------------------------------------

            "fingerprint":
                self.fingerprint,

            "short_fingerprint":
                self.short_fingerprint,

            # ---------------------------------------------
            # STATE
            # ---------------------------------------------

            "state":
                self.state,

            # ---------------------------------------------
            # USAGE
            # ---------------------------------------------

            "bytes_used":
                self.bytes_used,

            "max_bytes":
                self.max_bytes,

            "message_counter":
                self.message_counter,

            # ---------------------------------------------
            # REPLAY
            # ---------------------------------------------

            "last_nonce":
                self.last_nonce,

            # ---------------------------------------------
            # TIMESTAMPS
            # ---------------------------------------------

            "created_at":
                self.created_at.isoformat(),

            "expires_at":
                self.expires_at.isoformat(),

            "used_at":
                (
                    self.used_at.isoformat()
                    if self.used_at
                    else None
                ),

            "synchronized_at":
                (
                    self.synchronized_at.isoformat()
                    if self.synchronized_at
                    else None
                ),

            "verified_at":
                (
                    self.verified_at.isoformat()
                    if self.verified_at
                    else None
                ),

            "closed_at":
                (
                    self.closed_at.isoformat()
                    if self.closed_at
                    else None
                ),

            "last_activity":
                self.last_activity
        }

    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (

            f"<QuantumKey "

            f"id={self.key_id} "

            f"session={self.session_id} "

            f"state={self.state} "

            f"verified={self.verified} "

            f"protocol={self.protocol}>"
        )