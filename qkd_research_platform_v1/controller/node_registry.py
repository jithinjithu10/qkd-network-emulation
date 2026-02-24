"""
Research-Grade QKD Node Registry
DEBUG INSTRUMENTED VERSION
"""

import uuid
from datetime import datetime, timezone, timedelta
from qkd_research_platform_v1.core.models import NodeStatus


HEARTBEAT_TIMEOUT_SECONDS = 30


class NodeRegistry:

    def __init__(self):

        print("\n=== Initializing NodeRegistry ===")

        self.nodes = {}

        print("NodeRegistry initialized")


    # =================================================
    # REGISTER NODE
    # =================================================
    def register(self, node_id, ip_address, role="EDGE_KMS", capabilities=None):

        print(f"\nRegistering node: {node_id}")
        print(f"IP: {ip_address}")
        print(f"Role: {role}")

        if node_id in self.nodes:
            print("Node already registered")
            return {"status": "ALREADY_REGISTERED"}

        token = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        self.nodes[node_id] = {
            "ip": ip_address,
            "role": role,
            "capabilities": capabilities or {
                "supported_key_sizes": [128, 256],
                "max_rate": 1000,
                "quantum_capable": True
            },
            "auth_token": token,
            "status": NodeStatus.ONLINE,
            "registered_at": now,
            "last_heartbeat": now,
            "trust_score": 100,
            "failed_auth_attempts": 0
        }

        print("Node registered successfully")
        print("Auth token:", token)

        return {
            "status": "REGISTERED",
            "auth_token": token
        }


    # =================================================
    # AUTHENTICATION
    # =================================================
    def authenticate(self, node_id, token):

        print(f"\nAuthenticating node: {node_id}")

        node = self.nodes.get(node_id)

        if not node:
            print("Node not found")
            return False

        if node["auth_token"] != token:
            print("Authentication failed")
            node["failed_auth_attempts"] += 1
            node["trust_score"] -= 5
            return False

        print("Authentication successful")
        return True


    # =================================================
    # TOKEN ROTATION
    # =================================================
    def rotate_token(self, node_id):

        print(f"\nRotating token for node: {node_id}")

        node = self.nodes.get(node_id)

        if not node:
            print("Node not found")
            return {"error": "NODE_NOT_FOUND"}

        new_token = str(uuid.uuid4())
        node["auth_token"] = new_token

        print("Token rotated successfully")

        return {
            "status": "TOKEN_ROTATED",
            "auth_token": new_token
        }


    # =================================================
    # HEARTBEAT UPDATE
    # =================================================
    def heartbeat(self, node_id):

        print(f"\nHeartbeat received from: {node_id}")

        node = self.nodes.get(node_id)

        if not node:
            print("Node not found")
            return {"error": "NODE_NOT_FOUND"}

        node["last_heartbeat"] = datetime.now(timezone.utc)
        node["status"] = NodeStatus.ONLINE

        return {"status": "HEARTBEAT_UPDATED"}


    # =================================================
    # HEALTH CHECK
    # =================================================
    def check_node_health(self):

        print("\nRunning health check")

        now = datetime.now(timezone.utc)

        for node_id, node in self.nodes.items():

            if now - node["last_heartbeat"] > timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS):

                print(f"Node offline detected: {node_id}")

                node["status"] = NodeStatus.OFFLINE
                node["trust_score"] -= 10

            node["trust_score"] = max(0, node["trust_score"])

        print("Health check complete")


    # =================================================
    # MANUAL STATUS UPDATE
    # =================================================
    def update_status(self, node_id, status):

        print(f"\nUpdating status for {node_id} -> {status}")

        node = self.nodes.get(node_id)

        if not node:
            print("Node not found")
            return {"error": "NODE_NOT_FOUND"}

        node["status"] = status
        return {"status": "UPDATED"}


    # =================================================
    # GET NODE
    # =================================================
    def get_node(self, node_id):

        node = self.nodes.get(node_id)

        if not node:
            print(f"Node {node_id} not found")

        return node


    # =================================================
    # LIST NODES
    # =================================================
    def list_nodes(self):

        print("Listing nodes")

        return list(self.nodes.keys())


    # =================================================
    # LIST FULL NODE DETAILS
    # =================================================
    def list_node_details(self):

        print("Listing full node details")

        return self.nodes


    # =================================================
    # EXPORT METRICS
    # =================================================
    def export_metrics(self):

        total_nodes = len(self.nodes)

        online_nodes = len([
            n for n in self.nodes.values()
            if n["status"] == NodeStatus.ONLINE
        ])

        average_trust = (
            sum(n["trust_score"] for n in self.nodes.values()) / total_nodes
            if total_nodes > 0 else 0
        )

        metrics = {
            "total_nodes": total_nodes,
            "online_nodes": online_nodes,
            "average_trust_score": average_trust
        }

        print("\nNode Registry Metrics:", metrics)

        return metrics