# stress_engine.py

import requests
import threading
import time
from config import CENTRAL_KMS_URL


class StressEngine:

    def __init__(self):
        self.running = False

    def key_exhaustion_attack(self, rate=20):

        self.running = True

        def attack():
            while self.running:
                requests.post(
                    f"{CENTRAL_KMS_URL}/api/v1/keys/allocate",
                    json={
                        "session_id": "ATTACKER",
                        "role": "ENC"
                    }
                )
                time.sleep(1 / rate)

        thread = threading.Thread(target=attack)
        thread.start()

    def stop(self):
        self.running = False
