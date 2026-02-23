"""
link_manager.py
---------------

Research-Grade QKD Physical Link Manager
Quantum-Aware | Distance-Aware | Attack-Ready
Weeks 7–12 Advanced Physical Simulation
"""

import math
import random
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
        #       base_rate,
        #       effective_rate,
        #       latency_ms,
        #       distance_km,
        #       attenuation_db,
        #       qber,
        #       noise_probability,
        #       packet_loss_probability,
        #       status,
        #       traffic_count,
        #       last_updated
        #   }
        # }

        self.links = {}

    # =================================================
    # CREATE / UPDATE LINK (Physics-Aware)
    # =================================================
    def update_link(
        self,
        node_a,
        node_b,
        base_rate=None,
        latency_ms=5,
        distance_km=50,
        attenuation_db=0.2,
        status=None
    ):

        if not base_rate:
            base_rate = DEFAULT_LINK_RATE

        if not status:
            status = LinkStatus.AVAILABLE.value

        effective_rate = self._calculate_effective_rate(
            base_rate,
            distance_km,
            attenuation_db
        )

        qber = self._calculate_qber(distance_km)

        key = self._normalize_key(node_a, node_b)

        self.links[key] = {
            "node_a": node_a,
            "node_b": node_b,
            "base_rate": base_rate,
            "effective_rate": effective_rate,
            "latency_ms": latency_ms,
            "distance_km": distance_km,
            "attenuation_db": attenuation_db,
            "qber": qber,
            "noise_probability": random.uniform(0.0, 0.1),
            "packet_loss_probability": random.uniform(0.0, 0.05),
            "status": status,
            "traffic_count": 0,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        return {"status": "LINK_UPDATED", "link": key}

    # =================================================
    # PHYSICAL MODELS
    # =================================================
    def _calculate_effective_rate(self, base_rate, distance_km, attenuation_db):

        # Exponential attenuation model
        attenuation_factor = math.exp(-attenuation_db * distance_km / 100)
        return base_rate * attenuation_factor

    def _calculate_qber(self, distance_km):

        # Simple increasing QBER model
        base_qber = 0.01
        distance_factor = distance_km / 1000

        return min(0.15, base_qber + distance_factor)

    # =================================================
    # GET LINK
    # =================================================
    def get_link(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)
        return self.links.get(key)

    # =================================================
    # RECORD TRAFFIC
    # =================================================
    def record_traffic(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)

        if key in self.links:
            self.links[key]["traffic_count"] += 1
            return True

        return False

    # =================================================
    # DEGRADE LINK (Dynamic Physics Impact)
    # =================================================
    def degrade_link(self, node_a, node_b, severity=0.5):

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            return {"error": "LINK_NOT_FOUND"}

        link = self.links[key]

        link["effective_rate"] *= severity
        link["qber"] = min(0.2, link["qber"] + 0.05)
        link["status"] = LinkStatus.DEGRADED.value
        link["last_updated"] = datetime.now(timezone.utc).isoformat()

        return {"status": "LINK_DEGRADED"}

    # =================================================
    # ATTACK SIMULATION (Novel)
    # =================================================
    def inject_eavesdropping(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            return {"error": "LINK_NOT_FOUND"}

        link = self.links[key]

        link["qber"] += 0.1
        link["noise_probability"] += 0.1
        link["effective_rate"] *= 0.7
        link["status"] = LinkStatus.DEGRADED.value

        return {"status": "EAVESDROPPING_SIMULATED"}

    # =================================================
    # FAIL LINK
    # =================================================
    def fail_link(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            return {"error": "LINK_NOT_FOUND"}

        self.links[key]["status"] = LinkStatus.UNAVAILABLE.value
        return {"status": "LINK_FAILED"}

    # =================================================
    # RESTORE LINK
    # =================================================
    def restore_link(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            return {"error": "LINK_NOT_FOUND"}

        link = self.links[key]

        link["effective_rate"] = self._calculate_effective_rate(
            link["base_rate"],
            link["distance_km"],
            link["attenuation_db"]
        )

        link["qber"] = self._calculate_qber(link["distance_km"])
        link["status"] = LinkStatus.AVAILABLE.value

        return {"status": "LINK_RESTORED"}

    # =================================================
    # CAPACITY CHECK
    # =================================================
    def is_capacity_available(self, node_a, node_b, required_rate):

        link = self.get_link(node_a, node_b)

        if not link:
            return False

        if link["status"] != LinkStatus.AVAILABLE.value:
            return False

        return link["effective_rate"] >= required_rate

    # =================================================
    # LIST LINKS
    # =================================================
    def list_links(self):
        return self.links

    # =================================================
    # NORMALIZE KEY
    # =================================================
    def _normalize_key(self, node_a, node_b):

        if node_a < node_b:
            return f"{node_a}-{node_b}"
        else:
            return f"{node_b}-{node_a}"