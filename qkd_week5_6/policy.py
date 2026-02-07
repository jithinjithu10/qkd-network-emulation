from datetime import datetime, timezone


class PolicyEngine:
    def __init__(self):
        self.per_app_limit = 5
        self.min_freshness = 0.3
        self.refill_threshold = 3

    def allow_request(self, app_id, requested_keys):
        return requested_keys <= self.per_app_limit

    def filter_fresh_keys(self, keys):
        return [k for k in keys if k.freshness_score() >= self.min_freshness]

    def needs_refill(self, qbuffer_size):
        return qbuffer_size < self.refill_threshold
