"""
application_demo.py (FINAL FIXED VERSION)

Purpose:
Demonstrates secure communication using:
1. ETSI KMS mode (real IITR ↔ IITJ communication)
2. Local SYNC mode (deterministic keys)

Fixes:
- Uses config.AUTH_TOKEN
- Separate sender and receiver objects
- Wait for key sync before decryption
- Uses shared config seed
"""

from secure_transfer import SecureTransfer
from crypto_engine import CryptoEngine
from config import AUTH_TOKEN, SYNC_SEED
import hashlib
import time


# =================================================
# CONFIGURATION
# =================================================

KMS_URL = "http://103.37.201.5:8000"

# True → local sync
# False → real KMS mode
USE_SYNC_MODE = False


# =================================================
# SYNC KEY GENERATION
# =================================================
def generate_sync_key(index: int) -> str:
    return hashlib.sha256(
        f"{SYNC_SEED}-{index}".encode()
    ).hexdigest()


# =================================================
# WAIT FOR KEY (CRITICAL FOR REAL MODE)
# =================================================
def wait_for_key(kms_url, key_id):

    for _ in range(10):
        try:
            import requests

            r = requests.get(
                f"{kms_url}/etsi/v2/keys/{key_id}",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                timeout=3
            )

            if r.status_code == 200:
                return True

        except:
            pass

        time.sleep(0.5)

    return False


# =================================================
# DEMO FUNCTION
# =================================================
def run_demo():

    message = "Hello from QKD secure channel"

    print("\n==============================")
    print(" QKD Secure Communication Demo")
    print("==============================")

    print("\nOriginal Message:")
    print(message)


    # =================================================
    # MODE 1: REAL KMS
    # =================================================
    if not USE_SYNC_MODE:

        print("\n[MODE] KMS (Key_ID Based Synchronization)")

        try:
            sender = SecureTransfer(KMS_URL, AUTH_TOKEN)

            # -------------------------------
            # SENDER
            # -------------------------------
            key_id, iv, ciphertext, tag = sender.send_secure_message(message)

            print("\nEncrypted Ciphertext:")
            print(ciphertext.hex())

            print("\nKey ID:")
            print(key_id)

            # -------------------------------
            # WAIT FOR SYNC
            # -------------------------------
            print("\nWaiting for receiver sync...")
            if not wait_for_key(KMS_URL, key_id):
                print("Receiver does not have key yet")
                return

            # -------------------------------
            # RECEIVER (SEPARATE INSTANCE)
            # -------------------------------
            receiver = SecureTransfer(KMS_URL, AUTH_TOKEN)

            decrypted = receiver.receive_secure_message(
                key_id,
                iv,
                ciphertext,
                tag
            )

        except Exception as e:
            print(f"[ERROR] KMS mode failed: {e}")
            return


    # =================================================
    # MODE 2: LOCAL SYNC
    # =================================================
    else:

        print("\n[MODE] Local Sync")

        try:
            key_id = "0"

            key_hex = generate_sync_key(int(key_id))

            ce = CryptoEngine(
                key_hex,
                key_id=key_id,
                mode="SYNC"
            )

            iv, ciphertext, tag = ce.encrypt(message.encode())

            print("\nEncrypted Ciphertext:")
            print(ciphertext.hex())

            ce2 = CryptoEngine(
                generate_sync_key(int(key_id)),
                key_id=key_id,
                mode="SYNC"
            )

            decrypted = ce2.decrypt(iv, ciphertext, tag).decode()

        except Exception as e:
            print(f"[ERROR] SYNC mode failed: {e}")
            return


    # =================================================
    # FINAL OUTPUT
    # =================================================
    print("\nDecrypted Message:")
    print(decrypted)

    print("\nSecure transmission successful")


# =================================================
# ENTRY POINT
# =================================================
if __name__ == "__main__":
    run_demo()