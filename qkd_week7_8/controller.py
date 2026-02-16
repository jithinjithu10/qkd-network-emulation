"""
controller.py
--------------
Active QKD Network Controller (Week 7 Integrated)
"""

import requests
from node_registry import NodeRegistry
from link_manager import LinkManager
from audit import log_network_event
from models import LinkStatus


class QKDController:

    def __init__(self):
        self.registry = NodeRegistry()
        self.link_manager = LinkManager()

    # -------------------------------------------------
    # Node Registration
    # -------------------------------------------------
    def register_node(self, node_id, ip_address):
        result = self.registry.register(node_id, ip_address)
        log_network_event(f"Node registered: {node_id} at {ip_address}")
        return result

    # -------------------------------------------------
    # Update Link
    # -------------------------------------------------
    def update_link(self, node_a, node_b, rate, status):
        result = self.link_manager.update_link(node_a, node_b, rate, status)
        log_network_event(f"Link updated: {node_a}-{node_b} | {status}")
        return result

    # -------------------------------------------------
    # Secure Forward Request
    # -------------------------------------------------
    def forward_request(self, node_id, token, endpoint, payload=None):

        if not self.registry.authenticate(node_id, token):
            return {"error": "UNAUTHORIZED_NODE"}

        link = self.link_manager.get_link_for_node(node_id)

        if not link or link["status"] != LinkStatus.AVAILABLE.value:
            return {"error": "LINK_UNAVAILABLE"}

        node = self.registry.get_node(node_id)
        url = f"http://{node['ip']}{endpoint}"

        try:
            if payload:
                response = requests.post(url, json=payload, timeout=5)
            else:
                response = requests.get(url, timeout=5)

            return response.json()

        except Exception as e:
            return {"error": str(e)}
