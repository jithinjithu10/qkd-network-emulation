"""
link_manager.py
---------------
Maintains logical QKD links between nodes.

Abstracts:
- Key rate
- Availability
"""

class LinkManager:

    def __init__(self):
        self.links = {}

    def update_link(self, node_a, node_b, rate, availability):
        key = f"{node_a}-{node_b}"

        self.links[key] = {
            "rate": rate,
            "availability": availability
        }

        return {"status": "LINK_UPDATED"}

    def list_links(self):
        return self.links
