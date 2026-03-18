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

        response = requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
            json={
                "session_id": self.session_id,
                "role": role
            }
        )

        data = response.json()

        if data.get("status") != "RESERVED":
            print("⚠ Key unavailable")
            return None

        key_id = data["key_id"]

        self.local_key_store[key_id] = {
            "received_at": datetime.utcnow(),
            "used": False
        }

        self.current_key_id = key_id
        return key_id

    # =============================================
    # Mark Key Used
    # =============================================
    def consume_key(self):

        if not self.current_key_id:
            return

        requests.post(
            f"{CENTRAL_KMS_URL}/api/v1/keys/consume",
            json={"key_id": self.current_key_id}
        )

        self.local_key_store[self.current_key_id]["used"] = True
