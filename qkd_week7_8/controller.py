"""
controller.py
--------------
Central QKD Network Controller (Week 7)

Handles:
- Node registration
- Link abstraction
- Topology tracking
"""

from node_registry import NodeRegistry
from link_manager import LinkManager


class QKDController:

    def __init__(self):
        self.registry = NodeRegistry()
        self.link_manager = LinkManager()

    # -----------------------------------------
    # Register Node
    # -----------------------------------------
    def register_node(self, node_id, ip_address):
        return self.registry.register(node_id, ip_address)

    # -----------------------------------------
    # Get Topology
    # -----------------------------------------
    def get_topology(self):
        return {
            "registered_nodes": self.registry.list_nodes(),
            "links": self.link_manager.list_links()
        }

    # -----------------------------------------
    # Update Link Status
    # -----------------------------------------
    def update_link(self, node_a, node_b, rate, availability):
        return self.link_manager.update_link(node_a, node_b, rate, availability)
