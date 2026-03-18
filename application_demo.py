"""
application_demo.py (UPDATED)

Demonstrates secure communication using:
- ETSI KMS (session-based)
- SYNC mode (aligned with buffer)
"""

from secure_transfer import SecureTransfer
from crypto_engine import CryptoEngine
import hashlib


# =================================================
# CONFIGURATION
# =================================================

KMS_URL = "http://10.13.2.132:8001"
TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"

USE_SYNC_MODE = False   # True → simulate QKD sync


# =================================================
# SYNC KEY GENERATOR (MATCH BUFFER LOGIC)
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
    # MODE 1 → ETSI KMS (SESSION-BASED)
    # =================================================
    if not USE_SYNC_MODE:

        print("\n[MODE] ETSI KMS (Session-Based)")

        app = SecureTransfer(KMS_URL, TOKEN)

        #  Now returns session_id instead of raw key
        session_id, iv, ciphertext = app.send_secure_message(message)

        print("\nEncrypted Ciphertext:")
        print(ciphertext.hex())

        print("\nSession ID (share this):")
        print(session_id)

        #  Receiver uses session_id (not raw key)
        decrypted = app.receive_secure_message(
            session_id,
            iv,
            ciphertext
        )


    # =================================================
    # MODE 2 → SYNC MODE (MATCH BUFFER INDEX)
    # =================================================
    else:

        print("\n[MODE] Synchronized Key Generation")

        sync_index = 0   #  MUST match buffer start

        key = generate_sync_key(sync_index)

        ce = CryptoEngine(key)

        iv, ciphertext = ce.encrypt(message.encode())

        print("\nEncrypted Ciphertext:")
        print(ciphertext.hex())

        # simulate receiver side
        ce2 = CryptoEngine(key)

        decrypted = ce2.decrypt(iv, ciphertext).decode()


    print("\nDecrypted Message:")
    print(decrypted)

    print("\n✔ Secure transmission successful")


if __name__ == "__main__":
    run_demo()