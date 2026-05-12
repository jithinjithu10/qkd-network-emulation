# app_iitj.py
# IITJ RECEIVER APPLICATION
# HYBRID QKD + CLASSICAL ARCHITECTURE

import requests
import os
import sys
import json
import hashlib

from config import AUTH_TOKEN, SYSTEM_MODE
from secure_transfer import SecureTransfer
from crypto_engine import CryptoEngine


# =====================================================
# CONFIGURATION
# =====================================================

KMS_URL = os.getenv(
    "KMS_URL",
    "http://localhost:8001"
)

LOCAL_NODE = "IITJ"


# =====================================================
# HASHING
# =====================================================

def sha256_hash(key_material: str):

    return hashlib.sha256(
        key_material.encode()
    ).hexdigest()


# =====================================================
# SAFE HEX CONVERSION
# =====================================================

def safe_hex_to_bytes(value, field):

    try:

        return bytes.fromhex(value)

    except Exception:

        raise ValueError(
            f"Invalid hex value for {field}"
        )


# =====================================================
# METADATA VALIDATION
# =====================================================

def validate_metadata(metadata):

    required_fields = [
        "key_id",
        "session_id",
        "sync_index",
        "key_hash"
    ]

    for field in required_fields:

        if field not in metadata:
            raise ValueError(
                f"Missing metadata field: {field}"
            )

    return True


# =====================================================
# CHECK KMS STATUS
# =====================================================

