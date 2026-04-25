"""
application_demo.py

Purpose:
Demonstrates secure communication using:
1. ETSI KMS mode (real IITR ↔ IITJ communication)
2. Local SYNC mode (no KMS, deterministic key generation)

Fixes applied:
- Correct CryptoEngine initialization (requires key_id)
- Consistent use of key_id (no session_id confusion)
- Clean separation of modes
- Improved clarity and error handling
"""

from secure_transfer import SecureTransfer
from crypto_engine import CryptoEngine
import hashlib


# =================================================
# CONFIGURATION
# =================================================

# IMPORTANT:
# Replace with actual public IP when testing across IITR ↔ IITJ
KMS_URL = "http://103.37.201.5:8000"

TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"

# True  → local sync (no KMS)
# False → real KMS mode
USE_SYNC_MODE = False


# =================================================
# SYNC KEY GENERATION (TEST MODE ONLY)
# =================================================

def generate_sync_key(index: int) -> str:
    """
    Deterministic key generation for SYNC mode.
    Both sender and receiver must use the same index.
    """
    seed = "QKD_SHARED_SEED_2026"
    return hashlib.sha256(f"{seed}-{index}".encode()).hexdigest()


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
    # MODE 1: REAL KMS (ETSI MODE)
    # =================================================
    if not USE_SYNC_MODE:

        print("\n[MODE] KMS (Key_ID Based Synchronization)")

        try:
            app = SecureTransfer(KMS_URL, TOKEN)

            # -------------------------------
            # SENDER SIDE
            # -------------------------------
            key_id, iv, ciphertext, tag = app.send_secure_message(message)

            print("\nEncrypted Ciphertext:")
            print(ciphertext.hex())

            print("\nKey ID (shared between nodes):")
            print(key_id)

            print("\nAuthentication Tag:")
            print(tag.hex())

            # -------------------------------
            # RECEIVER SIDE (SIMULATED)
            # -------------------------------
            decrypted = app.receive_secure_message(
                key_id,
                iv,
                ciphertext,
                tag
            )

        except Exception as e:
            print(f"[ERROR] KMS mode failed: {e}")
            return


    # =================================================
    # MODE 2: LOCAL SYNC (NO KMS)
    # =================================================
    else:

        print("\n[MODE] Local Sync (Deterministic Key Generation)")

        try:
            key_id = "0"   # must match on both sides

            # Generate same key on both sides
            key_hex = generate_sync_key(int(key_id))

            # -------------------------------
            # SENDER SIDE
            # -------------------------------
            ce = CryptoEngine(
                key_hex,
                key_id=key_id,
                mode="SYNC"
            )

            iv, ciphertext, tag = ce.encrypt(message.encode())

            print("\nEncrypted Ciphertext:")
            print(ciphertext.hex())

            print("\nKey ID:")
            print(key_id)

            print("\nAuthentication Tag:")
            print(tag.hex())

            # -------------------------------
            # RECEIVER SIDE
            # -------------------------------
            key_hex_receiver = generate_sync_key(int(key_id))

            ce2 = CryptoEngine(
                key_hex_receiver,
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