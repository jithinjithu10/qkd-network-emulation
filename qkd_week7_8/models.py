"""
models.py
----------
Core data models for the QKD Network Stack.

Supports:
- Week 5: Advanced Key Buffering
- Week 6: Policy-Driven KMS
- Week 7: Network Control Layer
- Week 8: Service Interface Layer
"""

from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Union


# =================================================
# WEEK 5 – KEY LIFECYCLE STATES
# =================================================

class KeyState(str, Enum):
    GENERATED = "GENERATED"
    READY = "READY"
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"


# =================================================
# WEEK 5 – KEY ROLE (ENC / DEC SEPARATION)
# =================================================

class KeyRole(str, Enum):
    ENC = "ENC"
    DEC = "DEC"


# =================================================
# WEEK 7 – NODE STATUS
# =================================================

class NodeStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"


# =================================================
# WEEK 7 – LINK STATUS
# =================================================

class LinkStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


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

        # -------------------------------------------------
        # Normalize created_at safely (string or datetime)
        # -------------------------------------------------
        if isinstance(created_at, str):
            self.created_at = datetime.fromisoformat(created_at)
        elif isinstance(created_at, datetime):
            self.created_at = created_at.astimezone(timezone.utc)
        else:
            raise ValueError("Invalid created_at format")

        # Ensure timezone-aware
        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)

        # TTL
        self.ttl = timedelta(seconds=ttl_seconds)

        # Normalize role safely
        self.role = KeyRole(role)

        # Lifecycle state
        self.state = KeyState.GENERATED

        # Session binding
        self.session_id = None

        # Policy metadata
        self.usage_count = 0
        self.freshness_score = 100

    # ---------------------------------------------
    # Expiry Check
    # ---------------------------------------------
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > (self.created_at + self.ttl)

    # ---------------------------------------------
    # Freshness Degradation
    # ---------------------------------------------
    def degrade_freshness(self):
        self.freshness_score = max(0, self.freshness_score - 10)

    # ---------------------------------------------
    # Mark Usage
    # ---------------------------------------------
    def mark_used(self):
        self.usage_count += 1
        self.degrade_freshness()


# =================================================
# WEEK 7 – NODE MODEL
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


# =================================================
# WEEK 7 – LINK ABSTRACTION
# =================================================

class Link:
    """
    Represents a logical QKD link between two nodes.
    """

    def __init__(self, node_a: str, node_b: str, rate: float):
        self.node_a = node_a
        self.node_b = node_b
        self.rate = rate
        self.status = LinkStatus.AVAILABLE
        self.last_updated = datetime.now(timezone.utc)


# =================================================
# WEEK 8 – SESSION ABSTRACTION
# =================================================

class Session:
    """
    Represents a secure communication session.
    """

    def __init__(self, session_id: str, role: Union[KeyRole, str]):
        self.session_id = session_id
        self.role = KeyRole(role)
        self.created_at = datetime.now(timezone.utc)
        self.active = True

    def close(self):
        self.active = False
