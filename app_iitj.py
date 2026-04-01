# app_iitj.py

import requests
import os
import sys
import json

KMS_URL = "http://localhost:8001"   # IITJ KMS
AUTH_TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"


# -------------------------------
# CHECK KMS
# -------------------------------
def check_kms():
    try:
        r = requests.get(
            f"{KMS_URL}/etsi/v2/status",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=5
        )

        r.raise_for_status()
        d = r.json()

        print(f"[KMS] {d['status']} — available keys: {d['available_keys']}")

    except Exception as e:
        print(f"[ERROR] Cannot reach KMS: {e}")
        sys.exit(1)


# -------------------------------
# GET KEY USING ID
# -------------------------------
def get_key_by_id(key_id):
    r = requests.get(
        f"{KMS_URL}/etsi/v2/keys/{key_id}",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
    )
    r.raise_for_status()
    return r.json()["key"]


# -------------------------------
# MAIN
# -------------------------------
def main():

    print("=" * 55)
    print("IIT Jammu — Secure Application (SYNC FIXED)")
    print("=" * 55)

    check_kms()

    print("\n1. Receive message")
    print("2. Decrypt file")

    choice = input("\nChoice [1/2]: ").strip()

    from secure_transfer import SecureTransfer
    from crypto_engine import CryptoEngine


    # -------------------------------
    # RECEIVE MESSAGE
    # -------------------------------
    if choice == "1":

        session_id = input("session_id (key_id): ")
        iv_hex = input("iv: ")
        ct_hex = input("ciphertext: ")
        tag_hex = input("tag: ")

        st = SecureTransfer(KMS_URL, AUTH_TOKEN)

        plaintext = st.receive_secure_message(
            session_id,
            bytes.fromhex(iv_hex),
            bytes.fromhex(ct_hex),
            bytes.fromhex(tag_hex)
        )

        print("\nDecrypted message:", plaintext)


    # -------------------------------
    # FILE DECRYPTION
    # -------------------------------
    elif choice == "2":

        enc_file = input("Encrypted file (json): ")

        if not os.path.exists(enc_file):
            print("File not found")
            return

        with open(enc_file, "r") as f:
            encrypted_chunks = json.load(f)

        decrypted_data = b""

        for chunk in encrypted_chunks:

            key_id = chunk["key_id"]

            # get correct key using id
            key_hex = get_key_by_id(key_id)

            ce = CryptoEngine(key_hex)

            plaintext = ce.decrypt(
                bytes.fromhex(chunk["iv"]),
                bytes.fromhex(chunk["ciphertext"]),
                bytes.fromhex(chunk["tag"])
            )

            decrypted_data += plaintext

        with open("decrypted.txt", "wb") as f:
            f.write(decrypted_data)

        print("\nFile decrypted → decrypted.txt")


if __name__ == "__main__":
    main()