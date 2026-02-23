"""
policy.py
---------

Research-Grade ETSI-Aligned Policy Engine
Buffer-Aware | Quantum-Aware | Link-Aware | Mode-Controlled
"""

from collections import defaultdict
from statistics import mean
from models import KeyRole, KeyState
from config import (
    PER_APPLICATION_LIMIT,
    REFILL_THRESHOLD,
    MIN_FRESHNESS_SCORE,
    KEY_EXHAUSTION_TEST_RATE,
    DEFAULT_LINK_RATE
)


class PolicyEngine:

    def __init__(self):

        # Static config
        self.per_app_limit = PER_APPLICATION_LIMIT
        self.min_freshness = MIN_FRESHNESS_SCORE
        self.refill_threshold = REFILL_THRESHOLD

        # Baseline thresholds
        self.base_max_qber = 0.11
        self.base_min_entropy = 0.85

        # Active thresholds (dynamic copy)
        self.max_bit_error_rate = self.base_max_qber
        self.min_entropy_score = self.base_min_entropy

        # Runtime tracking
        self.app_usage_counter = defaultdict(int)
        self.node_allocation_counter = defaultdict(int)

        self.failed_allocations = 0
        self.total_allocations = 0
        self.allocation_fail_history = []

        # Modes
        self.mode = "ADAPTIVE"  # BASELINE | ADAPTIVE | STRESS


    # =================================================
    # MODE SWITCH
    # =================================================
    def set_mode(self, mode: str):

        self.mode = mode

        # Reset thresholds when switching
        self.max_bit_error_rate = self.base_max_qber
        self.min_entropy_score = self.base_min_entropy


    # =================================================
    # PER-APPLICATION QUOTA
    # =================================================
    def allow_request(self, app_id: str, requested_keys: int) -> bool:

        if self.app_usage_counter[app_id] + requested_keys > self.per_app_limit:
            return False

        self.app_usage_counter[app_id] += requested_keys
        return True


    # =================================================
    # BUFFER PRESSURE ADAPTATION
    # =================================================
    def adapt_to_buffer_pressure(self, pressure_ratio: float):

        if self.mode != "ADAPTIVE":
            return

        if pressure_ratio > 0.6:
            self.max_bit_error_rate = self.base_max_qber + 0.02
            self.min_entropy_score = self.base_min_entropy - 0.02

        elif 0.3 <= pressure_ratio <= 0.6:
            self.max_bit_error_rate = self.base_max_qber
            self.min_entropy_score = self.base_min_entropy

        else:
            self.max_bit_error_rate = self.base_max_qber - 0.02
            self.min_entropy_score = self.base_min_entropy + 0.02


    # =================================================
    # QUANTUM FILTERING
    # =================================================
    def filter_valid_keys(self, keys: list):

        valid = []

        for key in keys:

            if key.state != KeyState.READY:
                continue

            if key.is_expired():
                continue

            if key.freshness_score < self.min_freshness:
                continue

            # STRESS mode artificially tightens QBER
            if self.mode == "STRESS":
                if key.bit_error_rate > (self.base_max_qber - 0.03):
                    continue
            else:
                if key.bit_error_rate > self.max_bit_error_rate:
                    continue

            if key.entropy_score < self.min_entropy_score:
                continue

            valid.append(key)

        return valid


    # =================================================
    # LINK-AWARE CONTROL
    # =================================================
    def allow_allocation_based_on_link(self, link_info: dict) -> bool:

        if not link_info:
            return False

        status = link_info.get("status")
        rate = link_info.get("rate", 0)
        latency = link_info.get("latency", 0)
        noise = link_info.get("noise_probability", 0)

        if status != "AVAILABLE":
            return False

        if rate < DEFAULT_LINK_RATE * 0.2:
            return False

        if latency > 200:
            return False

        if noise > 0.15:
            return False

        return True


    # =================================================
    # NODE TRACKING
    # =================================================
    def record_node_allocation(self, node_id: str):
        self.node_allocation_counter[node_id] += 1
        self.total_allocations += 1


    def record_failed_allocation(self):
        self.failed_allocations += 1
        self.allocation_fail_history.append(1)

        if len(self.allocation_fail_history) > 50:
            self.allocation_fail_history.pop(0)


    # =================================================
    # EXHAUSTION DETECTION
    # =================================================
    def is_exhaustion_detected(self) -> bool:

        if not self.allocation_fail_history:
            return False

        failure_rate = mean(self.allocation_fail_history)

        if failure_rate > 0.6:
            return True

        if self.failed_allocations > KEY_EXHAUSTION_TEST_RATE:
            return True

        return False


    # =================================================
    # METRICS
    # =================================================
    def get_policy_metrics(self):

        return {
            "mode": self.mode,
            "max_qber": self.max_bit_error_rate,
            "min_entropy": self.min_entropy_score,
            "total_allocations": self.total_allocations,
            "failed_allocations": self.failed_allocations,
            "tracked_apps": len(self.app_usage_counter),
            "tracked_nodes": len(self.node_allocation_counter)
        }