"""
policy.py
----------

Full ETSI-Aligned Policy Engine
Weeks 6 – 12 Complete

Implements:
- Per-application quota enforcement
- Freshness + TTL validation
- Adaptive refill logic
- Role-aware decisions
- Link-aware allocation control
- Node-level throttling
- Stress-mode behavior
- Key exhaustion detection
- Metrics hooks (Week 12 ready)
"""

from collections import defaultdict
from models import KeyRole, KeyState
from config import (
    PER_APPLICATION_LIMIT,
    REFILL_THRESHOLD,
    MIN_FRESHNESS_SCORE,
    ENABLE_STRESS_MODE,
    KEY_EXHAUSTION_TEST_RATE,
    DEFAULT_LINK_RATE
)


class PolicyEngine:

    def __init__(self):

        # -------------------------------
        # Static policy configuration
        # -------------------------------
        self.per_app_limit = PER_APPLICATION_LIMIT
        self.min_freshness = MIN_FRESHNESS_SCORE
        self.refill_threshold = REFILL_THRESHOLD

        # -------------------------------
        # Runtime tracking
        # -------------------------------
        self.app_usage_counter = defaultdict(int)
        self.node_allocation_counter = defaultdict(int)

        self.failed_allocations = 0
        self.total_allocations = 0

    # =================================================
    # PER-APPLICATION QUOTA
    # =================================================
    def allow_request(self, app_id: str, requested_keys: int) -> bool:

        current_usage = self.app_usage_counter[app_id]

        if current_usage + requested_keys > self.per_app_limit:
            return False

        self.app_usage_counter[app_id] += requested_keys
        return True

    # =================================================
    # RESET APP USAGE (Session End)
    # =================================================
    def reset_app_usage(self, app_id: str):
        self.app_usage_counter[app_id] = 0

    # =================================================
    # FRESHNESS + STATE FILTERING
    # =================================================
    def filter_valid_keys(self, keys: list):

        valid_keys = []

        for key in keys:

            if key.state != KeyState.READY:
                continue

            if key.is_expired():
                continue

            if key.freshness_score < self.min_freshness:
                continue

            valid_keys.append(key)

        return valid_keys

    # =================================================
    # GLOBAL REFILL DECISION
    # =================================================
    def needs_refill(self, qbuffer_size: int) -> bool:
        return qbuffer_size < self.refill_threshold

    # =================================================
    # ROLE-AWARE REFILL
    # =================================================
    def needs_role_refill(self, enc_size: int, dec_size: int):

        return {
            KeyRole.ENC: enc_size < self.refill_threshold,
            KeyRole.DEC: dec_size < self.refill_threshold
        }

    # =================================================
    # LINK-AWARE ALLOCATION CONTROL (Week 11)
    # =================================================
    def allow_allocation_based_on_link(self, link_info: dict) -> bool:

        if not link_info:
            return False

        status = link_info.get("status")
        rate = link_info.get("rate", 0)

        # Block completely if unavailable
        if status != "AVAILABLE":
            return False

        # If link degraded significantly, restrict allocation
        if rate < (DEFAULT_LINK_RATE * 0.2):
            return False

        return True

    # =================================================
    # ADAPTIVE ALLOCATION SCALING (Week 11)
    # =================================================
    def adaptive_allocation_limit(self, link_info: dict) -> int:

        if not link_info:
            return 1

        rate = link_info.get("rate", DEFAULT_LINK_RATE)

        # Scale allocation proportional to link rate
        scale_factor = rate / DEFAULT_LINK_RATE

        dynamic_limit = max(1, int(self.per_app_limit * scale_factor))

        return dynamic_limit

    # =================================================
    # NODE-LEVEL RATE CONTROL
    # =================================================
    def record_node_allocation(self, node_id: str):
        self.node_allocation_counter[node_id] += 1
        self.total_allocations += 1

    def reset_node_allocation(self, node_id: str):
        self.node_allocation_counter[node_id] = 0

    # =================================================
    # KEY EXHAUSTION DETECTION (Week 11)
    # =================================================
    def record_failed_allocation(self):
        self.failed_allocations += 1

    def is_exhaustion_detected(self) -> bool:

        if ENABLE_STRESS_MODE:

            if self.failed_allocations > KEY_EXHAUSTION_TEST_RATE:
                return True

        return False

    # =================================================
    # METRICS EXPORT (Week 12)
    # =================================================
    def get_policy_metrics(self):

        return {
            "total_allocations": self.total_allocations,
            "failed_allocations": self.failed_allocations,
            "tracked_applications": len(self.app_usage_counter),
            "tracked_nodes": len(self.node_allocation_counter)
        }
