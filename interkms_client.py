# interkms_client.py (FINAL - SYNC CORRECT + SECURE)

import threading
import time
import requests
import hashlib

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


# -------------------------------
# XOR
# -------------------------------
def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


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
                expected_key_id = str(expected_index)

                success = False

                for attempt in range(INTERKMS_MAX_RETRIES):

                    try:

                        self.audit.api("/interkms/v1/request-key")

                        response = requests.post(
                            f"{peer_url}/interkms/v1/request-key",
                            headers={
                                "Authorization": f"Bearer {NODE_SHARED_SECRET}",
                                "X-Node-ID": NODE_ID
                            },
                            json={"key_id": expected_key_id},
                            timeout=5
                        )

                        if response.status_code != 200:
                            continue

                        data = response.json()

                        received_key_id = data["key_id"]

                        # -------------------------------
                        # STRICT SYNC CHECK
                        # -------------------------------
                        if str(received_key_id) != expected_key_id:

                            self.audit.sync_mismatch(
                                expected=expected_key_id,
                                received=received_key_id
                            )
                            continue

                        enc_key = data["enc_key"]
                        received_hash = data["hash"]

                        # -------------------------------
                        # GET PREVIOUS KEY
                        # -------------------------------
                        prev_id = str(int(received_key_id) - 1)
                        prev_key = self.buffer.get_key_by_id(prev_id)

                        if prev_key:
                            new_key = xor(
                                bytes.fromhex(enc_key),
                                bytes.fromhex(prev_key.key_value)
                            ).hex()
                        else:
                            # genesis case
                            new_key = enc_key

                        # -------------------------------
                        # HASH VERIFICATION
                        # -------------------------------
                        local_hash = hashlib.sha256(new_key.encode()).hexdigest()

                        if local_hash != received_hash:
                            self.audit.sync_fail(received_key_id)
                            continue

                        self.audit.sync_success(received_key_id)

                        # -------------------------------
                        # CREATE KEY OBJECT
                        # -------------------------------
                        key = Key(
                            key_id=received_key_id,
                            key_value=new_key,
                            key_size=256,
                            ttl_seconds=DEFAULT_TTL_SECONDS,
                            origin_node=peer_name
                        )

                        # -------------------------------
                        # ADD TO BUFFER
                        # -------------------------------
                        self.buffer.add_sync_key(key)

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