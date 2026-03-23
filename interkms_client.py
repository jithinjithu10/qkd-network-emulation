"""
interkms_client.py (UPDATED - RESEARCH LEVEL)

Fixes:
- Removed "sync-" prefix
- Strong sync validation
- Correct API field names
- Improved retry + logging
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
    INTERKMS_SYNC_INTERVAL,
    INTERKMS_MAX_RETRIES
)


class InterKMSClient:

    def __init__(self, buffer, audit):

        self.buffer = buffer
        self.audit = audit

        self.running = False
        self.thread = None

    # =================================================
    # START
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
    # STOP
    # =================================================

    def stop(self):

        self.running = False

        if self.thread:
            self.thread.join(timeout=2)

    # =================================================
    # LOOP
    # =================================================

    def _pull_loop(self):

        while self.running:

            for peer_name, peer_url in PEER_NODES.items():

                stats = self.buffer.stats()
                expected_index = stats.get("sync_index", 0)

                # FIX: numeric key_id only
                expected_key_id = str(expected_index)

                success = False

                for attempt in range(INTERKMS_MAX_RETRIES):

                    try:

                        self.audit.api_call(
                            "/interkms/v1/request-key",
                            plane="INTER-KMS"
                        )

                        response = requests.post(
                            f"{peer_url}/interkms/v1/request-key",
                            headers={
                                "Authorization": f"Bearer {NODE_SHARED_SECRET}",
                                "X-Node-ID": NODE_ID
                            },
                            json={
                                "key_id": expected_key_id
                            },
                            timeout=5
                        )

                        if response.status_code != 200:
                            continue

                        data = response.json()

                        # FIX: correct field name
                        received_key_id = data["key_id"]

                        # STRONG SYNC VALIDATION
                        if str(received_key_id) != expected_key_id:

                            self.audit.sync_mismatch(
                                expected=expected_key_id,
                                received=received_key_id
                            )
                            continue

                        key = Key(
                            key_id=received_key_id,
                            key_value=data["key"],
                            key_size=data.get("size", 256),
                            ttl_seconds=DEFAULT_TTL_SECONDS,
                            origin_node=data.get("origin", peer_name)
                        )

                        # insert into buffer
                        self.buffer.add_remote_key(
                            key,
                            remote_node=peer_name
                        )

                        self.audit.log(
                            "KEY_SYNCED",
                            f"{key.key_id} synced from {peer_name}",
                            plane="INTER-KMS"
                        )

                        success = True
                        break

                    except Exception as e:

                        self.audit.error(
                            f"Attempt {attempt+1} failed from {peer_name}: {str(e)}",
                            plane="INTER-KMS"
                        )

                if not success:
                    self.audit.error(
                        f"Failed to sync key {expected_key_id} from {peer_name}",
                        plane="INTER-KMS"
                    )

            time.sleep(INTERKMS_SYNC_INTERVAL)