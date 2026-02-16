from fastapi import FastAPI, HTTPException
import os
from controller import QKDController
from models import LinkStatus

app = FastAPI(title="Local Client KMS")

CENTRAL_NODE_ID = "IITR"
CENTRAL_KMS_IP = os.getenv("CENTRAL_KMS_IP", "10.13.2.132")
REQUEST_TIMEOUT = 5

controller = QKDController()

# Register central node on startup
node_info = controller.register_node(CENTRAL_NODE_ID, CENTRAL_KMS_IP)
auth_token = node_info.get("auth_token")

controller.update_link(
    CENTRAL_NODE_ID,
    CENTRAL_NODE_ID,
    rate=1000,
    status=LinkStatus.AVAILABLE.value
)


@app.get("/api/v1/status")
def get_status():

    return controller.forward_request(
        CENTRAL_NODE_ID,
        auth_token,
        "/api/v1/status"
    )


@app.post("/api/v1/keys/generate")
def generate_keys(request: dict):

    return controller.forward_request(
        CENTRAL_NODE_ID,
        auth_token,
        "/api/v1/keys/generate",
        request
    )


@app.post("/api/v1/keys/promote")
def promote_keys():

    return controller.forward_request(
        CENTRAL_NODE_ID,
        auth_token,
        "/api/v1/keys/promote"
    )


@app.post("/api/v1/keys/allocate")
def allocate_key(request: dict):

    return controller.forward_request(
        CENTRAL_NODE_ID,
        auth_token,
        "/api/v1/keys/allocate",
        request
    )


@app.post("/api/v1/keys/consume")
def consume_key(request: dict):

    return controller.forward_request(
        CENTRAL_NODE_ID,
        auth_token,
        "/api/v1/keys/consume",
        request
    )


@app.get("/api/v1/buffer/status")
def buffer_status():

    return controller.forward_request(
        CENTRAL_NODE_ID,
        auth_token,
        "/api/v1/buffer/status"
    )
