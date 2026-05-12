"""
application_demo.py
HYBRID QUANTUM-CLASSICAL QKD DEMO
"""

import hashlib
import json
import os
import time
import uuid

import requests

from secure_transfer import SecureTransfer
from crypto_engine import CryptoEngine
from config import AUTH_TOKEN, SYNC_SEED


# =====================================================
# CONFIGURATION
# =====================================================

KMS_URL = os.getenv(
    "KMS_URL",
    "http://localhost:8000"
)

USE_SYNC_MODE = False

LOCAL_NODE = "IITR"


# =====================================================
# BB84 SIMULATION
# =====================================================

def generate_bb84_key(index: int) -> str:

    """
    Simulated BB84 synchronized key.

    Real deployment:
    - generated independently
    - derived from quantum layer
    - NEVER transported
    """

    return hashlib.sha256(
        f"{SYNC_SEED}-BB84-{index}".encode()
    ).hexdigest()


# =====================================================
# SHA-256 HASH
# =====================================================

def sha256_hash(key_material: str):

    return hashlib.sha256(
        key_material.encode()
    ).hexdigest()


# =====================================================
# METADATA VALIDATION
# =====================================================

def validate_metadata(metadata):

    required = [
        "session_id",
        "key_id",
        "sync_index",
        "key_hash"
    ]

    for field in required:

        if field not in metadata:

            raise ValueError(
                f"Missing metadata field: {field}"
            )

    return True


# =====================================================
# WAIT FOR SYNC
# =====================================================

def wait_for_metadata_sync(kms_url, key_id):

    """
    Wait for synchronization metadata.

    Public classical channel only.
    """

    for _ in range(20):

        try:

            response = requests.get(
                f"{kms_url}/etsi/v2/keys/{key_id}",
                headers={
                    "Authorization":
                        f"Bearer {AUTH_TOKEN}"
                },
                timeout=3
            )

            if response.status_code == 200:

                data = response.json()

                if data.get("key_hash"):

                    validate_metadata(data)

                    return data

        except Exception:
            pass

        time.sleep(0.5)

    return None


# =====================================================
# DISPLAY METADATA
# =====================================================

def display_metadata(metadata):

    print("\n========== SESSION METADATA ==========")

    print(f"session_id : {metadata['session_id']}")
    print(f"key_id     : {metadata['key_id']}")
    print(f"sync_index : {metadata['sync_index']}")
    print(f"key_hash   : {metadata['key_hash']}")

    print("======================================\n")


# =====================================================
# VERIFY SYNCHRONIZATION
# =====================================================

def verify_sync(local_key, received_hash):

    local_hash = sha256_hash(local_key)

    if local_hash != received_hash:

        print("[SYNC ERROR]")
        print("SHA-256 mismatch detected")

        return False

    return True


# =====================================================
# REAL KMS MODE
# =====================================================

def run_kms_mode(message):

    print("\n[MODE]")
    print("Hybrid QKD KMS Mode")

    try:

        # -------------------------------------------------
        # SESSION
        # -------------------------------------------------

        session_id = str(uuid.uuid4())[:8]

        sync_index = int(time.time())

        print(f"\n[SESSION] {session_id}")

        # -------------------------------------------------
        # SENDER
        # -------------------------------------------------

        sender = SecureTransfer(
            KMS_URL,
            AUTH_TOKEN
        )

        key_id, iv, ciphertext, tag = (
            sender.send_secure_message(message)
        )

        print("\n[CIPHERTEXT]")
        print(ciphertext.hex())

        print("\n[KEY ID]")
        print(key_id)

        # -------------------------------------------------
        # WAIT FOR SYNC
        # -------------------------------------------------

        print("\n[SYNC]")
        print("Waiting for metadata synchronization...")

        metadata = wait_for_metadata_sync(
            KMS_URL,
            key_id
        )

        if not metadata:

            print("[ERROR]")
            print("Synchronization timeout")

            return

        display_metadata(metadata)

        # -------------------------------------------------
        # LOCAL BB84 KEY
        # -------------------------------------------------

        """
        IMPORTANT:
        In real deployment,
        local_key must come from:
        - BB84 layer
        - local QKD buffer
        - synchronized derivation
        """

        local_key = generate_bb84_key(
            metadata["sync_index"]
        )

        # -------------------------------------------------
        # VERIFY HASH
        # -------------------------------------------------

        verified = verify_sync(
            local_key,
            metadata["key_hash"]
        )

        if not verified:

            print("[ERROR]")
            print("Synchronization failed")

            return

        print("[SYNC VERIFIED]")
        print("Both nodes derived identical key")

        # -------------------------------------------------
        # RECEIVER
        # -------------------------------------------------

        receiver = SecureTransfer(
            KMS_URL,
            AUTH_TOKEN
        )

        decrypted = receiver.receive_secure_message(
            key_id,
            iv,
            ciphertext,
            tag
        )

        print("\n[DECRYPTED MESSAGE]")
        print(decrypted)

        print("\n[SUCCESS]")
        print("Secure communication established")

    except Exception as e:

        print(f"[ERROR] KMS mode failed: {e}")


