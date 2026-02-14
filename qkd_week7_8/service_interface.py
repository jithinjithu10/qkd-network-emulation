"""
service_interface.py
---------------------
Implements ETSI-style service interface.

APIs:
- GET_STATUS
- GET_KEY
- RESERVE_KEY
"""

from fastapi import APIRouter
from storage import fetch_ready_key
from models import KeyRole


router = APIRouter()


@router.get("/api/v2/status")
def get_status():
    return {
        "service": "QKD-KMS",
        "version": "v2",
        "status": "RUNNING"
    }


@router.post("/api/v2/get_key")
def get_key(request: dict):
    role = KeyRole(request.get("role", "ENC"))
    key_id = fetch_ready_key(role)

    if not key_id:
        return {"status": "NO_KEY_AVAILABLE"}

    return {
        "status": "KEY_AVAILABLE",
        "key_id": key_id
    }
