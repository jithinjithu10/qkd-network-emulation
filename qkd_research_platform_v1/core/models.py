"""
models.py
---------

Research-Grade QKD Network Stack Models
ETSI-Aligned | OpenQKD-Aware | Novel Simulation Ready

Supports:
- Weeks 1–3  : Quantum emulation metadata
- Weeks 4–6  : Advanced KMS lifecycle
- Weeks 7–8  : Network control plane
- Weeks 9–10 : Secure application transfer
- Weeks 11–12: Stress, attack & metrics evaluation
"""

from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Union
import uuid


# =================================================
# ENUM DEFINITIONS
# =================================================

class KeyState(str, Enum):
    GENERATED = "GENERATED"
    READY = "READY"
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class KeyRole(str, Enum):
    ENC = "ENC"
    DEC = "DEC"


class NodeStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"


class LinkStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    DEGRADED = "DEGRADED"


class TransferStatus(str, Enum):
    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# =================================================
# EXPERIMENT CONTEXT (Week 12)
# =================================================

class ExperimentContext:
    """
    Enables reproducible academic experiments.
    """

    def __init__(self, parameters: Dict):
        self.experiment_id = str(uuid.uuid4())
        self.parameters = parameters
        self.started_at = datetime.now(timezone.utc)
        self.notes = ""


# =================================================
# QUANTUM KEY MODEL (Weeks 1–6)
# =================================================

class Key:
    """
    Represents a QKD-generated cryptographic key
    with quantum-level metadata.
    """

    def __init__(
        self,
        key_id: str,
        key_value: str,
        key_size: int,
        ttl_seconds: int,
        role: Union[KeyRole, str],
        source_node: str,
        bit_error_rate: float = 0.0,
        entropy_score: float = 1.0,
        amplification_factor: float = 1.0,
        link_quality: float = 1.0
    ):

        self.key_id = key_id
        self.key_value = key_value
        self.key_size = key_size
        self.created_at = datetime.now(timezone.utc)
        self.ttl = timedelta(seconds=ttl_seconds)

        self.role = KeyRole(role)
        self.state = KeyState.GENERATED
        self.session_id: Optional[str] = None

        # Quantum metadata (Novel contribution)
        self.source_node = source_node
        self.bit_error_rate = bit_error_rate
        self.entropy_score = entropy_score
        self.amplification_factor = amplification_factor
        self.link_quality = link_quality

        # Policy metadata
        self.usage_count = 0
        self.freshness_score = 100

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > (self.created_at + self.ttl)

    def mark_used(self):
        self.usage_count += 1
        self.freshness_score = max(0, self.freshness_score - 10)


# =================================================
# NODE MODEL (Week 7)
# =================================================

class Node:
    """
    Logical QKD node representation.
    """

    def __init__(self, node_id: str, ip_address: str):
        self.node_id = node_id
        self.ip_address = ip_address
        self.status = NodeStatus.ONLINE
        self.registered_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)


# =================================================
# LINK MODEL (Weeks 2 + 7 + 11)
# =================================================

class Link:
    """
    Physical + Logical QKD link abstraction.
    """

    def __init__(
        self,
        node_a: str,
        node_b: str,
        rate: float,
        latency_ms: float = 1.0,
        noise_probability: float = 0.0,
        packet_loss_probability: float = 0.0
    ):

        self.node_a = node_a
        self.node_b = node_b

        self.rate = rate
        self.latency_ms = latency_ms
        self.noise_probability = noise_probability
        self.packet_loss_probability = packet_loss_probability

        self.status = LinkStatus.AVAILABLE
        self.last_updated = datetime.now(timezone.utc)

    def degrade(self, new_rate: float, new_latency: float):
        self.rate = new_rate
        self.latency_ms = new_latency
        self.status = LinkStatus.DEGRADED
        self.last_updated = datetime.now(timezone.utc)

    def fail(self):
        self.status = LinkStatus.UNAVAILABLE
        self.last_updated = datetime.now(timezone.utc)

    def restore(self):
        self.status = LinkStatus.AVAILABLE
        self.last_updated = datetime.now(timezone.utc)


# =================================================
# SESSION MODEL (Week 8–9)
# =================================================

class Session:
    """
    Secure communication session abstraction.
    """

    def __init__(self, app_id: str, role: Union[KeyRole, str]):
        self.session_id = str(uuid.uuid4())
        self.app_id = app_id
        self.role = KeyRole(role)
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
        self.keys: Dict[str, Key] = {}

    def store_key(self, key: Key):
        self.keys[key.key_id] = key

    def get_key(self, key_id: str) -> Optional[Key]:
        return self.keys.get(key_id)

    def delete_key(self, key_id: str):
        if key_id in self.keys:
            del self.keys[key_id]


# =================================================
# SECURE TRANSFER MODEL (Week 10)
# =================================================

class SecureTransfer:
    """
    Represents QKD-protected data transfer.
    """

    def __init__(self, session_id: str):
        self.transfer_id = str(uuid.uuid4())
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
# METRICS ENGINE MODEL (Week 12)
# =================================================

class Metrics:
    """
    Collects system-wide evaluation metrics.
    """

    def __init__(self):

        # Key metrics
        self.total_keys_generated = 0
        self.total_keys_consumed = 0
        self.failed_allocations = 0

        # Transfer metrics
        self.total_transfers = 0
        self.failed_transfers = 0

        # Latency & throughput
        self.allocation_latency_history: List[float] = []
        self.transfer_latency_history: List[float] = []
        self.throughput_history: List[float] = []

        # Stress & attack tracking
        self.link_degradation_events = 0
        self.key_exhaustion_events = 0

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

    def record_allocation_latency(self, latency: float):
        self.allocation_latency_history.append(latency)

    def record_transfer_latency(self, latency: float):
        self.transfer_latency_history.append(latency)

    def record_throughput(self, throughput: float):
        self.throughput_history.append(throughput)