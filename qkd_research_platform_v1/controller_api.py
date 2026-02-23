"""
controller_api.py
------------------

Active QKD Control Plane Router
Week 7–12 Research Grade

Provides:
- Node registration
- Token authentication
- Link management
- Topology inspection
- Heartbeat monitoring
- Capacity-aware forwarding
- Link-state enforcement
- Network metrics export
"""

from fastapi import APIRouter, HTTPException, Header
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

    return controller.register_node(node_id, ip)


# =================================================
# HEARTBEAT
# =================================================

@router.post("/controller/heartbeat")
def heartbeat(request: dict):

    node_id = request.get("node_id")

    if not node_id:
        raise HTTPException(status_code=400, detail="node_id required")

    return controller.registry.heartbeat(node_id)


# =================================================
# AUTHENTICATED LINK UPDATE
# =================================================

@router.post("/controller/link/update")
def update_link(
    request: dict,
    authorization: str = Header(None)
):

    node_a = request.get("node_a")
    node_b = request.get("node_b")
    rate = request.get("rate", 1000)
    status = request.get("status", LinkStatus.AVAILABLE.value)

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.replace("Bearer ", "")

    # Verify node_a owns token
    if not controller.registry.authenticate(node_a, token):
        raise HTTPException(status_code=401, detail="Invalid token")

    return controller.update_link(node_a, node_b, rate, status)


# =================================================
# ACTIVE FORWARDING ENDPOINT
# =================================================

@router.post("/controller/forward")
def forward_request(
    request: dict,
    authorization: str = Header(None)
):

    source_node = request.get("source_node")
    endpoint = request.get("endpoint")
    payload = request.get("payload")

    if not source_node or not endpoint:
        raise HTTPException(status_code=400, detail="source_node and endpoint required")

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    token = authorization.replace("Bearer ", "")

    # Authenticate node
    if not controller.registry.authenticate(source_node, token):
        raise HTTPException(status_code=401, detail="AUTH_FAILED")

    # Check link status
    link = controller.link_manager.get_link_for_node(source_node)

    if not link:
        raise HTTPException(status_code=400, detail="No link defined")

    if link["status"] == LinkStatus.UNAVAILABLE.value:
        raise HTTPException(status_code=503, detail="Link unavailable")

    if link["status"] == LinkStatus.DEGRADED.value:
        log_network_event(f"Degraded forwarding from {source_node}")

    # Capacity check
    if not controller.link_manager.is_capacity_available(
        link["node_a"],
        link["node_b"],
        required_rate=1
    ):
        raise HTTPException(status_code=503, detail="Insufficient capacity")

    # Record traffic
    controller.link_manager.record_traffic(
        link["node_a"],
        link["node_b"]
    )

    # Forward request
    response = controller.forward_request(
        source_node,
        token,
        endpoint,
        payload
    )

    return response


# =================================================
# TOPOLOGY VIEW
# =================================================

@router.get("/controller/topology")
def get_topology():

    return controller.get_topology()


# =================================================
# FULL NETWORK METRICS
# =================================================

@router.get("/controller/metrics")
def get_metrics():

    return {
        "registered_nodes": controller.registry.list_node_details(),
        "links": controller.link_manager.list_links(),
        "controller_metrics": controller.get_metrics()
    }