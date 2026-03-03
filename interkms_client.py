"""
interkms_client.py

Inter-KMS Client Logic.

Used when NODE_ROLE = CLIENT.

Pulls keys from remote peer node
and injects them into local buffer.
"""

import threading
import time
import requests
from models import Key
from config import (
    NODE_ROLE,
    NODE_ID,
    PEER_NODES,
    DEFAULT_TTL_SECONDS,
    NODE_SHARED_SECRET
)


class InterKMSClient:

    def __init__(self, buffer, audit):

        self.buffer = buffer
        self.audit = audit
        self.running = False

    # =================================================
    # START PULLING THREAD
    # =================================================

    def start(self):

        if NODE_ROLE != "CLIENT":
            return

        self.running = True

        thread = threading.Thread(
            target=self._pull_loop,
            daemon=True
        )

        thread.start()

        print(f"[INFO] Inter-KMS client started on {NODE_ID}")

    # =================================================
    # CONTINUOUS PULL LOOP
    # =================================================

    def _pull_loop(self):

        while self.running:

            for peer_name, peer_url in PEER_NODES.items():

                try:
                    response = requests.post(
                        f"{peer_url}/interkms/v1/request-key",
                        headers={
                            "Authorization": f"Bearer {NODE_SHARED_SECRET}"
                        },
                        timeout=5
                    )

                    if response.status_code == 200:

                        data = response.json()

                        key = Key(
                            key_id=data["key_ID"],
                            key_value=data["key"],
                            key_size=data["size"],
                            ttl_seconds=DEFAULT_TTL_SECONDS,
                            origin_node=peer_name
                        )

                        self.buffer.add_key(key)

                        self.audit.key_received_from_node(
                            key.key_id,
                            peer_name
                        )

                except Exception as e:
                    self.audit.error(
                        f"Inter-KMS pull error: {str(e)}",
                        plane="INTER-KMS"
                    )

            time.sleep(2)  # Pull interval