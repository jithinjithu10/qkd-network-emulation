# app_iitj.py (UPDATED VERSION - STABLE)

import requests
import os
import sys
import json

from config import AUTH_TOKEN, SYSTEM_MODE
from secure_transfer import SecureTransfer
from crypto_engine import CryptoEngine


# =================================================
# CONFIGURATION
# =================================================

KMS_URL = "http://localhost:8001"


# =================================================
# CHECK KMS STATUS
# =================================================
def check_kms():

    try:
        response = requests.get(
            f"{KMS_URL}/etsi/v2/status",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=5
        )

        response.raise_for_status()
        data = response.json()

        print(f"[KMS] {data['status']} — available keys: {data['available_keys']}")

    except Exception as e:
        print(f"[ERROR] Cannot reach KMS: {e}")
        sys.exit(1)


# =================================================
# GET KEY BY ID (WITH RETRY)
# =================================================
def get_key_by_id(key_id: str) -> str:

    for attempt in range(3):

        try:
            response = requests.get(
                f"{KMS_URL}/etsi/v2/keys/{key_id}",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                timeout=5
            )

            response.raise_for_status()
            data = response.json()

            key = data.get("key")

            if not key:
                raise ValueError("Invalid key response")

            return key

        except Exception as e:
            if attempt == 2:
                print(f"[ERROR] Failed to fetch key {key_id}: {e}")
                sys.exit(1)


# =================================================
# SAFE HEX CONVERSION
# =================================================
def safe_hex_to_bytes(value, field):

    try:
        return bytes.fromhex(value)
    except Exception:
        raise ValueError(f"Invalid hex input for {field}")


# =================================================
# MAIN APPLICATION
# =================================================
def main():

    print("=" * 60)
    print("IIT Jammu — Secure Application")
    print("=" * 60)

    check_kms()

    print("\n1. Receive message")
    print("2. Decrypt file")

    choice = input("\nChoice [1/2]: ").strip()

    # =================================================
    # OPTION 1: RECEIVE MESSAGE
    # =================================================
    if choice == "1":

        print("\nEnter encrypted message details:")

        key_id = input("key_id: ").strip()
        iv_hex = input("iv: ").strip()
        ct_hex = input("ciphertext: ").strip()
        tag_hex = input("tag: ").strip()

        try:
            st = SecureTransfer(KMS_URL, AUTH_TOKEN)

            plaintext = st.receive_secure_message(
                key_id,
                safe_hex_to_bytes(iv_hex, "iv"),
                safe_hex_to_bytes(ct_hex, "ciphertext"),
                safe_hex_to_bytes(tag_hex, "tag")
            )

            print("\nDecrypted message:")
            print(plaintext)

        except Exception as e:
            print(f"[ERROR] Decryption failed: {e}")

    # =================================================
    # OPTION 2: FILE DECRYPTION
    # =================================================
    elif choice == "2":

        enc_file = input("Encrypted file (json): ").strip()

        if not os.path.exists(enc_file):
            print("[ERROR] File not found")
            return

        try:
            with open(enc_file, "r") as f:
                encrypted_chunks = json.load(f)

        except Exception as e:
            print(f"[ERROR] Failed to read file: {e}")
            return

        decrypted_data = b""

        for idx, chunk in enumerate(encrypted_chunks):

            try:
                key_id = chunk["key_id"]

                key_hex = get_key_by_id(key_id)

                ce = CryptoEngine(
                    key_hex,
                    key_id=key_id,
                    mode=SYSTEM_MODE
                )

                plaintext = ce.decrypt(
                    bytes.fromhex(chunk["iv"]),
                    bytes.fromhex(chunk["ciphertext"]),
                    bytes.fromhex(chunk["tag"])
                )

                decrypted_data += plaintext

            except Exception as e:
                print(f"[ERROR] Failed at chunk {idx}: {e}")
                return

        try:
            with open("decrypted.txt", "wb") as f:
                f.write(decrypted_data)

            print("\nFile decrypted successfully → decrypted.txt")

        except Exception as e:
            print(f"[ERROR] Failed to write output file: {e}")

    else:
        print("Invalid choice")


# =================================================
# ENTRY POINT
# =================================================
if __name__ == "__main__":
    main()