# experiments/experiment_runner.py

import csv
import time
import requests
from application.data_channel import SecureQKDChannel
from config import CENTRAL_KMS_URL


class ExperimentRunner:

    def __init__(self, output_file="experiment_results.csv"):
        self.output_file = output_file
        self.results = []

    # =================================================
    # Switch Policy Mode
    # =================================================
    def set_policy_mode(self, mode):

        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/policy/mode",
            json={"mode": mode}
        )

        if response.status_code != 200:
            raise Exception("Failed to switch policy mode")

        print(f"Switched to {mode} mode")

    # =================================================
    # Run Single Experiment Mode
    # =================================================
    def run_mode(self, mode, messages=500, message_size=1024):

        self.set_policy_mode(mode)

        channel = SecureQKDChannel()

        channel.establish_session()

        success_count = 0

        start_time = time.time()

        for _ in range(messages):

            try:
                payload = b"A" * message_size
                channel.send(payload)
                success_count += 1
            except Exception:
                break

        end_time = time.time()

        duration = end_time - start_time

        metrics = channel.get_metrics()

        result = {
            "mode": mode,
            "messages_attempted": messages,
            "messages_successful": success_count,
            "success_rate": success_count / messages,
            "avg_latency": metrics["average_latency"],
            "total_bytes": metrics["total_bytes"],
            "rekey_count": metrics["rekey_count"],
            "total_duration": duration,
            "throughput_bytes_per_sec":
                metrics["total_bytes"] / duration if duration > 0 else 0
        }

        self.results.append(result)

        print(f"Completed {mode} experiment")

    # =================================================
    # Run Full Sequential Experiment
    # =================================================
    def run_full_experiment(self):

        print("Starting Sequential Experiment...")

        self.run_mode("BASELINE")
        self.run_mode("ADAPTIVE")
        self.run_mode("STRESS")

        self.export_results()

    # =================================================
    # Export CSV
    # =================================================
    def export_results(self):

        keys = self.results[0].keys()

        with open(self.output_file, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.results)

        print(f"Results saved to {self.output_file}")


if __name__ == "__main__":

    runner = ExperimentRunner()
    runner.run_full_experiment()