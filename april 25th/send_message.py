# send_message.py
# Purpose:
# Sends encrypted message from IITR → IITJ over HTTP
#
# Flow:
# 1. Get key from IITR KMS
# 2. Encrypt message
# 3. Send to IITJ /receive-message API


import requests
from secure_transfer import SecureTransfer


# =================================================
# CONFIGURATION
# =================================================

# IMPORTANT: CHANGE THIS (IITR KMS)
# Your IITR public IP
KMS_URL = "http://103.37.201.5:8000"


# IMPORTANT: CHANGE THIS (IITJ RECEIVER)
# Replace with IITJ public IP
IITJ_URL = "http://<IITJ_PUBLIC_IP>:8001/receive-message"


# IMPORTANT: MUST MATCH config.py
TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"


# =================================================
# MAIN FUNCTION
# =================================================

def main():

    print("=" * 60)
    print("IITR → IITJ Secure Message Sender")
    print("=" * 60)

    message = input("\nEnter message to send: ").strip()

    if not message:
        print("Message cannot be empty")
        return

    # -------------------------------
    # INITIALIZE SECURE TRANSFER
    # -------------------------------
    st = SecureTransfer(KMS_URL, TOKEN)

    try:
        # -------------------------------
        # ENCRYPT MESSAGE
        # -------------------------------
        key_id, iv, ciphertext, tag = st.send_secure_message(message)

        print("\n[ENCRYPTION SUCCESS]")
        print(f"Key ID: {key_id}")
        print(f"Ciphertext: {ciphertext.hex()}")

    except Exception as e:
        print(f"[ERROR] Encryption failed: {e}")
        return

    # -------------------------------
    # SEND TO IITJ
    # -------------------------------
    try:
        response = requests.post(
            IITJ_URL,
            json={
                "key_id": key_id,
                "iv": iv.hex(),
                "ciphertext": ciphertext.hex(),
                "tag": tag.hex()
            },
            timeout=5
        )

        response.raise_for_status()

        print("\n[DELIVERY SUCCESS]")
        print("Response from IITJ:", response.json())

    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")


# =================================================
# ENTRY POINT
# =================================================

if __name__ == "__main__":
    main()