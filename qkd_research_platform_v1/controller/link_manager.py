"""
Research-Grade QKD Physical Link Manager
DEBUG INSTRUMENTED VERSION
"""

import math
import random
from datetime import datetime, timezone

from qkd_research_platform_v1.core.models import LinkStatus
from qkd_research_platform_v1.config import DEFAULT_LINK_RATE


class LinkManager:

    def __init__(self):

        print("\n=== Initializing LinkManager ===")

        self.links = {}

        print("LinkManager initialized")


    # =================================================
    # CREATE / UPDATE LINK
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

        print(f"\nUpdating physical link {node_a} <-> {node_b}")

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

        print(f"Base rate: {base_rate}")
        print(f"Effective rate: {effective_rate}")
        print(f"Distance: {distance_km} km")
        print(f"QBER: {qber}")

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

        attenuation_factor = math.exp(-attenuation_db * distance_km / 100)

        rate = base_rate * attenuation_factor

        print(f"Calculated attenuation factor: {attenuation_factor}")
        print(f"Effective rate computed: {rate}")

        return rate


    def _calculate_qber(self, distance_km):

        base_qber = 0.01
        distance_factor = distance_km / 1000

        qber = min(0.15, base_qber + distance_factor)

        print(f"Calculated QBER: {qber}")

        return qber


    # =================================================
    # GET LINK
    # =================================================
    def get_link(self, node_a, node_b):

        key = self._normalize_key(node_a, node_b)

        link = self.links.get(key)

        if not link:
            print(f"Link {key} not found")

        return link


    # =================================================
    # DEGRADE LINK
    # =================================================
    def degrade_link(self, node_a, node_b, severity=0.5):

        print(f"\nDegrading link {node_a}-{node_b}")

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            print("Link not found")
            return {"error": "LINK_NOT_FOUND"}

        link = self.links[key]

        link["effective_rate"] *= severity
        link["qber"] = min(0.2, link["qber"] + 0.05)
        link["status"] = LinkStatus.DEGRADED.value
        link["last_updated"] = datetime.now(timezone.utc).isoformat()

        print("Link degraded. New effective rate:", link["effective_rate"])
        print("New QBER:", link["qber"])

        return {"status": "LINK_DEGRADED"}


    # =================================================
    # ATTACK SIMULATION
    # =================================================
    def inject_eavesdropping(self, node_a, node_b):

        print(f"\nInjecting eavesdropping on {node_a}-{node_b}")

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            print("Link not found")
            return {"error": "LINK_NOT_FOUND"}

        link = self.links[key]

        link["qber"] += 0.1
        link["noise_probability"] += 0.1
        link["effective_rate"] *= 0.7
        link["status"] = LinkStatus.DEGRADED.value

        print("Eavesdropping simulated")
        print("New QBER:", link["qber"])
        print("New effective rate:", link["effective_rate"])

        return {"status": "EAVESDROPPING_SIMULATED"}


    # =================================================
    # FAIL LINK
    # =================================================
    def fail_link(self, node_a, node_b):

        print(f"\nFailing link {node_a}-{node_b}")

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            print("Link not found")
            return {"error": "LINK_NOT_FOUND"}

        self.links[key]["status"] = LinkStatus.UNAVAILABLE.value

        return {"status": "LINK_FAILED"}


    # =================================================
    # RESTORE LINK
    # =================================================
    def restore_link(self, node_a, node_b):

        print(f"\nRestoring link {node_a}-{node_b}")

        key = self._normalize_key(node_a, node_b)

        if key not in self.links:
            print("Link not found")
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

        print(f"\nChecking capacity {node_a}-{node_b}")

        link = self.get_link(node_a, node_b)

        if not link:
            return False

        if link["status"] != LinkStatus.AVAILABLE.value:
            print("Link not available")
            return False

        print("Effective rate:", link["effective_rate"])
        print("Required rate:", required_rate)

        return link["effective_rate"] >= required_rate


    # =================================================
    # LIST LINKS
    # =================================================
    def list_links(self):

        print("Listing all links")

        return self.links


    # =================================================
    # NORMALIZE KEY
    # =================================================
    def _normalize_key(self, node_a, node_b):

        if node_a < node_b:
            return f"{node_a}-{node_b}"
        else:
            return f"{node_b}-{node_a}"