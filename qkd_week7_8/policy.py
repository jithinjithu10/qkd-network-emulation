"""
policy.py
----------
Policy Engine for QKD KMS.

Implements:
- Per-application key usage limits
- Freshness filtering
- TTL enforcement
- Adaptive refill logic
- Role-aware decisions
"""

from datetime import datetime, timezone
from collections import defaultdict
from models import KeyRole, KeyState


class PolicyEngine:

    def __init__(self):
        # Maximum keys per application per session
        self.per_app_limit = 5

        # Minimum freshness score required
        self.min_freshness = 30   # since freshness starts at 100

        # Refill threshold for Q Buffer
        self.refill_threshold = 3

        # Track application usage
        self.app_usage_counter = defaultdict(int)

    # -------------------------------------------------
    # Per-Application Quota Enforcement
    # -------------------------------------------------
    def allow_request(self, app_id: str, requested_keys: int) -> bool:
        """
        Check whether application exceeds its allocation quota.
        """
        current_usage = self.app_usage_counter[app_id]

        if current_usage + requested_keys > self.per_app_limit:
            return False

        self.app_usage_counter[app_id] += requested_keys
        return True

    # -------------------------------------------------
    # Freshness + Expiry Filtering
    # -------------------------------------------------
    def filter_valid_keys(self, keys: list):
        """
        Return only keys that:
        - Are READY
        - Are not expired
        - Meet freshness requirement
        """
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

    # -------------------------------------------------
    # Adaptive Refill Logic
    # -------------------------------------------------
    def needs_refill(self, qbuffer_size: int) -> bool:
        """
        Determine if Q Buffer needs refill.
        """
        return qbuffer_size < self.refill_threshold

    # -------------------------------------------------
    # Role-Aware Refill Decision
    # -------------------------------------------------
    def needs_role_refill(self, enc_size: int, dec_size: int):
        """
        Determine refill requirement separately
        for ENC and DEC pools.
        """
        return {
            KeyRole.ENC: enc_size < self.refill_threshold,
            KeyRole.DEC: dec_size < self.refill_threshold
        }

    # -------------------------------------------------
    # Session Reset (Week 8)
    # -------------------------------------------------
    def reset_app_usage(self, app_id: str):
        """
        Reset usage counter after session ends.
        """
        self.app_usage_counter[app_id] = 0
