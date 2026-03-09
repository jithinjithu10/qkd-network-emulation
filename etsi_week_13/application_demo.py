"""
application_demo.py

Demonstrates secure communication using
QKD keys from ETSI KMS.
"""

from secure_transfer import SecureTransfer


KMS_URL = "http://127.0.0.1:8001"

TOKEN = "ETSI_DEMO_SECURE_TOKEN_2026"


def run_demo():

    app = SecureTransfer(KMS_URL, TOKEN)

    message = "Hello from QKD secure channel"

    print("\nOriginal Message:")
    print(message)

    key, iv, ciphertext = app.send_secure_message(message)

    print("\nEncrypted Ciphertext:")
    print(ciphertext.hex())

    decrypted = app.receive_secure_message(key, iv, ciphertext)

    print("\nDecrypted Message:")
    print(decrypted)


if __name__ == "__main__":
    run_demo()