"""
application_demo.py (FINAL - SYNC + KMS CORRECT)

Fixes:
- Uses key_id properly (not confusing session_id)
- Works with IITR ↔ IITJ synced KMS
- Clean separation of modes
- Simple and clear
"""

from secure_transfer import SecureTransfer
from crypto_engine import CryptoEngine
import hashlib


# =================================================
# CONFIG
# =================================================

KMS_URL = "http://10.13.2.132:8001"
TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"

USE_SYNC_MODE = False   # True → local sync (no KMS)


# =================================================
# SIMPLE SYNC KEY (FOR TEST MODE)
# =================================================

def generate_sync_key(index):
    seed = "QKD_SHARED_SEED_2026"
    return hashlib.sha256(f"{seed}-{index}".encode()).hexdigest()


# =================================================
# DEMO
# =================================================

def run_demo():

    message = "Hello from QKD secure channel"

    print("\n==============================")
    print(" QKD Secure Communication Demo")
    print("==============================")

    print("\nOriginal Message:")
    print(message)


    # =================================================
    # MODE 1 → REAL KMS (IITR ↔ IITJ SYNC)
    # =================================================
    if not USE_SYNC_MODE:

        print("\n[MODE] KMS (Key_ID Based Sync)")

        app = SecureTransfer(KMS_URL, TOKEN)

        # -------------------------------
        # SENDER SIDE
        # -------------------------------
        key_id, iv, ciphertext, tag = app.send_secure_message(message)

        print("\nEncrypted Ciphertext:")
        print(ciphertext.hex())

        print("\nKey ID (share this):")
        print(key_id)

        print("\nTag:")
        print(tag.hex())

        # -------------------------------
        # RECEIVER SIDE
        # -------------------------------
        decrypted = app.receive_secure_message(
            key_id,
            iv,
            ciphertext,
            tag
        )


    # =================================================
    # MODE 2 → LOCAL SYNC (NO KMS)
    # =================================================
    else:

        print("\n[MODE] Local Sync (Same Key Generation)")

        key_id = 0   # must match on both sides

        key = generate_sync_key(key_id)

        ce = CryptoEngine(key)

        iv, ciphertext, tag = ce.encrypt(message.encode())

        print("\nEncrypted Ciphertext:")
        print(ciphertext.hex())

        print("\nKey ID:")
        print(key_id)

        print("\nTag:")
        print(tag.hex())

        # receiver uses SAME key_id
        key2 = generate_sync_key(key_id)

        ce2 = CryptoEngine(key2)

        decrypted = ce2.decrypt(iv, ciphertext, tag).decode()


    print("\nDecrypted Message:")
    print(decrypted)

    print("\n✔ Secure transmission successful")


# =================================================
# MAIN
# =================================================

if __name__ == "__main__":
    run_demo()