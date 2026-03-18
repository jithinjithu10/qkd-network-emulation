"""
node_registry.py
----------------

QKD Node Registry
Weeks 7–11 Ready

Supports:
- Node registration
- Authentication tokens
- Heartbeat tracking
- Status monitoring
- Offline detection
- Multi-node topology (6 nodes ready)
"""

import uuid
from datetime import datetime, timezone, timedelta
from models import NodeStatus


HEARTBEAT_TIMEOUT_SECONDS = 30


class NodeRegistry:

    def __init__(self):
        # Format:
        # {
        #   "NODE_ID": {
        #       "ip": "...",
        #       "auth_token": "...",
        #       "status": NodeStatus.ONLINE,
        #       "registered_at": timestamp,
        #       "last_heartbeat": timestamp
        #   }
        # }
        self.nodes = {}

    # =================================================
    # REGISTER NODE
    # =================================================
    def register(self, node_id, ip_address):

        if node_id in self.nodes:
            return {"status": "ALREADY_REGISTERED"}

        token = str(uuid.uuid4())

        now = datetime.now(timezone.utc)

        self.nodes[node_id] = {
            "ip": ip_address,
            "auth_token": token,
            "status": NodeStatus.ONLINE,
            "registered_at": now,
            "last_heartbeat": now
        }

        return {
            "status": "REGISTERED",
            "auth_token": token
        }

    # =================================================
    # AUTHENTICATION
    # =================================================
    def authenticate(self, node_id, token):

        node = self.nodes.get(node_id)

        if not node:
            return False

        return node["auth_token"] == token

    # =================================================
    # HEARTBEAT UPDATE
    # =================================================
    def heartbeat(self, node_id):

        node = self.nodes.get(node_id)

        if not node:
            return {"error": "NODE_NOT_FOUND"}

        node["last_heartbeat"] = datetime.now(timezone.utc)
        node["status"] = NodeStatus.ONLINE

        return {"status": "HEARTBEAT_UPDATED"}

    # =================================================
    # OFFLINE DETECTION (Week 11)
    # =================================================
    def check_node_health(self):

        now = datetime.now(timezone.utc)

        for node_id, node in self.nodes.items():

            if now - node["last_heartbeat"] > timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS):
                node["status"] = NodeStatus.OFFLINE

    # =================================================
    # MANUAL STATUS UPDATE
    # =================================================
    def update_status(self, node_id, status):

        node = self.nodes.get(node_id)

        if not node:
            return {"error": "NODE_NOT_FOUND"}

        node["status"] = status
        return {"status": "UPDATED"}

    # =================================================
    # GET NODE
    # =================================================
    def get_node(self, node_id):
        return self.nodes.get(node_id)

    # =================================================
    # LIST NODES (Basic)
    # =================================================
    def list_nodes(self):
        return list(self.nodes.keys())

    # =================================================
    # LIST FULL NODE DETAILS
    # =================================================
    def list_node_details(self):
        return self.nodes
