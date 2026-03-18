"""
interkms_client.py

Inter-KMS Client Logic.

Used when NODE_ROLE = CLIENT.

Responsibilities:
- Pull keys from peer QKD nodes
- Inject keys into local buffer
- Enable distributed key availability

Runs in background thread.
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
    NODE_SHARED_SECRET,
    INTERKMS_SYNC_INTERVAL
)


class InterKMSClient:

    def __init__(self, buffer, audit):

        self.buffer = buffer
        self.audit = audit

        self.running = False
        self.thread = None

    # =================================================
    # START CLIENT
    # =================================================

    def start(self):

        if NODE_ROLE != "CLIENT":
            return

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._pull_loop,
            daemon=True
        )

        self.thread.start()

        print(f"[INFO] Inter-KMS client started on {NODE_ID}")

    # =================================================
    # STOP CLIENT
    # =================================================

    def stop(self):

        self.running = False

        if self.thread:
            self.thread.join(timeout=2)

    # =================================================
    # MAIN PULL LOOP
    # =================================================

    def _pull_loop(self):

        while self.running:

            for peer_name, peer_url in PEER_NODES.items():

                try:

                    self.audit.api_call(
                        "/interkms/v1/request-key",
                        plane="INTER-KMS"
                    )

                    response = requests.post(
                        f"{peer_url}/interkms/v1/request-key",
                        headers={
                            "Authorization": f"Bearer {NODE_SHARED_SECRET}"
                        },
                        timeout=5
                    )

                    if response.status_code != 200:
                        continue

                    data = response.json()

                    key = Key(
                        key_id=data["key_ID"],
                        key_value=data["key"],
                        key_size=data["size"],
                        ttl_seconds=DEFAULT_TTL_SECONDS,
                        origin_node=data.get("origin", peer_name)
                    )

                    # Inject into local buffer
                    self.buffer.add_remote_key(
                        key,
                        remote_node=peer_name
                    )

                except Exception as e:

                    self.audit.error(
                        f"Inter-KMS pull error from {peer_name}: {str(e)}",
                        plane="INTER-KMS"
                    )

            # Wait before next sync cycle
            time.sleep(INTERKMS_SYNC_INTERVAL)