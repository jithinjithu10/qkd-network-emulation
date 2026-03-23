"""
application_demo.py (UPDATED - FINAL CORRECT)

Fixes:
- Includes AES-GCM tag
- Matches SecureTransfer API
- Consistent with research model
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
# SYNC KEY GENERATOR
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
    # MODE 1 → ETSI KMS
    # =================================================
    if not USE_SYNC_MODE:

        print("\n[MODE] ETSI KMS (Session-Based)")

        app = SecureTransfer(KMS_URL, TOKEN)

        #  FIXED: includes tag
        session_id, iv, ciphertext, tag = app.send_secure_message(message)

        print("\nEncrypted Ciphertext:")
        print(ciphertext.hex())

        print("\nSession ID (share this):")
        print(session_id)

        print("\nTag:")
        print(tag.hex())

        #  FIXED: pass tag also
        decrypted = app.receive_secure_message(
            session_id,
            iv,
            ciphertext,
            tag
        )


    # =================================================
    # MODE 2 → SYNC MODE
    # =================================================
    else:

        print("\n[MODE] Synchronized Key Generation")

        sync_index = 0   # must match sender

        key = generate_sync_key(sync_index)

        ce = CryptoEngine(key)

        # FIXED: include tag
        iv, ciphertext, tag = ce.encrypt(message.encode())

        print("\nEncrypted Ciphertext:")
        print(ciphertext.hex())

        print("\nTag:")
        print(tag.hex())

        # simulate receiver
        ce2 = CryptoEngine(key)

        decrypted = ce2.decrypt(iv, ciphertext, tag).decode()


    print("\nDecrypted Message:")
    print(decrypted)

    print("\n✔ Secure transmission successful")


if __name__ == "__main__":
    run_demo()