"""
link_manager.py
---------------

QKD Logical Link Manager
Weeks 7–12 Full Implementation

Supports:
- Multi-node topology
- Bidirectional logical links
- Link rate abstraction
- Latency abstraction
- Degradation simulation
- Failure simulation
- Traffic metrics (Week 12)
- Capacity-aware routing
"""

from datetime import datetime, timezone
from models import LinkStatus
from config import DEFAULT_LINK_RATE


class LinkManager:

    def __init__(self):

        # Format:
        # {
        #   "A-B": {
        #       node_a,
        #       node_b,
        #       rate,
        #       latency,
        #       status,
        #       traffic_count,
        #       last_updated
        #   }
        # }

        self.links = {}

    # =================================================
    # CREATE / UPDATE LINK
    # =================================================
    def update_link(self, node_a, node_b, rate=None, status=None, latency=1):

        if not rate:
            rate = DEFAULT_LINK_RATE

        if not status:
            status = LinkStatus.AVAILABLE.value

        key = self._normalize_key(node_a, node_b)

        self.links[key] = {
            "node_a": node_a,
            "node_b": node_b,
            "rate": rate,
            "latency": latency,
            "status": status,
            "traffic_count": 0,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        return {"status": "LINK_UPDATED", "link": key}

    # =================================================
    # GET SPECIFIC LINK
    # =================================================
    def get_link(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)
        return self.links.get(key)

    # =================================================
    # GET ANY LINK FOR NODE (Controller Compatibility)
    # =================================================
    def get_link_for_node(self, node_id):

        for key, value in self.links.items():
            if value["node_a"] == node_id or value["node_b"] == node_id:
                return value

        return None

    # =================================================
    # GET ALL LINKS FOR NODE
    # =================================================
    def get_links_for_node(self, node_id):

        result = {}

        for key, value in self.links.items():
            if value["node_a"] == node_id or value["node_b"] == node_id:
                result[key] = value

        return result

    # =================================================
    # RECORD TRAFFIC (Week 12 Evaluation)
    # =================================================
    def record_traffic(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)

        if key in self.links:
            self.links[key]["traffic_count"] += 1
            return True

        return False

    # =================================================
    # DEGRADE LINK (Reduce Rate)
    # =================================================
    def degrade_link(self, node_a, node_b, new_rate):

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            return {"error": "LINK_NOT_FOUND"}

        self.links[key]["rate"] = new_rate
        self.links[key]["status"] = LinkStatus.DEGRADED.value
        self.links[key]["last_updated"] = datetime.now(timezone.utc).isoformat()

        return {"status": "LINK_DEGRADED", "new_rate": new_rate}

    # =================================================
    # FAIL LINK (Simulate Outage)
    # =================================================
    def fail_link(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            return {"error": "LINK_NOT_FOUND"}

        self.links[key]["status"] = LinkStatus.UNAVAILABLE.value
        self.links[key]["last_updated"] = datetime.now(timezone.utc).isoformat()

        return {"status": "LINK_FAILED"}

    # =================================================
    # RESTORE LINK
    # =================================================
    def restore_link(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            return {"error": "LINK_NOT_FOUND"}

        self.links[key]["status"] = LinkStatus.AVAILABLE.value
        self.links[key]["last_updated"] = datetime.now(timezone.utc).isoformat()

        return {"status": "LINK_RESTORED"}

    # =================================================
    # CAPACITY CHECK (Week 11 Stress Simulation)
    # =================================================
    def is_capacity_available(self, node_a, node_b, required_rate):

        link = self.get_link(node_a, node_b)

        if not link:
            return False

        if link["status"] != LinkStatus.AVAILABLE.value:
            return False

        return link["rate"] >= required_rate

    # =================================================
    # LIST ALL LINKS
    # =================================================
    def list_links(self):
        return self.links

    # =================================================
    # NORMALIZE KEY (Bidirectional)
    # Ensures A-B == B-A
    # =================================================
    def _normalize_key(self, node_a, node_b):

        if node_a < node_b:
            return f"{node_a}-{node_b}"
        else:
            return f"{node_b}-{node_a}"
