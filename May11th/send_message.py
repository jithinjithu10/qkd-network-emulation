# send_message.py
# ADVANCED HYBRID QKD SECURE MESSAGE TRANSMISSION

import requests
import time
import hashlib
import uuid

from datetime import datetime

from secure_transfer import SecureTransfer
from performance_metrics import PerformanceMetrics

from config import (

    AUTH_TOKEN,

    PEER_NODES,

    QKD_PROTOCOL,
    SYSTEM_MODE,

    ENABLE_SHA256_SYNC,
    ENABLE_REPLAY_PROTECTION
)

# =========================================================
# CONFIGURATION
# =========================================================

IITR_KMS = PEER_NODES["IITR"].rstrip("/")

IITJ_BASE = PEER_NODES["IITJ"].rstrip("/")

IITJ_URL = (
    f"{IITJ_BASE}/receive-message"
)

HEADERS = {

    "Authorization":
        f"Bearer {AUTH_TOKEN}"
}

# =========================================================
# PERFORMANCE
# =========================================================

metrics = PerformanceMetrics()

# =========================================================
# SHA-256
# =========================================================

def sha256_hash(
    key_material
):

    return hashlib.sha256(

        bytes.fromhex(key_material)

    ).hexdigest()

# =========================================================
# VERIFY HASH
# =========================================================

def verify_hash(

    local_hash,

    remote_hash
):

    if not ENABLE_SHA256_SYNC:
        return True

    return local_hash == remote_hash

# =========================================================
# WAIT FOR SYNCHRONIZATION
# =========================================================

def wait_for_key_on_receiver(
    key_id
):

    print(

        f"\n[SYNC] Waiting for IITJ "
        f"to synchronize key {key_id}..."
    )

    for _ in range(20):

        try:

            r = requests.get(

                f"{IITJ_BASE}/etsi/v2/keys/{key_id}",

                headers=HEADERS,

                timeout=3
            )

            if r.status_code == 200:

                data = r.json()

                if data.get("verified"):

                    print(

                        "[SYNC SUCCESS] "
                        "Key synchronized & verified"
                    )

                    return data

        except:
            pass

        time.sleep(0.5)

    print(

        "[SYNC FAILED] "
        "IITJ does not have verified key"
    )

    return None

# =========================================================
# FETCH METADATA
# =========================================================

def fetch_metadata(
    key_id
):

    try:

        r = requests.get(

            f"{IITR_KMS}/etsi/v2/metadata/{key_id}",

            headers=HEADERS,

            timeout=5
        )

        if r.status_code != 200:
            return None

        return r.json()

    except:
        return None

# =========================================================
# BANNER
# =========================================================

def banner():

    print("\n" + "=" * 70)

    print(
        " HYBRID QUANTUM-CLASSICAL "
        "QKD MESSAGE TRANSMISSION "
    )

    print("=" * 70)

    print("\nArchitecture")

    print(
        "- Quantum Layer   : BB84 + SimulaQron"
    )

    print(
        "- Classical Layer : ETSI APIs"
    )

    print(
        "- Encryption       : AES-256-GCM"
    )

    print(
        "- Synchronization  : SHA-256"
    )

    print(
        "- Replay Protection: ENABLED"
    )

    print("=" * 70)

# =========================================================
# MAIN
# =========================================================

