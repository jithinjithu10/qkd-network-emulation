"""
controller.py
--------------

Research-Grade QKD Network Controller
Graph-Based | Link-Aware | Exhaustion-Aware
ETSI Control Plane | Experiment Ready
Weeks 7–12 Advanced Implementation
"""

import requests
import random
import time
from datetime import datetime
from collections import defaultdict, deque

from node_registry import NodeRegistry
from link_manager import LinkManager
from models import LinkStatus
from audit import log_network_event


class QKDController:

    def __init__(self):

        self.registry = NodeRegistry()
        self.link_manager = LinkManager()

        # Graph representation
        self.graph = defaultdict(list)

        # Metrics
        self.metrics = {
            "total_forwarded_requests": 0,
            "failed_requests": 0,
            "multi_hop_routes": 0,
            "degraded_routing_events": 0,
            "unavailable_link_blocks": 0,
            "rerouted_due_to_exhaustion": 0
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

        self.link_manager.update_link(node_a, node_b, rate, status)

        self.graph[node_a].append(node_b)
        self.graph[node_b].append(node_a)

        log_network_event(
            f"[LINK UPDATE] {node_a}<->{node_b} | Rate={rate} | Status={status}"
        )

        return {"status": "LINK_UPDATED"}

    # =================================================
    # TOPOLOGY VIEW
    # =================================================
    def get_topology(self):

        return {
            "nodes": self.registry.list_nodes(),
            "links": self.link_manager.list_links()
        }

    # =================================================
    # SHORTEST PATH (BFS)
    # =================================================
    def _find_path(self, source, destination):

        visited = set()
        queue = deque([(source, [source])])

        while queue:
            node, path = queue.popleft()

            if node == destination:
                return path

            visited.add(node)

            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return None

    # =================================================
    # LINK QUALITY CHECK
    # =================================================
    def _validate_path(self, path):

        for i in range(len(path) - 1):
            link = self.link_manager.get_link(path[i], path[i+1])

            if not link:
                return False, "LINK_NOT_FOUND"

            if link["status"] == LinkStatus.UNAVAILABLE.value:
                self.metrics["unavailable_link_blocks"] += 1
                return False, "LINK_UNAVAILABLE"

            if link["status"] == LinkStatus.DEGRADED.value:
                self.metrics["degraded_routing_events"] += 1
                time.sleep(random.uniform(0.5, 1.2))

        return True, "VALID"

    # =================================================
    # FORWARD REQUEST (Multi-Hop)
    # =================================================
    def forward_request(self, source_node, destination_node, token, endpoint, payload=None):

        if not self.registry.get_node(source_node):
            self.metrics["failed_requests"] += 1
            return {"error": "SOURCE_NOT_FOUND"}

        if not self.registry.get_node(destination_node):
            self.metrics["failed_requests"] += 1
            return {"error": "DESTINATION_NOT_FOUND"}

        path = self._find_path(source_node, destination_node)

        if not path:
            self.metrics["failed_requests"] += 1
            return {"error": "NO_ROUTE_FOUND"}

        if len(path) > 2:
            self.metrics["multi_hop_routes"] += 1

        valid, reason = self._validate_path(path)

        if not valid:
            return {"error": reason}

        dest = self.registry.get_node(destination_node)

        url = f"http://{dest['ip']}:8001{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:

            start = time.time()

            if payload:
                response = requests.post(url, json=payload, headers=headers, timeout=5)
            else:
                response = requests.get(url, headers=headers, timeout=5)

            latency = time.time() - start

            self.metrics["total_forwarded_requests"] += 1

            log_network_event(
                f"[FORWARD] {source_node}->{destination_node} | "
                f"Path={path} | Latency={latency:.4f}s"
            )

            return response.json()

        except Exception as e:

            self.metrics["failed_requests"] += 1
            log_network_event(f"[ERROR] {str(e)}")

            return {"error": str(e)}

    # =================================================
    # LINK DEGRADATION SIMULATION
    # =================================================
    def simulate_link_degradation(self, node_a, node_b, probability=0.2):

        link = self.link_manager.get_link(node_a, node_b)

        if not link:
            return {"status": "LINK_NOT_FOUND"}

        if random.random() < probability:
            self.link_manager.degrade_link(node_a, node_b, link["rate"] * 0.5)
            return {"status": "DEGRADED"}

        self.link_manager.restore_link(node_a, node_b)
        return {"status": "AVAILABLE"}

    # =================================================
    # EXHAUSTION-AWARE REROUTING
    # =================================================
    def reroute_if_exhausted(self, source_node, token, endpoint):

        nodes = self.registry.list_nodes()

        for node_id in nodes:
            response = self.forward_request(
                source_node,
                node_id,
                token,
                endpoint
            )

            if response.get("status") == "KEY_AVAILABLE":
                self.metrics["rerouted_due_to_exhaustion"] += 1
                return response

        return {"error": "ALL_NODES_EXHAUSTED"}

    # =================================================
    # METRICS EXPORT
    # =================================================
    def get_metrics(self):

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.metrics
        }