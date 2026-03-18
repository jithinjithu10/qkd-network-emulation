# metrics_engine.py

import time
import requests
from config import CENTRAL_KMS_URL


class MetricsEngine:

    def measure_allocation_latency(self):

        start = time.time()

        requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
            json={
                "session_id": "METRIC",
                "role": "ENC"
            }
        )

        end = time.time()

        return end - start

    def fetch_kms_metrics(self):

        response = requests.get(
            f"{CENTRAL_KMS_URL}/api/v1/metrics"
        )

        return response.json()