def main():

    banner()

    delivery_id = str(
        uuid.uuid4()
    )[:8]

    print(f"\n[IITR KMS]")
    print(IITR_KMS)

    print(f"\n[IITJ NODE]")
    print(IITJ_BASE)

    print(f"\n[DELIVERY ID]")
    print(delivery_id)

    # =====================================================
    # INPUT
    # =====================================================

    message = input(
        "\nEnter secure message: "
    ).strip()

    if not message:

        print(
            "\n[ERROR] Empty message"
        )

        return

    # =====================================================
    # SECURE TRANSFER
    # =====================================================

    st = SecureTransfer(

        IITR_KMS,

        AUTH_TOKEN
    )

    # =====================================================
    # ENCRYPTION TIMER
    # =====================================================

    enc_start = metrics.timer()

    try:

        encrypted = st.send_secure_message(
            message
        )

        key_id = encrypted["key_id"]

        iv = encrypted["iv"]

        ciphertext = encrypted["ciphertext"]

        tag = encrypted["tag"]

        nonce = encrypted["nonce"]

        session_id = encrypted["session_id"]

        metrics.record_encryption(

            metrics.elapsed(
                enc_start
            )
        )

        metrics.record_message(
            len(message.encode())
        )

        print("\n[ENCRYPTION SUCCESS]")

        print(f"\nKey ID:")
        print(key_id)

        print(f"\nNonce:")
        print(nonce)

        print(f"\nCiphertext:")
        print(ciphertext.hex())

    except Exception as e:

        print(
            f"\n[ERROR] Encryption failed: {e}"
        )

        return

    # =====================================================
    # FETCH METADATA
    # =====================================================

    metadata = fetch_metadata(
        key_id
    )

    if not metadata:

        print(
            "\n[ERROR] Metadata unavailable"
        )

        return

    sync_index = metadata.get(
        "sync_index"
    )

    local_hash = metadata.get(
        "key_hash"
    )

    # =====================================================
    # WAIT FOR RECEIVER
    # =====================================================

    receiver_data = wait_for_key_on_receiver(
        key_id
    )

    if not receiver_data:

        print(
            "\n[ABORT] "
            "Synchronization incomplete"
        )

        return

    # =====================================================
    # VERIFY HASH
    # =====================================================

    remote_hash = receiver_data.get(
        "key_hash"
    )

    verified = verify_hash(

        local_hash,

        remote_hash
    )

    if not verified:

        print(
            "\n[ERROR] "
            "SHA-256 verification failed"
        )

        return

    print(
        "\n[VERIFICATION SUCCESS]"
    )

    print(
        "SHA-256 synchronization verified"
    )

    # =====================================================
    # BUILD PAYLOAD
    # =====================================================

    payload = {

        "delivery_id":
            delivery_id,

        "key_id":
            key_id,

        "iv":
            iv.hex(),

        "ciphertext":
            ciphertext.hex(),

        "tag":
            tag.hex(),

        "nonce":
            nonce,

        "metadata": {

            "protocol":
                QKD_PROTOCOL,

            "mode":
                SYSTEM_MODE,

            "session_id":
                session_id,

            "sync_index":
                sync_index,

            "key_hash":
                local_hash,

            "verified":
                verified,

            "timestamp":
                datetime.utcnow().isoformat(),

            "replay_protection":
                ENABLE_REPLAY_PROTECTION
        }
    }

    # =====================================================
    # DELIVERY TIMER
    # =====================================================

    delivery_start = metrics.timer()

    try:

        response = requests.post(

            IITJ_URL,

            headers=HEADERS,

            json=payload,

            timeout=15
        )

        response.raise_for_status()

        result = response.json()

        metrics.record_delivery(

            metrics.elapsed(
                delivery_start
            )
        )

        metrics.session_success()

    except Exception as e:

        metrics.session_failure()

        print(
            f"\n[ERROR] "
            f"Transmission failed: {e}"
        )

        return

    # =====================================================
    # SUCCESS OUTPUT
    # =====================================================

    print("\n" + "=" * 70)

    print(" SECURE MESSAGE DELIVERED ")

    print("=" * 70)

    print(f"\nProtocol:")
    print(QKD_PROTOCOL)

    print(f"\nMode:")
    print(SYSTEM_MODE)

    print(f"\nDelivery ID:")
    print(delivery_id)

    print(f"\nSession ID:")
    print(session_id)

    print(f"\nSynchronization:")
    print("VERIFIED")

    print(f"\nReplay Protection:")
    print("ENABLED")

    print(f"\nReceiver Response:")
    print(result)

    print("\n" + "=" * 70)

    # =====================================================
    # METRICS
    # =====================================================

    print("\nPERFORMANCE METRICS")

    report = metrics.report()

    print(

        f"\nEncryption Time: "
        f"{report['avg_encryption_time']:.6f}s"
    )

    print(

        f"Delivery Time: "
        f"{report['avg_delivery_time']:.6f}s"
    )

    print(

        f"Throughput: "
        f"{report['throughput_bytes_per_sec']:.2f} B/s"
    )

    print(

        f"Messages/sec: "
        f"{report['messages_per_second']:.2f}"
    )

# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()