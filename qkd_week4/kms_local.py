"""
kms_local.py
-------------
Local client that requests keys from the Central KMS.
"""

from fastapi import FastAPI
import requests

app = FastAPI()

# Replace with actual server IP
CENTRAL_KMS_URL = "http://10.13.1.220:8001"


@app.post("/api/v1/request-key")
def request_key():
    """
    Request a cryptographic key from the Central KMS.
    """
    response = requests.post(
        f"{CENTRAL_KMS_URL}/api/v1/keys/get",
        json={
            "number_of_keys": 1,
            "key_size": 256
        }
    )

    return response.json()
