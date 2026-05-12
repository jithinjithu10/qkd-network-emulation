# interkms_client.py
# ADVANCED DISTRIBUTED HYBRID QKD INTER-KMS CLIENT

import hashlib
import threading
import time
import hmac
import uuid

import requests

from models import Key

from config import (

    NODE_ROLE,

    NODE_ID,

    get_peer_url,

    DEFAULT_TTL_SECONDS,

    NODE_SHARED_SECRET,

    AUTH_TOKEN,

    INTERKMS_SYNC_INTERVAL,

    INTERKMS_MAX_RETRIES,

    ENABLE_SHA256_SYNC,

    ENABLE_METADATA_SYNC,

    QKD_PROTOCOL,

    SYSTEM_MODE
)

# =========================================================
# SHA-256
# =========================================================

def sha256_hash(
    key_material: str
):

    return hashlib.sha256(

        bytes.fromhex(key_material)

    ).hexdigest()

# =========================================================
# INTER-KMS CLIENT
# =========================================================

class InterKMSClient:

    """
    Distributed Inter-KMS Synchronization Client

    Responsibilities
    ----------------
    - distributed metadata synchronization
    - BB84 key consistency validation
    - synchronization ordering
    - replay prevention
    - inter-node trust verification
    - deterministic synchronization
    """

    def __init__(
        self,
        buffer,
        audit
    ):

        self.buffer = buffer

        self.audit = audit

        self.running = False

        self.thread = None

        # =================================================
        # POINTER
        # =================================================

        self.current_key_id = 0

        # =================================================
        # TRACKING
        # =================================================

        self.used_nonces = set()

        self.used_sync_ids = set()

        self.verified_sessions = {}

        # =================================================
        # METRICS
        # =================================================

        self.sync_success = 0

        self.sync_failures = 0

        self.replay_attempts = 0

        self.peer_failures = 0

        self.sync_latencies = []

    # =====================================================
    # START
    # =====================================================

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

        print(

            f"[INFO] Inter-KMS client started "
            f"on {NODE_ID}"
        )

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

        self.running = False

        if self.thread:

            self.thread.join(timeout=2)

    # =====================================================
    # VERIFY HASH
    # =====================================================

    def verify_hash(

        self,

        local_key,

        remote_hash
    ):

        if not ENABLE_SHA256_SYNC:
            return True

        local_hash = sha256_hash(
            local_key
        )

        return hmac.compare_digest(

            local_hash,

            remote_hash
        )

    # =====================================================
    # VERIFY NONCE
    # =====================================================

    def verify_nonce(
        self,
        nonce
    ):

        if not nonce:
            return False

        if nonce in self.used_nonces:

            self.replay_attempts += 1

            return False

        self.used_nonces.add(
            nonce
        )

        return True

    # =====================================================
    # VERIFY SYNC ID
    # =====================================================

    def verify_sync_id(
        self,
        sync_id
    ):

        if not sync_id:
            return False

        if sync_id in self.used_sync_ids:

            self.replay_attempts += 1

            return False

        self.used_sync_ids.add(
            sync_id
        )

        return True

    # =====================================================
    # PEER STATUS
    # =====================================================

    def fetch_peer_status(

        self,

        peer_url,

        headers
    ):

        response = requests.get(

            f"{peer_url}/etsi/v2/status",

            headers=headers,

            timeout=5
        )

        if response.status_code != 200:

            raise Exception(
                "Status API failed"
            )

        return response.json()

    # =====================================================
    # VERIFY METADATA
    # =====================================================

    def verify_metadata(
        self,
        data
    ):

        required = [

            "key_id",

            "session_id",

            "sync_index",

            "protocol"
        ]

        for field in required:

            if field not in data:

                self.audit.error(

                    (
                        f"Missing metadata "
                        f"{field}"
                    ),

                    "INTER-KMS"
                )

                return False

        if data["protocol"] != QKD_PROTOCOL:

            self.audit.error(

                (
                    f"Protocol mismatch "
                    f"{data['protocol']}"
                ),

                "INTER-KMS"
            )

            return False

        return True

    # =====================================================
    # RECORD LATENCY
    # =====================================================

    def record_latency(
        self,
        value
    ):

        self.sync_latencies.append(
            value
        )

    # =====================================================
    # AVERAGE LATENCY
    # =====================================================

    def average_latency(
        self
    ):

        if not self.sync_latencies:
            return 0

        return (

            sum(self.sync_latencies)

            /

            len(self.sync_latencies)
        )

    # =====================================================
    # MAIN LOOP
    # =====================================================

    def _pull_loop(self):

        while self.running:

            start_time = time.perf_counter()

            peer_url = (
                get_peer_url()
                .rstrip("/")
            )

            # =================================================
            # AUTH
            # =================================================

            auth_headers = {

                "Authorization":
                    f"Bearer {AUTH_TOKEN}"
            }

            interkms_headers = {

                "Authorization":
                    f"Bearer {NODE_SHARED_SECRET}",

                "X-Node-ID":
                    NODE_ID
            }

            # =================================================
            # STATUS
            # =================================================

            try:

                status = self.fetch_peer_status(

                    peer_url,

                    auth_headers
                )

                max_key_id = int(

                    status.get(
                        "sync_index",
                        -1
                    )

                ) - 1

            except Exception as e:

                self.peer_failures += 1

                self.audit.error(

                    (
                        f"Status fetch failed: "
                        f"{str(e)}"
                    ),

                    plane="INTER-KMS"
                )

                time.sleep(
                    INTERKMS_SYNC_INTERVAL
                )

                continue

            expected_key_id = (
                self.current_key_id
            )

            # =================================================
            # WAIT
            # =================================================

            if expected_key_id > max_key_id:

                self.audit.log(

                    "SYNC_WAIT",

                    (
                        f"waiting_for="
                        f"{expected_key_id} "
                        f"max_available="
                        f"{max_key_id}"
                    ),

                    plane="SYNC"
                )

                time.sleep(1)

                continue

            success = False

            # =================================================
            # RETRIES
            # =================================================

            for attempt in range(
                INTERKMS_MAX_RETRIES
            ):

                try:

                    sync_id = str(
                        uuid.uuid4()
                    )[:8]

                    if not self.verify_sync_id(
                        sync_id
                    ):

                        continue

                    self.audit.api(
                        "/interkms/v1/request-key"
                    )

                    response = requests.post(

                        f"{peer_url}/interkms/v1/request-key",

                        headers=interkms_headers,

                        json={

                            "key_id":
                                str(expected_key_id),

                            "sync_id":
                                sync_id,

                            "timestamp":
                                time.time()
                        },

                        timeout=10
                    )

                    if response.status_code != 200:
                        continue

                    data = response.json()

                    # -----------------------------------------
                    # VERIFY METADATA
                    # -----------------------------------------

                    if not self.verify_metadata(
                        data
                    ):

                        continue

                    # -----------------------------------------
                    # KEY ID
                    # -----------------------------------------

                    received_key_id = int(

                        data.get("key_id")
                    )

                    if (

                        received_key_id
                        != expected_key_id

                    ):

                        self.audit.sync_mismatch(

                            expected=expected_key_id,

                            received=received_key_id
                        )

                        continue

                    # -----------------------------------------
                    # METADATA
                    # -----------------------------------------

                    key_hash = data.get(
                        "key_hash"
                    )

                    session_id = data.get(
                        "session_id"
                    )

                    protocol = data.get(
                        "protocol"
                    )

                    nonce = data.get(
                        "nonce"
                    )

                    # -----------------------------------------
                    # NONCE
                    # -----------------------------------------

                    if nonce:

                        if not self.verify_nonce(
                            nonce
                        ):

                            continue

                    # -----------------------------------------
                    # PROTOCOL
                    # -----------------------------------------

                    if protocol != QKD_PROTOCOL:

                        self.audit.error(

                            (
                                f"Protocol mismatch "
                                f"{protocol}"
                            ),

                            "INTER-KMS"
                        )

                        continue

                    # -----------------------------------------
                    # LOCAL KEY
                    # -----------------------------------------

                    local_key = (

                        self.buffer.get_key_by_id(
                            str(expected_key_id)
                        )
                    )

                    # -----------------------------------------
                    # ALREADY EXISTS
                    # -----------------------------------------

                    if local_key:

                        verified = self.verify_hash(

                            local_key.key_value,

                            key_hash
                        )

                        if verified:

                            self.audit.sync_success(
                                expected_key_id
                            )

                            self.current_key_id += 1

                            self.sync_success += 1

                            success = True

                            break

                    # =================================================
                    # METADATA MODE
                    # =================================================

                    if ENABLE_METADATA_SYNC:

                        self.audit.log(

                            "METADATA_SYNC",

                            (
                                f"key_id="
                                f"{expected_key_id} "
                                f"session="
                                f"{session_id}"
                            ),

                            plane="SYNC"
                        )

                        self.audit.error(

                            (
                                f"Local BB84 key "
                                f"missing "
                                f"{expected_key_id}"
                            ),

                            "SYNC"
                        )

                        break

                    # =================================================
                    # RAW KEY MODE
                    # =================================================

                    raw_key = data.get("key")

                    if not raw_key:

                        self.audit.error(

                            "Raw key unavailable",

                            "INTER-KMS"
                        )

                        continue

                    # -----------------------------------------
                    # HASH VERIFY
                    # -----------------------------------------

                    verified = self.verify_hash(

                        raw_key,

                        key_hash
                    )

                    if not verified:

                        self.sync_failures += 1

                        self.audit.sync_fail(
                            expected_key_id
                        )

                        continue

                    # -----------------------------------------
                    # STORE KEY
                    # -----------------------------------------

                    key = Key(

                        key_id=
                            str(expected_key_id),

                        key_value=
                            raw_key,

                        key_size=
                            256,

                        ttl_seconds=
                            DEFAULT_TTL_SECONDS,

                        origin_node=
                            "PEER_BB84"
                    )

                    self.buffer.add_sync_key(
                        key
                    )

                    # -----------------------------------------
                    # VERIFY ACK
                    # -----------------------------------------

                    verify_response = requests.post(

                        f"{peer_url}/interkms/v1/verify",

                        headers=interkms_headers,

                        json={

                            "key_id":
                                str(expected_key_id),

                            "node":
                                NODE_ID,

                            "key_hash":
                                key_hash,

                            "sync_id":
                                sync_id,

                            "timestamp":
                                time.time()
                        },

                        timeout=5
                    )

                    if (
                        verify_response.status_code
                        == 200
                    ):

                        self.audit.sync_success(
                            expected_key_id
                        )

                    self.current_key_id += 1

                    self.sync_success += 1

                    success = True

                    break

                except Exception as e:

                    self.sync_failures += 1

                    self.audit.error(

                        (
                            f"Attempt "
                            f"{attempt + 1} "
                            f"failed: {str(e)}"
                        ),

                        plane="INTER-KMS"
                    )

                # =================================================
                # EXPONENTIAL BACKOFF
                # =================================================

                time.sleep(
                    0.5 * (attempt + 1)
                )

            # =================================================
            # FAILURE
            # =================================================

            if not success:

                self.sync_failures += 1

                self.audit.error(

                    (
                        f"Failed to synchronize "
                        f"key {expected_key_id}"
                    ),

                    plane="INTER-KMS"
                )

            latency = (

                time.perf_counter()
                -
                start_time
            )

            self.record_latency(
                latency
            )

            time.sleep(
                INTERKMS_SYNC_INTERVAL
            )

    # =====================================================
    # METRICS
    # =====================================================

    def metrics(self):

        return {

            "current_key_id":
                self.current_key_id,

            "sync_success":
                self.sync_success,

            "sync_failures":
                self.sync_failures,

            "peer_failures":
                self.peer_failures,

            "replay_attempts":
                self.replay_attempts,

            "average_latency":
                self.average_latency()
        }

    # =====================================================
    # DEBUG
    # =====================================================

    def debug_dump(self):

        return {

            "metrics":
                self.metrics(),

            "verified_sessions":
                self.verified_sessions,

            "used_sync_ids":
                list(self.used_sync_ids)
        }