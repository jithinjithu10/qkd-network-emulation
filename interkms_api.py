"""
interkms_api.py

Inter-KMS Interface (Node-to-Node Communication)

Used ONLY for trusted node communication.
Not exposed to application clients.

Implements:
- POST /interkms/v1/request-key
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from buffers import QBuffer
from audit import AuditLogger
from config import AUTH_ENABLED, AUTH_TOKEN

router = APIRouter()

buffer = QBuffer()
audit = AuditLogger()

security = HTTPBearer()


# =================================================
# AUTHENTICATION (Node-to-Node)
# =================================================

def verify_node_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    if not AUTH_ENABLED:
        return True

    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    if credentials.credentials != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid node token")

    return True


# =================================================
# INTER-KMS KEY REQUEST
# =================================================

@router.post("/interkms/v1/request-key")
def request_key(auth: bool = Depends(verify_node_token)):

    key = buffer.get_next_key()

    if not key:
        raise HTTPException(status_code=404, detail="No keys available")

    audit.key_consumed(key.key_id)

    return {
        "key_ID": key.key_id,
        "key": key.key_value,
        "size": key.key_size
    }