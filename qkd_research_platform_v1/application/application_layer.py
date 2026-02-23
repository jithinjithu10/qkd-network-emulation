# application_layer.py

import requests
import uuid
from datetime import datetime
from config import CENTRAL_KMS_URL


class QKDApplicationClient:

    def __init__(self):

        self.session_id = None
        self.local_key_store = {}
        self.current_key_id = None

        # Metrics tracking
        self.total_requests = 0
        self.failed_requests = 0
        self.latencies = []


    # =============================================
    # Create Session
    # =============================================
    def create_session(self):

        self.session_id = str(uuid.uuid4())
        return self.session_id


    # =============================================
    # Request Key from KMS
    # =============================================
    def request_key(self, role="ENC"):

        if not self.session_id:
            raise Exception("Session not created")

        self.total_requests += 1

        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
            json={
                "session_id": self.session_id,
                "role": role
            }
        )

        data = response.json()

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
            return

        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/consume",
            json={"session_id": self.session_id}
        )

        data = response.json()

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

        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate":
                (self.total_requests - self.failed_requests)
                / self.total_requests
                if self.total_requests else 0,
            "average_latency": avg_latency
        }