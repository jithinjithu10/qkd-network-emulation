from models import LinkStatus


class LinkManager:

    def __init__(self):
        self.links = {}

    def update_link(self, node_a, node_b, rate, status):

        key = f"{node_a}-{node_b}"

        self.links[key] = {
            "rate": rate,
            "status": status
        }

        return {"status": "LINK_UPDATED"}

    def get_link_for_node(self, node_id):

        for key, value in self.links.items():
            if node_id in key:
                return value

        return None

    def list_links(self):
        return self.links