def check_kms():

    try:

        response = requests.get(
            f"{KMS_URL}/etsi/v2/status",
            headers={
                "Authorization": f"Bearer {AUTH_TOKEN}"
            },
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        print(
            f"[KMS STATUS] {data['status']} "
            f"| available keys = {data['available_keys']}"
        )

    except Exception as e:

        print(f"[ERROR] Cannot connect to KMS: {e}")
        sys.exit(1)


# =====================================================
# FETCH METADATA
# =====================================================

def get_key_metadata(key_id: str):

    """
    Public classical channel:
    exchanges metadata ONLY.

    NEVER raw quantum keys.
    """

    try:

        response = requests.get(
            f"{KMS_URL}/etsi/v2/keys/{key_id}",
            headers={
                "Authorization": f"Bearer {AUTH_TOKEN}"
            },
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        validate_metadata(data)

        return data

    except Exception as e:

        print(f"[ERROR] Metadata fetch failed: {e}")
        sys.exit(1)


# =====================================================
# FETCH LOCAL KEY
# =====================================================

def get_local_key(key_id: str):

    """
    Local QKD-derived key retrieval.

    Key should already exist locally
    from BB84/SimulaQron layer.
    """

    try:

        response = requests.get(
            f"{KMS_URL}/etsi/v2/keys/{key_id}",
            headers={
                "Authorization": f"Bearer {AUTH_TOKEN}"
            },
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        key = data.get("key")

        if not key:
            raise ValueError(
                "Local key unavailable"
            )

        return key

    except Exception as e:

        print(f"[ERROR] Local key retrieval failed: {e}")
        sys.exit(1)


# =====================================================
# VERIFY SYNCHRONIZATION
# =====================================================

def verify_key_synchronization(local_key, received_hash):

    local_hash = sha256_hash(local_key)

    if local_hash != received_hash:

        print("[SYNC ERROR]")
        print("Hash mismatch detected")

        return False

    return True


# =====================================================
# DISPLAY METADATA
# =====================================================

def display_metadata(metadata):

    print("\n========== SESSION METADATA ==========")

    print(f"key_id      : {metadata['key_id']}")
    print(f"session_id  : {metadata['session_id']}")
    print(f"sync_index  : {metadata['sync_index']}")
    print(f"key_hash    : {metadata['key_hash']}")

    print("======================================\n")


# =====================================================
# RECEIVE MESSAGE
# =====================================================

def receive_message():

    print("\nEnter encrypted message details:")

    key_id = input("key_id: ").strip()
    iv_hex = input("iv: ").strip()
    ct_hex = input("ciphertext: ").strip()
    tag_hex = input("tag: ").strip()

    try:

        # -------------------------------------------------
        # STEP 1 — FETCH METADATA
        # -------------------------------------------------

        metadata = get_key_metadata(key_id)

        display_metadata(metadata)

        received_hash = metadata["key_hash"]

        # -------------------------------------------------
        # STEP 2 — LOCAL QKD KEY
        # -------------------------------------------------

        local_key = get_local_key(key_id)

        # -------------------------------------------------
        # STEP 3 — VERIFY SYNCHRONIZATION
        # -------------------------------------------------

        verified = verify_key_synchronization(
            local_key,
            received_hash
        )

        if not verified:
            return

        print("[SYNC VERIFIED]")
        print("Shared QKD key validated")

        # -------------------------------------------------
        # STEP 4 — AES-GCM DECRYPTION
        # -------------------------------------------------

        st = SecureTransfer(
            KMS_URL,
            AUTH_TOKEN
        )

        plaintext = st.receive_secure_message(
            key_id,
            safe_hex_to_bytes(iv_hex, "iv"),
            safe_hex_to_bytes(ct_hex, "ciphertext"),
            safe_hex_to_bytes(tag_hex, "tag")
        )

        print("\n========== DECRYPTED MESSAGE ==========")
        print(plaintext)
        print("=======================================\n")

    except Exception as e:

        print(f"[ERROR] Secure receive failed: {e}")


# =====================================================
# FILE DECRYPTION
# =====================================================

def decrypt_file():

    enc_file = input(
        "Encrypted file (json): "
    ).strip()

    if not os.path.exists(enc_file):

        print("[ERROR] File not found")
        return

    try:

        with open(enc_file, "r") as f:

            encrypted_chunks = json.load(f)

    except Exception as e:

        print(f"[ERROR] Cannot read encrypted file: {e}")
        return

    decrypted_data = b""

    for idx, chunk in enumerate(encrypted_chunks):

        try:

            key_id = chunk["key_id"]

            # ---------------------------------------------
            # METADATA
            # ---------------------------------------------

            metadata = get_key_metadata(key_id)

            received_hash = metadata["key_hash"]

            # ---------------------------------------------
            # LOCAL KEY
            # ---------------------------------------------

            local_key = get_local_key(key_id)

            # ---------------------------------------------
            # VERIFY SYNCHRONIZATION
            # ---------------------------------------------

            verified = verify_key_synchronization(
                local_key,
                received_hash
            )

            if not verified:

                raise ValueError(
                    "Synchronization failed"
                )

            # ---------------------------------------------
            # AES-GCM DECRYPTION
            # ---------------------------------------------

            ce = CryptoEngine(
                local_key,
                key_id=key_id,
                mode=SYSTEM_MODE
            )

            plaintext = ce.decrypt(
                safe_hex_to_bytes(chunk["iv"], "iv"),
                safe_hex_to_bytes(chunk["ciphertext"], "ciphertext"),
                safe_hex_to_bytes(chunk["tag"], "tag")
            )

            decrypted_data += plaintext

        except Exception as e:

            print(
                f"[ERROR] Chunk {idx} failed: {e}"
            )

            return

    try:

        with open("decrypted.txt", "wb") as f:

            f.write(decrypted_data)

        print(
            "\n[SUCCESS] File decrypted → decrypted.txt"
        )

    except Exception as e:

        print(f"[ERROR] Output write failed: {e}")


# =====================================================
# MAIN
# =====================================================

def main():

    print("=" * 65)
    print("IIT Jammu — Hybrid Quantum-Classical Receiver")
    print("=" * 65)

    print(f"[INFO] Public Channel URL: {KMS_URL}")

    print(
        "[INFO] QKD keys expected from "
        "BB84/SimulaQron layer"
    )

    check_kms()

    print("\n1. Receive secure message")
    print("2. Decrypt encrypted file")

    choice = input("\nChoice [1/2]: ").strip()

    if choice == "1":

        receive_message()

    elif choice == "2":

        decrypt_file()

    else:

        print("Invalid choice")


# =====================================================
# ENTRY
# =====================================================

if __name__ == "__main__":

    main()