"""
controller.py
--------------
Central QKD Network Controller (Week 7)

Handles:
- Node registration
- Link abstraction
- Topology tracking
- Forwarding requests to registered nodes
"""

import requests
from node_registry import NodeRegistry
from link_manager import LinkManager


class QKDController:

    def __init__(self):
        self.registry = NodeRegistry()
        self.link_manager = LinkManager()

    # =================================================
    # NODE REGISTRATION
    # =================================================
    def register_node(self, node_id, ip_address):
        return self.registry.register(node_id, ip_address)

    # =================================================
    # LINK UPDATE
    # =================================================
    def update_link(self, node_a, node_b, rate, availability):
        return self.link_manager.update_link(
            node_a,
            node_b,
            rate,
            availability
        )

    # =================================================
    # TOPOLOGY VIEW
    # =================================================
    def get_topology(self):
        return {
            "registered_nodes": self.registry.list_nodes(),
            "links": self.link_manager.list_links()
        }

    # =================================================
    # FORWARD REQUEST (Control → Data Plane)
    # =================================================
    def forward_request(self, node_id, token, endpoint, payload=None):
        """
        Forward REST request to registered node.
        """

        node = self.registry.nodes.get(node_id)

        if not node:
            return {"error": "NODE_NOT_FOUND"}

        url = f"http://{node['ip']}:8001{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:
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

            return response.json()

        except Exception as e:
            return {"error": str(e)}
