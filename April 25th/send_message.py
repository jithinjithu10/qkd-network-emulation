# send_message.py
# FINAL PRODUCTION VERSION

import requests
import time
from secure_transfer import SecureTransfer
from config import AUTH_TOKEN


# =================================================
# CONFIGURATION
# =================================================

KMS_URL = "http://127.0.0.1:8000"   # IITR
IITJ_BASE = "http://127.0.0.1:8001" # IITJ
IITJ_URL = f"{IITJ_BASE}/receive-message"

TOKEN = AUTH_TOKEN


# =================================================
# WAIT FOR KEY SYNC
# =================================================

def wait_for_key_on_receiver(key_id):

    print(f"\n[SYNC] Waiting for IITJ to receive key {key_id}...")

    for _ in range(10):
        try:
            r = requests.get(
                f"{IITJ_BASE}/etsi/v2/keys/{key_id}",
                headers={"Authorization": f"Bearer {TOKEN}"},
                timeout=3
            )

            if r.status_code == 200:
                print("[SYNC SUCCESS] Key available on IITJ")
                return True

        except:
            pass

        time.sleep(0.5)

    print("[SYNC FAILED] IITJ does not have the key yet")
    return False


# =================================================
# MAIN
# =================================================

def main():

    print("=" * 60)
    print("IITR → IITJ Secure Message Sender")
    print("=" * 60)

    message = input("\nEnter message to send: ").strip()

    if not message:
        print("Message cannot be empty")
        return

    st = SecureTransfer(KMS_URL, TOKEN)

    try:
        key_id, iv, ciphertext, tag = st.send_secure_message(message)

        print("\n[ENCRYPTION SUCCESS]")
        print(f"Key ID: {key_id}")
        print(f"Ciphertext: {ciphertext.hex()}")

    except Exception as e:
        print(f"[ERROR] Encryption failed: {e}")
        return

    # -------------------------------
    # WAIT FOR SYNC
    # -------------------------------
    if not wait_for_key_on_receiver(key_id):
        print("[ABORT] Not sending message (key not synced)")
        return

    # -------------------------------
    # SEND MESSAGE
    # -------------------------------
    try:
        response = requests.post(
            IITJ_URL,
            headers={"Authorization": f"Bearer {TOKEN}"},  # FIXED
            json={
                "key_id": key_id,
                "iv": iv.hex(),
                "ciphertext": ciphertext.hex(),
                "tag": tag.hex()
            },
            timeout=15
        )

        response.raise_for_status()

        print("\n[DELIVERY SUCCESS]")
        print("Response from IITJ:", response.json())

    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")


# =================================================
# ENTRY
# =================================================

if __name__ == "__main__":
    main()