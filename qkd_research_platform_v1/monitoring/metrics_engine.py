# metrics_engine.py
"""
Research-Grade Metrics Engine
Week 12 Evaluation Framework
Latency | Throughput | Failure Rate | Comparative Analysis
"""

import time
import statistics
import requests
from config import CENTRAL_KMS_URL


class MetricsEngine:

    def __init__(self):

        self.latencies = []
        self.successful = 0
        self.failed = 0

    # =================================================
    # MULTI-SAMPLE LATENCY TEST
    # =================================================
    def measure_allocation_latency(self, samples=20):

        self.latencies.clear()
        self.successful = 0
        self.failed = 0

        for _ in range(samples):

            start = time.time()

            try:
                response = requests.post(
                    f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
                    json={
                        "session_id": "METRIC",
                        "role": "ENC"
                    },
                    timeout=5
                )

                latency = time.time() - start
                self.latencies.append(latency)

                if response.json().get("status") == "RESERVED":
                    self.successful += 1
                else:
                    self.failed += 1

            except:
                self.failed += 1

        return self._generate_latency_report()

    # =================================================
    # LATENCY REPORT
    # =================================================
    def _generate_latency_report(self):

        if not self.latencies:
            return {"error": "No latency samples collected"}

        avg = statistics.mean(self.latencies)
        median = statistics.median(self.latencies)
        stdev = statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0

        throughput = (
            self.successful / sum(self.latencies)
            if sum(self.latencies) > 0 else 0
        )

        failure_rate = (
            self.failed / (self.successful + self.failed)
            if (self.successful + self.failed) > 0 else 0
        )

        return {
            "samples": len(self.latencies),
            "average_latency_sec": avg,
            "median_latency_sec": median,
            "std_dev_latency_sec": stdev,
            "max_latency_sec": max(self.latencies),
            "min_latency_sec": min(self.latencies),
            "throughput_requests_per_sec": throughput,
            "success_count": self.successful,
            "failure_count": self.failed,
            "failure_rate": failure_rate
        }

    # =================================================
    # TIME-SERIES MONITORING
    # =================================================
    def monitor_kms(self, duration=10, interval=1):

        timeline = []

        start_time = time.time()

        while time.time() - start_time < duration:

            try:
                response = requests.get(
                    f"{CENTRAL_KMS_URL}/api/v1/metrics",
                    timeout=5
                )
                data = response.json()

                timeline.append({
                    "timestamp": time.time(),
                    "ready_keys": data.get("ready_keys", 0),
                    "reserved_keys": data.get("reserved_keys", 0),
                    "consumed_keys": data.get("consumed_keys", 0),
                    "expired_keys": data.get("expired_keys", 0)
                })

            except:
                pass

            time.sleep(interval)

        return timeline

    # =================================================
    # FETCH FULL METRICS SNAPSHOT
    # =================================================
    def fetch_kms_metrics(self):

        response = requests.get(
            f"{CENTRAL_KMS_URL}/api/v1/metrics",
            timeout=5
        )

        return response.json()

    # =================================================
    # COMPARATIVE TEST (Baseline vs Adaptive)
    # =================================================
    def comparative_test(self, samples=20):

        print("Running baseline test...")
        baseline = self.measure_allocation_latency(samples)

        print("Switch policy to ADAPTIVE mode manually before next test.")

        input("Press Enter to continue...")

        adaptive = self.measure_allocation_latency(samples)

        return {
            "baseline": baseline,
            "adaptive": adaptive
        }