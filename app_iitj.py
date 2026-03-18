"""
app_iitj.py  —  IIT Jammu Application (UPDATED)

Supports:
- Remote KMS (IITR)
- Session-based secure communication
- No manual key sharing
"""

import requests
import os
import sys

# 🔥 CHANGE THIS WHEN CONNECTING TO IITR
KMS_URL = "http://<IITR_IP>:8000"   # e.g., http://172.16.x.x:8000
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

        print(f"  [KMS] {d['status']} — available keys: {d['available_keys']}")

    except Exception as e:
        print(f"  [ERROR] Cannot reach KMS: {e}")
        sys.exit(1)


# =================================================
# MAIN
# =================================================

def main():

    print("=" * 55)
    print("  IIT Jammu — QKD Secure Application (UPDATED)")
    print("=" * 55)

    check_kms()

    print()
    print("  1. Send secure message (AUTO SYNC)")
    print("  2. Receive secure message (AUTO SYNC)")
    print("  3. Encrypt file")
    print("  4. Decrypt file")

    choice = input("\nChoice [1/2/3/4]: ").strip()

    from secure_transfer import SecureTransfer
    from crypto_engine import CryptoEngine


    # =================================================
    # SEND MESSAGE
    # =================================================

    if choice == "1":

        msg = input("Message to send: ")

        st = SecureTransfer(KMS_URL, AUTH_TOKEN)

        # 🔥 Automatically fetch synchronized key
        key_id, key_hex, iv, ct = st.send_secure_message(msg)

        print("\nSend this to receiver:\n")
        print("session_id:", key_id)
        print("iv:", iv.hex())
        print("ciphertext:", ct.hex())


    # =================================================
    # RECEIVE MESSAGE
    # =================================================

    elif choice == "2":

        session_id = input("session_id: ")
        iv_hex = input("iv: ")
        ct_hex = input("ciphertext: ")

        st = SecureTransfer(KMS_URL, AUTH_TOKEN)

        plaintext = st.receive_secure_message(
            session_id,
            bytes.fromhex(iv_hex),
            bytes.fromhex(ct_hex)
        )

        print("\nDecrypted message:", plaintext)


    # =================================================
    # FILE ENCRYPTION
    # =================================================

    elif choice == "3":

        file_path = input("File to encrypt: ")

        if not os.path.exists(file_path):
            print("File not found")
            return

        r = requests.post(
            f"{KMS_URL}/etsi/v2/keys",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )

        key_data = r.json()
        key_hex = key_data["key"]

        from crypto_engine import CryptoEngine

        with open(file_path, "rb") as f:
            data = f.read()

        ce = CryptoEngine(key_hex)
        iv, ciphertext = ce.encrypt(data)

        with open("encrypted.enc", "wb") as f:
            f.write(iv + ciphertext)

        print("\nFile encrypted → encrypted.enc")
        print("Share session key ID instead of raw key")


    # =================================================
    # FILE DECRYPTION
    # =================================================

    elif choice == "4":

        enc_file = input("Encrypted file: ")
        key_hex = input("key: ")

        with open(enc_file, "rb") as f:
            raw = f.read()

        iv = raw[:16]
        ciphertext = raw[16:]

        ce = CryptoEngine(key_hex)

        plaintext = ce.decrypt(iv, ciphertext)

        with open("decrypted.txt", "wb") as f:
            f.write(plaintext)

        print("File decrypted → decrypted.txt")


if __name__ == "__main__":
    main()