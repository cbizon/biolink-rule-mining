"""Track which nodes are used in the graph to identify orphans."""


class NodeTracker:
    """Track node usage to identify orphaned nodes after filtering."""

    def __init__(self):
        self.used_nodes = set()

    def mark_edge(self, edge: dict) -> None:
        """Mark subject and object nodes as used."""
        self.used_nodes.add(edge["subject"])
        self.used_nodes.add(edge["object"])

    def is_used(self, node_id: str) -> bool:
        """Check if a node is used in any edge."""
        return node_id in self.used_nodes

    def get_used_count(self) -> int:
        """Get count of used nodes."""
        return len(self.used_nodes)
