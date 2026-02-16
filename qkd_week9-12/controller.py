"""
controller.py
--------------

Central QKD Network Controller
Weeks 7–12 Full Implementation
ETSI-style Control Plane

Supports:
- Multi-node topology (6 nodes)
- Link availability & degradation
- Forwarding enforcement
- Exhaustion-aware routing
- Stress simulation hooks
- Metrics collection
"""

import requests
import random
from datetime import datetime
from node_registry import NodeRegistry
from link_manager import LinkManager
from models import LinkStatus
from audit import log_network_event


class QKDController:

    def __init__(self):

        self.registry = NodeRegistry()
        self.link_manager = LinkManager()

        # Metrics (Week 12)
        self.metrics = {
            "total_forwarded_requests": 0,
            "failed_requests": 0,
            "degraded_routing_events": 0,
            "unavailable_link_blocks": 0
        }

    # =================================================
    # NODE REGISTRATION
    # =================================================
    def register_node(self, node_id, ip_address):

        response = self.registry.register(node_id, ip_address)

        log_network_event(f"[REGISTER] Node={node_id}")

        return response

    # =================================================
    # LINK UPDATE
    # =================================================
    def update_link(self, node_a, node_b, rate, status):

        response = self.link_manager.update_link(
            node_a,
            node_b,
            rate,
            status
        )

        log_network_event(
            f"[LINK UPDATE] {node_a} <-> {node_b} | Rate={rate} | Status={status}"
        )

        return response

    # =================================================
    # TOPOLOGY VIEW
    # =================================================
    def get_topology(self):

        return {
            "registered_nodes": self.registry.list_nodes(),
            "links": self.link_manager.list_links()
        }

    # =================================================
    # LINK CHECK
    # =================================================
    def _is_link_available(self, node_a, node_b):

        link = self.link_manager.get_link_for_node(node_a)

        if not link:
            return False, "LINK_NOT_FOUND"

        status = link["status"]

        if status == LinkStatus.UNAVAILABLE.value:
            self.metrics["unavailable_link_blocks"] += 1
            return False, "LINK_UNAVAILABLE"

        if status == LinkStatus.DEGRADED.value:
            self.metrics["degraded_routing_events"] += 1
            return True, "LINK_DEGRADED"

        return True, "LINK_AVAILABLE"

    # =================================================
    # FORWARD REQUEST
    # =================================================
    def forward_request(self, source_node, token, endpoint, payload=None):

        node = self.registry.get_node(source_node)

        if not node:
            self.metrics["failed_requests"] += 1
            return {"error": "NODE_NOT_FOUND"}

        available, link_status = self._is_link_available(
            source_node,
            source_node
        )

        if not available:
            return {"error": link_status}

        url = f"http://{node['ip']}:8001{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:

            # Simulate degraded link latency (Week 11)
            if link_status == "LINK_DEGRADED":
                delay = random.uniform(0.5, 1.5)

            if payload:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=5
                )
            else:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=5
                )

            self.metrics["total_forwarded_requests"] += 1

            log_network_event(
                f"[FORWARD] Node={source_node} | Endpoint={endpoint} | Status={link_status}"
            )

            return response.json()

        except Exception as e:

            self.metrics["failed_requests"] += 1

            log_network_event(
                f"[ERROR] Forwarding to {source_node} failed | {str(e)}"
            )

            return {"error": str(e)}

    # =================================================
    # WEEK 11 – LINK DEGRADATION SIMULATION
    # =================================================
    def simulate_link_degradation(self, node_id, probability=0.2):

        link = self.link_manager.get_link_for_node(node_id)

        if not link:
            return {"status": "LINK_NOT_FOUND"}

        if random.random() < probability:
            link["status"] = LinkStatus.DEGRADED.value
            log_network_event(f"[SIMULATION] Link degraded for {node_id}")
            return {"status": "DEGRADED"}

        link["status"] = LinkStatus.AVAILABLE.value
        return {"status": "AVAILABLE"}

    # =================================================
    # WEEK 12 – METRICS EXPORT
    # =================================================
    def get_metrics(self):

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.metrics
        }
