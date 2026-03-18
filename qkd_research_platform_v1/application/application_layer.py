# application_layer.py

import requests
import uuid
import time
from datetime import datetime

from qkd_research_platform_v1.config import CENTRAL_KMS_URL


class QKDApplicationClient:

    def __init__(self):

        self.session_id = None
        self.local_key_store = {}
        self.current_key_id = None

        # Metrics tracking
        self.total_requests = 0
        self.failed_requests = 0
        self.latencies = []

        print("QKDApplicationClient initialized")
        print("KMS URL:", CENTRAL_KMS_URL)


    # =============================================
    # Create Session
    # =============================================
    def create_session(self):

        self.session_id = str(uuid.uuid4())

        print("\n=== SESSION CREATED ===")
        print("Session ID:", self.session_id)

        return self.session_id


    # =============================================
    # Request Key from KMS
    # =============================================
    def request_key(self, role="ENC"):

        if not self.session_id:
            raise Exception("Session not created")

        print("\n=== REQUESTING KEY ===")
        print("Session:", self.session_id)
        print("Role:", role)

        self.total_requests += 1

        try:
            start_time = time.time()

            response = requests.post(
                f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
                json={
                    "session_id": self.session_id,
                    "role": role
                },
                timeout=10
            )

            end_time = time.time()
            round_trip = end_time - start_time

            print("HTTP Status Code:", response.status_code)
            print("Round-trip time:", round_trip)

        except Exception as e:
            print("ERROR contacting KMS:", e)
            self.failed_requests += 1
            return None

        data = response.json()

        print("Response Data:", data)

        if data.get("status") != "RESERVED":

            self.failed_requests += 1

            print("Key request failed:",
                  data.get("status"))

            return None

        key_id = data["key_id"]
        latency = data.get("latency")
        pressure = data.get("pressure")
        policy_mode = data.get("policy_mode")

        if latency:
            self.latencies.append(latency)

        print("Key Reserved:", key_id)
        print("Allocation Latency:", latency)
        print("Buffer Pressure:", pressure)
        print("Policy Mode:", policy_mode)

        self.local_key_store[key_id] = {
            "received_at": datetime.utcnow(),
            "used": False,
            "latency": latency,
            "pressure": pressure,
            "policy_mode": policy_mode
        }

        self.current_key_id = key_id

        return key_id


    # =============================================
    # Consume Key (Session-Based)
    # =============================================
    def consume_key(self):

        if not self.session_id:
            print("No active session")
            return

        print("\n=== CONSUMING KEY ===")
        print("Session:", self.session_id)

        try:
            response = requests.post(
                f"{CENTRAL_KMS_URL}/api/v1/keys/consume",
                json={"session_id": self.session_id},
                timeout=10
            )

        except Exception as e:
            print("ERROR consuming key:", e)
            return None

        data = response.json()

        print("Consume Response:", data)

        if data.get("status") == "CONSUMED":

            key_id = data.get("key_id")

            if key_id in self.local_key_store:
                self.local_key_store[key_id]["used"] = True

            self.current_key_id = None

        return data


    # =============================================
    # Application Metrics
    # =============================================
    def get_metrics(self):

        avg_latency = (
            sum(self.latencies) / len(self.latencies)
            if self.latencies else 0
        )

        metrics = {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate":
                (self.total_requests - self.failed_requests)
                / self.total_requests
                if self.total_requests else 0,
            "average_latency": avg_latency
        }

        print("\n=== APPLICATION METRICS ===")
        print(metrics)

        return metrics