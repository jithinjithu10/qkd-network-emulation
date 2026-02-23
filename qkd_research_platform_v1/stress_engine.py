# stress_engine.py
"""
Research-Grade Stress & Attack Engine
Week 11–12 Advanced Evaluation Framework
Key Exhaustion | Distributed Attack | Link Degradation | Metrics Analysis
"""

import requests
import threading
import time
import statistics
from config import CENTRAL_KMS_URL


class StressEngine:

    def __init__(self):

        self.running = False
        self.metrics = {
            "total_requests": 0,
            "successful_allocations": 0,
            "failed_allocations": 0,
            "latencies": [],
            "attack_duration": 0
        }

    # =================================================
    # KEY EXHAUSTION ATTACK
    # =================================================
    def key_exhaustion_attack(self, rate=20, duration=10):

        self.running = True
        start_time = time.time()

        def attack():
            while self.running:

                t0 = time.time()

                try:
                    response = requests.post(
                        f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
                        json={
                            "session_id": "ATTACKER",
                            "role": "ENC"
                        },
                        timeout=3
                    )

                    latency = time.time() - t0

                    self.metrics["latencies"].append(latency)
                    self.metrics["total_requests"] += 1

                    if response.json().get("status") == "RESERVED":
                        self.metrics["successful_allocations"] += 1
                    else:
                        self.metrics["failed_allocations"] += 1

                except:
                    self.metrics["failed_allocations"] += 1

                time.sleep(1 / rate)

        thread = threading.Thread(target=attack)
        thread.start()

        time.sleep(duration)
        self.stop()

        self.metrics["attack_duration"] = time.time() - start_time

        return self.get_report()

    # =================================================
    # DISTRIBUTED EXHAUSTION ATTACK
    # =================================================
    def distributed_attack(self, attackers=5, rate=10, duration=10):

        threads = []

        for i in range(attackers):

            def attacker(id=i):
                while self.running:
                    requests.post(
                        f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
                        json={
                            "session_id": f"ATTACKER_{id}",
                            "role": "ENC"
                        }
                    )
                    time.sleep(1 / rate)

            threads.append(threading.Thread(target=attacker))

        self.running = True

        for t in threads:
            t.start()

        time.sleep(duration)
        self.stop()

        return self.get_report()

    # =================================================
    # LINK DEGRADATION SIMULATION
    # =================================================
    def link_degradation_attack(self, controller_url, node_a, node_b):

        try:
            requests.post(
                f"{controller_url}/controller/link/degrade",
                json={
                    "node_a": node_a,
                    "node_b": node_b
                }
            )
            return {"status": "DEGRADATION_TRIGGERED"}

        except Exception as e:
            return {"error": str(e)}

    # =================================================
    # COMBINED ATTACK SCENARIO
    # =================================================
    def combined_attack(self, controller_url, node_a, node_b):

        self.link_degradation_attack(controller_url, node_a, node_b)
        return self.key_exhaustion_attack(rate=30, duration=15)

    # =================================================
    # STOP ENGINE
    # =================================================
    def stop(self):
        self.running = False

    # =================================================
    # REPORT GENERATION
    # =================================================
    def get_report(self):

        avg_latency = (
            statistics.mean(self.metrics["latencies"])
            if self.metrics["latencies"]
            else 0
        )

        failure_rate = (
            self.metrics["failed_allocations"] /
            self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0
            else 0
        )

        return {
            "total_requests": self.metrics["total_requests"],
            "successful_allocations": self.metrics["successful_allocations"],
            "failed_allocations": self.metrics["failed_allocations"],
            "average_latency_sec": avg_latency,
            "failure_rate": failure_rate,
            "attack_duration_sec": self.metrics["attack_duration"]
        }