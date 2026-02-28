"""
kms_server.py

Entry point for ETSI-compliant KMS server.
"""

from fastapi import FastAPI
from etsi_api import router
from config import HOST, PORT
import uvicorn


# =================================================
# FASTAPI APP
# =================================================

app = FastAPI(
    title="ETSI-Compliant QKD Key Management System",
    version="1.0"
)

app.include_router(router)


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