from fastapi import APIRouter
from controller import QKDController

router = APIRouter()
controller = QKDController()


@router.post("/controller/register")
def register_node(request: dict):
    return controller.register_node(
        request["node_id"],
        request["ip"]
    )


@router.post("/controller/link/update")
def update_link(request: dict):
    return controller.update_link(
        request["node_a"],
        request["node_b"],
        request["rate"],
        request["status"]
    )


@router.get("/controller/topology")
def get_topology():
    return controller.get_topology()
