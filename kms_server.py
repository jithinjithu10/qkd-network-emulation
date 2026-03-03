"""
kms_server.py

Entry point for ETSI-aligned QKD Node.

Implements:
- Shared local key buffer (QBuffer)
- ETSI Application Plane (v2)
- Inter-KMS Plane (Node-to-Node)
- Optional Inter-KMS Client (if NODE_ROLE = CLIENT)
- Clean dependency injection architecture
"""

from fastapi import FastAPI
import uvicorn

from config import HOST, PORT, NODE_ROLE
from buffers import QBuffer
from audit import AuditLogger

from etsi_api import create_etsi_router
from interkms_api import create_interkms_router
from interkms_client import InterKMSClient


# =================================================
# SHARED NODE COMPONENTS
# =================================================

buffer = QBuffer()
audit = AuditLogger()

# Inter-KMS Client (only active on CLIENT nodes)
interkms_client = InterKMSClient(buffer, audit)


# =================================================
# FASTAPI APPLICATION
# =================================================

app = FastAPI(
    title="ETSI-Aligned QKD Node",
    version="2.1",
    description="ETSI-compliant QKD Key Management Node"
)

app.include_router(create_etsi_router(buffer, audit))
app.include_router(create_interkms_router(buffer, audit))


# =================================================
# STARTUP EVENT
# =================================================

@app.on_event("startup")
def startup_event():
    """
    Automatically start Inter-KMS client
    if node is configured as CLIENT.
    """

    if NODE_ROLE == "CLIENT":
        interkms_client.start()
        print("[INFO] Inter-KMS client activated")


# =================================================
# MAIN ENTRY
# =================================================

if __name__ == "__main__":
    uvicorn.run(
        "kms_server:app",
        host=HOST,
        port=PORT,
        reload=False
    )