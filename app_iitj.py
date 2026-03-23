"""
app_iitj.py  —  IIT Jammu Application (UPDATED - RESEARCH CORRECT)

Fixes:
- No raw key usage
- Uses session_id (key_id)
- Supports chunk-based encryption (data-per-key)
- No manual key sharing
"""

import requests
import os
import sys

KMS_URL = "https://semipatriotic-lurkingly-janey.ngrok-free.dev"
AUTH_TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"


# =================================================
# CHECK KMS
# =================================================

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


# =================================================
# GET KEY FROM KMS (ONLY VIA ID)
# =================================================

def get_key():
    r = requests.post(
        f"{KMS_URL}/etsi/v2/keys",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
    )
    r.raise_for_status()
    return r.json()   # contains key_id + key


# =================================================
# MAIN
# =================================================

def main():

    print("=" * 55)
    print("IIT Jammu — QKD Secure Application (UPDATED)")
    print("=" * 55)

    check_kms()

    print("\n1. Send secure message")
    print("2. Receive secure message")
    print("3. Encrypt file (chunk-based)")
    print("4. Decrypt file (chunk-based)")

    choice = input("\nChoice [1/2/3/4]: ").strip()

    from secure_transfer import SecureTransfer
    from crypto_engine import CryptoEngine


    # =================================================
    # SEND MESSAGE
    # =================================================

    if choice == "1":

        msg = input("Message to send: ")

        st = SecureTransfer(KMS_URL, AUTH_TOKEN)

        session_id, iv, ciphertext, tag = st.send_secure_message(msg)

        print("\nSend this to receiver:\n")
        print("session_id:", session_id)
        print("iv:", iv.hex())
        print("ciphertext:", ciphertext.hex())
        print("tag:", tag.hex())


    # =================================================
    # RECEIVE MESSAGE
    # =================================================

    elif choice == "2":

        session_id = input("session_id: ")
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


    # =================================================
    # FILE ENCRYPTION (FIXED - CHUNK BASED)
    # =================================================

    elif choice == "3":

        file_path = input("File to encrypt: ")

        if not os.path.exists(file_path):
            print("File not found")
            return

        with open(file_path, "rb") as f:
            data = f.read()

        chunk_size = 32   # 32 bytes per key (IMPORTANT)

        encrypted_chunks = []

        for i in range(0, len(data), chunk_size):

            chunk = data[i:i + chunk_size]

            # get new key for each chunk
            key_data = get_key()
            key_id = key_data["key_id"]
            key_hex = key_data["key"]

            ce = CryptoEngine(key_hex)

            iv, ciphertext, tag = ce.encrypt(chunk)

            encrypted_chunks.append({
                "key_id": key_id,
                "iv": iv.hex(),
                "ciphertext": ciphertext.hex(),
                "tag": tag.hex()
            })

        # save as JSON-like file
        import json
        with open("encrypted.json", "w") as f:
            json.dump(encrypted_chunks, f)

        print("\nFile encrypted → encrypted.json")
        print("Share this file (contains key_ids, not keys)")


    # =================================================
    # FILE DECRYPTION (FIXED)
    # =================================================

    elif choice == "4":

        import json

        enc_file = input("Encrypted file (json): ")

        with open(enc_file, "r") as f:
            encrypted_chunks = json.load(f)

        decrypted_data = b""

        for chunk in encrypted_chunks:

            key_id = chunk["key_id"]

            # get key using key_id
            r = requests.get(
                f"{KMS_URL}/etsi/v2/keys/{key_id}",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
            )
            r.raise_for_status()

            key_hex = r.json()["key"]

            ce = CryptoEngine(key_hex)

            plaintext = ce.decrypt(
                bytes.fromhex(chunk["iv"]),
                bytes.fromhex(chunk["ciphertext"]),
                bytes.fromhex(chunk["tag"])
            )

            decrypted_data += plaintext

        with open("decrypted.txt", "wb") as f:
            f.write(decrypted_data)

        print("File decrypted → decrypted.txt")


if __name__ == "__main__":
    main()