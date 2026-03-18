"""
Research-Grade QKD Network Controller
DEBUG INSTRUMENTED VERSION
"""

import requests
import random
import time
from datetime import datetime
from collections import defaultdict, deque

from qkd_research_platform_v1.controller.node_registry import NodeRegistry
from qkd_research_platform_v1.controller.link_manager import LinkManager
from qkd_research_platform_v1.core.models import LinkStatus
from qkd_research_platform_v1.core.audit import log_network_event


class QKDController:

    def __init__(self):

        print("\n=== Initializing QKDController ===")

        self.registry = NodeRegistry()
        self.link_manager = LinkManager()

        self.graph = defaultdict(set)  # FIX: use set to avoid duplicates

        self.metrics = {
            "total_forwarded_requests": 0,
            "failed_requests": 0,
            "multi_hop_routes": 0,
            "degraded_routing_events": 0,
            "unavailable_link_blocks": 0,
            "rerouted_due_to_exhaustion": 0
        }

        print("Controller initialized successfully")


    # =================================================
    # NODE REGISTRATION
    # =================================================
    def register_node(self, node_id, ip_address):

        print(f"\nRegistering node: {node_id} ({ip_address})")

        response = self.registry.register(node_id, ip_address)

        log_network_event(f"[REGISTER] Node={node_id}")

        return response


    # =================================================
    # LINK UPDATE
    # =================================================
    def update_link(self, node_a, node_b, rate, status):

        print(f"\nUpdating link {node_a}<->{node_b}")
        print(f"Rate: {rate}, Status: {status}")

        self.link_manager.update_link(node_a, node_b, rate, status)

        # Avoid duplicates
        self.graph[node_a].add(node_b)
        self.graph[node_b].add(node_a)

        log_network_event(
            f"[LINK UPDATE] {node_a}<->{node_b} | Rate={rate} | Status={status}"
        )

        return {"status": "LINK_UPDATED"}


    # =================================================
    # TOPOLOGY VIEW
    # =================================================
    def get_topology(self):

        print("\nFetching topology")

        return {
            "nodes": self.registry.list_nodes(),
            "links": self.link_manager.list_links()
        }


    # =================================================
    # SHORTEST PATH (BFS)
    # =================================================
    def _find_path(self, source, destination):

        print(f"\nFinding path from {source} to {destination}")

        visited = set()
        queue = deque([(source, [source])])

        while queue:
            node, path = queue.popleft()

            if node == destination:
                print("Path found:", path)
                return path

            visited.add(node)

            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        print("No route found")
        return None


    # =================================================
    # LINK QUALITY CHECK
    # =================================================
    def _validate_path(self, path):

        print("Validating path:", path)

        for i in range(len(path) - 1):

            link = self.link_manager.get_link(path[i], path[i+1])

            if not link:
                print("Link not found:", path[i], path[i+1])
                return False, "LINK_NOT_FOUND"

            if link["status"] == LinkStatus.UNAVAILABLE.value:
                print("Link unavailable:", path[i], path[i+1])
                self.metrics["unavailable_link_blocks"] += 1
                return False, "LINK_UNAVAILABLE"

            if link["status"] == LinkStatus.DEGRADED.value:
                print("Link degraded:", path[i], path[i+1])
                self.metrics["degraded_routing_events"] += 1
                time.sleep(random.uniform(0.3, 0.8))

        return True, "VALID"


    # =================================================
    # FORWARD REQUEST
    # =================================================
    def forward_request(self, source_node, destination_node, token, endpoint, payload=None):

        print(f"\n=== FORWARD REQUEST ===")
        print(f"Source: {source_node}")
        print(f"Destination: {destination_node}")
        print(f"Endpoint: {endpoint}")

        if not self.registry.get_node(source_node):
            print("Source not found")
            self.metrics["failed_requests"] += 1
            return {"error": "SOURCE_NOT_FOUND"}

        if not self.registry.get_node(destination_node):
            print("Destination not found")
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
            print("Path validation failed:", reason)
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

            print("Forwarded successfully. Latency:", latency)

            self.metrics["total_forwarded_requests"] += 1

            log_network_event(
                f"[FORWARD] {source_node}->{destination_node} | "
                f"Path={path} | Latency={latency:.4f}s"
            )

            return response.json()

        except Exception as e:

            print("Forwarding error:", e)

            self.metrics["failed_requests"] += 1
            log_network_event(f"[ERROR] {str(e)}")

            return {"error": str(e)}


    # =================================================
    # METRICS EXPORT
    # =================================================
    def get_metrics(self):

        print("\nController Metrics Requested")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.metrics
        }