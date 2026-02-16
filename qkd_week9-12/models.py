"""
models.py
----------

Core data models for Full QKD Network Stack
Weeks 1 – 12 Complete

Supports:
- Key lifecycle (Week 5–6)
- Network control plane (Week 7)
- Service abstraction (Week 8)
- Application layer (Week 9)
- Secure transfer layer (Week 10)
- Stress testing (Week 11)
- Metrics & evaluation (Week 12)
"""

from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Union, Optional


# =================================================
# KEY LIFECYCLE STATES (ETSI-aligned logical states)
# =================================================

class KeyState(str, Enum):
    GENERATED = "GENERATED"
    READY = "READY"
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


# =================================================
# KEY ROLE (ENC / DEC separation)
# =================================================

class KeyRole(str, Enum):
    ENC = "ENC"
    DEC = "DEC"


# =================================================
# NODE STATUS (Control Plane)
# =================================================

class NodeStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"


# =================================================
# LINK STATUS
# =================================================

class LinkStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    DEGRADED = "DEGRADED"


# =================================================
# TRANSFER STATUS (Week 10)
# =================================================

class TransferStatus(str, Enum):
    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# =================================================
# KEY DATA MODEL
# =================================================

class Key:
    """
    Represents a cryptographic key managed by the Central KMS.
    """

    def __init__(
        self,
        key_id: str,
        key_value: str,
        key_size: int,
        created_at: Union[str, datetime],
        ttl_seconds: int,
        role: Union[KeyRole, str]
    ):

        self.key_id = key_id
        self.key_value = key_value
        self.key_size = key_size

        # Normalize timestamp
        if isinstance(created_at, str):
            self.created_at = datetime.fromisoformat(created_at)
        elif isinstance(created_at, datetime):
            self.created_at = created_at.astimezone(timezone.utc)
        else:
            raise ValueError("Invalid created_at format")

        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)

        self.ttl = timedelta(seconds=ttl_seconds)
        self.role = KeyRole(role)

        self.state = KeyState.GENERATED
        self.session_id: Optional[str] = None

        # Policy metadata
        self.usage_count = 0
        self.freshness_score = 100

    # -------------------------------------------------
    # Expiry
    # -------------------------------------------------
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > (self.created_at + self.ttl)

    # -------------------------------------------------
    # Usage Tracking
    # -------------------------------------------------
    def mark_used(self):
        self.usage_count += 1
        self.freshness_score = max(0, self.freshness_score - 10)


# =================================================
# NODE MODEL (Control Plane)
# =================================================

class Node:
    """
    Represents a QKD node in the logical topology.
    """

    def __init__(self, node_id: str, ip_address: str):
        self.node_id = node_id
        self.ip_address = ip_address
        self.status = NodeStatus.ONLINE
        self.registered_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)


# =================================================
# LINK MODEL
# =================================================

class Link:
    """
    Logical QKD link between two nodes.
    """

    def __init__(self, node_a: str, node_b: str, rate: float):
        self.node_a = node_a
        self.node_b = node_b
        self.rate = rate
        self.status = LinkStatus.AVAILABLE
        self.last_updated = datetime.now(timezone.utc)

    def degrade(self, new_rate: float):
        self.rate = new_rate
        self.status = LinkStatus.DEGRADED
        self.last_updated = datetime.now(timezone.utc)

    def fail(self):
        self.status = LinkStatus.UNAVAILABLE
        self.last_updated = datetime.now(timezone.utc)

    def restore(self):
        self.status = LinkStatus.AVAILABLE
        self.last_updated = datetime.now(timezone.utc)


# =================================================
# SESSION MODEL (Week 8 + 9)
# =================================================

class Session:
    """
    Secure communication session abstraction.
    """

    def __init__(self, session_id: str, role: Union[KeyRole, str], app_id: str):
        self.session_id = session_id
        self.role = KeyRole(role)
        self.app_id = app_id
        self.created_at = datetime.now(timezone.utc)
        self.active = True
        self.keys_used = 0

    def close(self):
        self.active = False

    def increment_key_usage(self):
        self.keys_used += 1


# =================================================
# APPLICATION KEY STORE (Week 9)
# =================================================

class ApplicationKeyStore:
    """
    Stores keys locally at application side.
    """

    def __init__(self):
        self.keys = {}

    def store_key(self, key: Key):
        self.keys[key.key_id] = key

    def get_key(self, key_id: str):
        return self.keys.get(key_id)

    def delete_key(self, key_id: str):
        if key_id in self.keys:
            del self.keys[key_id]


# =================================================
# DATA TRANSFER MODEL (Week 10)
# =================================================

class SecureTransfer:
    """
    Represents a QKD-protected data transfer session.
    """

    def __init__(self, transfer_id: str, session_id: str):
        self.transfer_id = transfer_id
        self.session_id = session_id
        self.status = TransferStatus.INITIATED
        self.bytes_transferred = 0
        self.started_at = datetime.now(timezone.utc)
        self.completed_at = None

    def update_progress(self, bytes_chunk: int):
        self.bytes_transferred += bytes_chunk
        self.status = TransferStatus.IN_PROGRESS

    def complete(self):
        self.status = TransferStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def fail(self):
        self.status = TransferStatus.FAILED


# =================================================
# METRICS MODEL (Week 12)
# =================================================

class Metrics:
    """
    Collects system evaluation metrics.
    """

    def __init__(self):
        self.total_keys_generated = 0
        self.total_keys_consumed = 0
        self.failed_allocations = 0
        self.total_transfers = 0
        self.failed_transfers = 0

    def record_key_generated(self):
        self.total_keys_generated += 1

    def record_key_consumed(self):
        self.total_keys_consumed += 1

    def record_failed_allocation(self):
        self.failed_allocations += 1

    def record_transfer(self, success: bool):
        self.total_transfers += 1
        if not success:
            self.failed_transfers += 1
