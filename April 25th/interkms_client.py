# interkms_client.py
# FINAL PRODUCTION VERSION (STATE-AWARE SYNC - FIXED)

import threading
import time
import requests
import hashlib

from models import Key

from config import (
    NODE_ROLE,
    NODE_ID,
    get_peer_url,
    DEFAULT_TTL_SECONDS,
    NODE_SHARED_SECRET,
    INTERKMS_SYNC_INTERVAL,
    INTERKMS_MAX_RETRIES,
    AUTH_TOKEN
)


# =================================================
# XOR HELPER
# =================================================
def xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


class InterKMSClient:

    def __init__(self, buffer, audit):

        self.buffer = buffer
        self.audit = audit

        self.running = False
        self.thread = None

        # deterministic sync pointer
        self.current_key_id = 0

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
    # MAIN SYNC LOOP
    # =================================================
    def _pull_loop(self):

        while self.running:

            peer_url = get_peer_url()

            # --------------------------------------------
            # STEP 1: GET SERVER STATUS (FIXED)
            # --------------------------------------------
            try:
                status_resp = requests.get(
                    f"{peer_url}/etsi/v2/status",
                    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                    timeout=5
                )

                if status_resp.status_code != 200:
                    raise Exception("Status API failed")

                status = status_resp.json()

                # FIX: use sync_index instead of non-existent max_key_id
                max_key_id = int(status.get("sync_index", -1)) - 1

            except Exception as e:
                self.audit.error(
                    f"Status fetch failed: {str(e)}",
                    plane="INTER-KMS"
                )
                time.sleep(INTERKMS_SYNC_INTERVAL)
                continue

            expected_key_id = self.current_key_id

            # --------------------------------------------
            # STEP 2: PREVENT OVERSHOOT
            # --------------------------------------------
            if expected_key_id > max_key_id:
                self.audit.log(
                    "WAITING",
                    f"Waiting for key {expected_key_id}, max available {max_key_id}",
                    plane="SYNC"
                )
                time.sleep(1)
                continue

            success = False

            # --------------------------------------------
            # STEP 3: FETCH KEY
            # --------------------------------------------
            for attempt in range(INTERKMS_MAX_RETRIES):

                try:

                    self.audit.api("/interkms/v1/request-key")

                    response = requests.post(
                        f"{peer_url}/interkms/v1/request-key",
                        headers={
                            "Authorization": f"Bearer {NODE_SHARED_SECRET}",
                            "X-Node-ID": NODE_ID
                        },
                        json={"key_id": str(expected_key_id)},
                        timeout=10
                    )

                    if response.status_code != 200:
                        continue

                    data = response.json()

                    received_key_id = int(data.get("key_id"))

                    # STRICT MATCH CHECK
                    if received_key_id != expected_key_id:
                        self.audit.sync_mismatch(
                            expected=expected_key_id,
                            received=received_key_id
                        )
                        continue

                    enc_key = data.get("enc_key")
                    received_hash = data.get("hash")

                    if not enc_key or not received_hash:
                        continue

                    # --------------------------------
                    # PREVIOUS KEY
                    # --------------------------------
                    if expected_key_id > 0:
                        prev_key = self.buffer.get_key_by_id(str(expected_key_id - 1))
                    else:
                        prev_key = None

                    # --------------------------------
                    # XOR RECOVERY
                    # --------------------------------
                    if prev_key:
                        try:
                            new_key = xor(
                                bytes.fromhex(enc_key),
                                bytes.fromhex(prev_key.key_value)
                            ).hex()
                        except Exception as e:
                            self.audit.sync_fail(expected_key_id)
                            continue
                    else:
                        new_key = enc_key

                    # --------------------------------
                    # HASH VERIFICATION (FIXED)
                    # --------------------------------
                    local_hash = hashlib.sha256(
                        bytes.fromhex(new_key)
                    ).hexdigest()

                    if local_hash != received_hash:
                        self.audit.sync_fail(expected_key_id)
                        continue

                    # --------------------------------
                    # STORE KEY
                    # --------------------------------
                    key = Key(
                        key_id=str(expected_key_id),
                        key_value=new_key,
                        key_size=256,
                        ttl_seconds=DEFAULT_TTL_SECONDS,
                        origin_node="PEER"
                    )

                    self.buffer.add_sync_key(key)

                    self.audit.log(
                        "KEY_SYNCED",
                        f"{expected_key_id} synced from peer",
                        plane="INTER-KMS"
                    )

                    # MOVE FORWARD ONLY AFTER SUCCESS
                    self.current_key_id += 1

                    success = True
                    break

                except Exception as e:
                    self.audit.error(
                        f"Attempt {attempt+1} failed: {str(e)}",
                        plane="INTER-KMS"
                    )

                time.sleep(0.5)

            # --------------------------------------------
            # FAILURE CASE
            # --------------------------------------------
            if not success:
                self.audit.error(
                    f"Failed to sync key {expected_key_id}",
                    plane="INTER-KMS"
                )

            time.sleep(INTERKMS_SYNC_INTERVAL)