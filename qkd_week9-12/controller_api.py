"""
controller_api.py
------------------

Central QKD Network Controller REST Layer

Weeks 7–12 compliant
ETSI-style Control Plane abstraction

Provides:
- Node registration
- Node authentication
- Link management
- Topology inspection
- Link degradation simulation
- Network metrics view
"""

from fastapi import APIRouter, HTTPException
from controller import QKDController
from models import LinkStatus
from audit import log_network_event

router = APIRouter()

controller = QKDController()


# =================================================
# NODE REGISTRATION
# =================================================

@router.post("/controller/register")
def register_node(request: dict):

    node_id = request.get("node_id")
    ip = request.get("ip")

    if not node_id or not ip:
        raise HTTPException(status_code=400, detail="node_id and ip required")

    response = controller.register_node(node_id, ip)

    log_network_event(f"Node registered: {node_id} ({ip})")

    return response


# =================================================
# NODE AUTHENTICATION
# =================================================

@router.post("/controller/authenticate")
def authenticate_node(request: dict):

    node_id = request.get("node_id")
    token = request.get("token")

    if not node_id or not token:
        raise HTTPException(status_code=400, detail="node_id and token required")

    if controller.registry.authenticate(node_id, token):
        return {"status": "AUTH_SUCCESS"}

    raise HTTPException(status_code=401, detail="AUTH_FAILED")


# =================================================
# LINK UPDATE
# =================================================

@router.post("/controller/link/update")
def update_link(request: dict):

    node_a = request.get("node_a")
    node_b = request.get("node_b")
    rate = request.get("rate")
    status = request.get("status")

    if not node_a or not node_b:
        raise HTTPException(status_code=400, detail="node_a and node_b required")

    if not rate:
        rate = 1000

    if not status:
        status = LinkStatus.AVAILABLE.value

    response = controller.update_link(
        node_a,
        node_b,
        rate,
        status
    )

    log_network_event(
        f"Link updated: {node_a} <-> {node_b} | Rate={rate} | Status={status}"
    )

    return response


# =================================================
# LINK DEGRADATION (Week 11 Testing)
# =================================================

@router.post("/controller/link/degrade")
def degrade_link(request: dict):

    node_a = request.get("node_a")
    node_b = request.get("node_b")
    new_rate = request.get("rate", 100)

    if not node_a or not node_b:
        raise HTTPException(status_code=400, detail="node_a and node_b required")

    controller.update_link(
        node_a,
        node_b,
        new_rate,
        LinkStatus.DEGRADED.value
    )

    log_network_event(
        f"Link degraded: {node_a} <-> {node_b} | NewRate={new_rate}"
    )

    return {"status": "LINK_DEGRADED"}


# =================================================
# TOPOLOGY VIEW
# =================================================

@router.get("/controller/topology")
def get_topology():

    topology = controller.get_topology()

    return topology


# =================================================
# NETWORK METRICS (Week 12)
# =================================================

@router.get("/controller/metrics")
def get_metrics():

    return {
        "registered_nodes_count": len(controller.registry.list_nodes()),
        "total_links": len(controller.link_manager.list_links())
    }