# =====================================================
# LOCAL SYNC MODE
# =====================================================

def run_sync_mode(message):

    print("\n[MODE]")
    print("Local BB84 Synchronization Simulation")

    try:

        # -------------------------------------------------
        # SESSION
        # -------------------------------------------------

        session_id = str(uuid.uuid4())[:8]

        sync_index = 0

        key_id = str(sync_index)

        print(f"\n[SESSION] {session_id}")

        # -------------------------------------------------
        # BB84 KEY
        # -------------------------------------------------

        sender_key = generate_bb84_key(
            sync_index
        )

        sender_hash = sha256_hash(
            sender_key
        )

        metadata = {
            "session_id": session_id,
            "key_id": key_id,
            "sync_index": sync_index,
            "key_hash": sender_hash
        }

        display_metadata(metadata)

        # -------------------------------------------------
        # AES ENCRYPTION
        # -------------------------------------------------

        ce_sender = CryptoEngine(
            sender_key,
            key_id=key_id,
            mode="SYNC"
        )

        iv, ciphertext, tag = ce_sender.encrypt(
            message.encode()
        )

        print("\n[CIPHERTEXT]")
        print(ciphertext.hex())

        # -------------------------------------------------
        # RECEIVER DERIVES SAME KEY
        # -------------------------------------------------

        receiver_key = generate_bb84_key(
            sync_index
        )

        # -------------------------------------------------
        # VERIFY
        # -------------------------------------------------

        verified = verify_sync(
            receiver_key,
            sender_hash
        )

        if not verified:

            print("[ERROR]")
            print("Synchronization failed")

            return

        print("\n[SYNC VERIFIED]")
        print("SHA-256 hashes matched")

        # -------------------------------------------------
        # AES DECRYPTION
        # -------------------------------------------------

        ce_receiver = CryptoEngine(
            receiver_key,
            key_id=key_id,
            mode="SYNC"
        )

        decrypted = ce_receiver.decrypt(
            iv,
            ciphertext,
            tag
        ).decode()

        print("\n[DECRYPTED MESSAGE]")
        print(decrypted)

        print("\n[SUCCESS]")
        print("Local quantum synchronization successful")

    except Exception as e:

        print(f"[ERROR] SYNC mode failed: {e}")


# =====================================================
# MAIN DEMO
# =====================================================

def run_demo():

    message = (
        "Hello from Hybrid Quantum-Classical "
        "Secure Communication Framework"
    )

    print("\n" + "=" * 65)
    print(" HYBRID QKD SECURE COMMUNICATION DEMO ")
    print("=" * 65)

    print("\n[ARCHITECTURE]")
    print("Quantum Channel   : SimulaQron + BB84")
    print("Classical Channel : FastAPI + ETSI APIs")
    print("Encryption        : AES-GCM")

    print(f"\n[KMS URL]")
    print(KMS_URL)

    print("\n[PLAINTEXT MESSAGE]")
    print(message)

    # -------------------------------------------------
    # MODE
    # -------------------------------------------------

    if USE_SYNC_MODE:

        run_sync_mode(message)

    else:

        run_kms_mode(message)


# =====================================================
# ENTRY
# =====================================================

if __name__ == "__main__":

    run_demo()