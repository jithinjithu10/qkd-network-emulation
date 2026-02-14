"""
node_registry.py
----------------
Handles QKD node registration and authentication.
"""

import uuid


class NodeRegistry:

    def __init__(self):
        self.nodes = {}

    def register(self, node_id, ip_address):
        if node_id in self.nodes:
            return {"status": "ALREADY_REGISTERED"}

        token = str(uuid.uuid4())  # simple auth token

        self.nodes[node_id] = {
            "ip": ip_address,
            "auth_token": token
        }

        return {
            "status": "REGISTERED",
            "auth_token": token
        }

    def authenticate(self, node_id, token):
        node = self.nodes.get(node_id)
        if not node:
            return False
        return node["auth_token"] == token

    def list_nodes(self):
        return list(self.nodes.keys())
