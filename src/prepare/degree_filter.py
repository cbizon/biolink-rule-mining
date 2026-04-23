"""Type-stratified degree filtering for hub nodes."""

import json
from collections import defaultdict
from pathlib import Path

from library import assign_node_type, build_compound_predicate


class NodeTypeMap:
    """Maps node IDs to their categories and names."""

    def __init__(self):
        self._node_to_type = {}
        self._node_to_name = {}

    def load_from_file(self, nodes_path: Path) -> int:
        """Load node types and names from nodes.jsonl file.

        Returns:
            Number of nodes loaded
        """
        count = 0
        with open(nodes_path) as f:
            for line in f:
                node = json.loads(line)
                category = node["category"]

                # Assign node to single type or pseudotype (e.g., Gene+Protein)
                if isinstance(category, list):
                    node_type = assign_node_type(category)
                else:
                    node_type = category

                self._node_to_type[node["id"]] = node_type
                self._node_to_name[node["id"]] = node.get("name", "")
                count += 1

                if count % 100000 == 0:
                    print(f"  Loaded {count:,} node types...")

        return count

    def get_type(self, node_id: str) -> str | None:
        """Get the category/type for a node ID."""
        return self._node_to_type.get(node_id)

    def get_name(self, node_id: str) -> str:
        """Get the name for a node ID."""
        return self._node_to_name.get(node_id, "")


class TypeStratifiedDegreeCounter:
    """Counts edges per (node, neighbor_type, predicate) triple."""

    def __init__(self, node_type_map: NodeTypeMap):
        self.node_type_map = node_type_map
        # Maps (node_id, neighbor_category, compound_predicate) -> count
        self._degree_counts = defaultdict(int)

    def count_edge(self, edge: dict) -> None:
        """Count an edge for both subject and object nodes."""
        subject_id = edge["subject"]
        object_id = edge["object"]

        subject_type = self.node_type_map.get_type(subject_id)
        object_type = self.node_type_map.get_type(object_id)

        # Extract qualifiers and build compound predicate
        direction = None
        aspect = None

        if "qualifiers" in edge:
            qualifiers = edge["qualifiers"]
            if isinstance(qualifiers, dict):
                direction = qualifiers.get("object_direction_qualifier")
                aspect = qualifiers.get("object_aspect_qualifier")

        if "object_direction_qualifier" in edge:
            direction = edge["object_direction_qualifier"]
        if "object_aspect_qualifier" in edge:
            aspect = edge["object_aspect_qualifier"]

        # Remove biolink: prefix from qualifiers if present
        if direction and ":" in direction:
            direction = direction.split(":")[-1]
        if aspect and ":" in aspect:
            aspect = aspect.split(":")[-1]

        # Build compound predicate (e.g., "affects--increased--activity")
        base_predicate = edge["predicate"]
        compound_predicate = build_compound_predicate(base_predicate, direction, aspect)

        # Count subject -> (object_type, predicate)
        if object_type:
            self._degree_counts[(subject_id, object_type, compound_predicate)] += 1

        # Count object -> (subject_type, predicate)
        if subject_type:
            self._degree_counts[(object_id, subject_type, compound_predicate)] += 1

    def get_hub_triples(self, max_degree: int) -> set[tuple[str, str, str]]:
        """Get (node_id, neighbor_type, predicate) triples exceeding threshold.

        Returns:
            Set of (node_id, neighbor_category, predicate) tuples that are hubs
        """
        return {
            (node_id, neighbor_type, predicate)
            for (node_id, neighbor_type, predicate), count in self._degree_counts.items()
            if count > max_degree
        }

    def get_all_counts(self) -> dict[tuple[str, str, str], int]:
        """Get all degree counts.

        Returns:
            Dict mapping (node_id, neighbor_category, predicate) -> count
        """
        return dict(self._degree_counts)


def should_filter_hub_edge(
    edge: dict,
    hub_triples: set[tuple[str, str, str]],
    node_type_map: NodeTypeMap,
) -> bool:
    """Check if edge should be filtered due to hub node.

    An edge is filtered if either:
    - (subject, object_type, predicate) is a hub triple, OR
    - (object, subject_type, predicate) is a hub triple
    """
    subject_id = edge["subject"]
    object_id = edge["object"]

    subject_type = node_type_map.get_type(subject_id)
    object_type = node_type_map.get_type(object_id)

    # Extract qualifiers and build compound predicate
    direction = None
    aspect = None

    if "qualifiers" in edge:
        qualifiers = edge["qualifiers"]
        if isinstance(qualifiers, dict):
            direction = qualifiers.get("object_direction_qualifier")
            aspect = qualifiers.get("object_aspect_qualifier")

    if "object_direction_qualifier" in edge:
        direction = edge["object_direction_qualifier"]
    if "object_aspect_qualifier" in edge:
        aspect = edge["object_aspect_qualifier"]

    # Remove biolink: prefix from qualifiers if present
    if direction and ":" in direction:
        direction = direction.split(":")[-1]
    if aspect and ":" in aspect:
        aspect = aspect.split(":")[-1]

    # Build compound predicate
    base_predicate = edge["predicate"]
    compound_predicate = build_compound_predicate(base_predicate, direction, aspect)

    # Check if subject is a hub to (object_type, predicate)
    if object_type and (subject_id, object_type, compound_predicate) in hub_triples:
        return True

    # Check if object is a hub to (subject_type, predicate)
    if subject_type and (object_id, subject_type, compound_predicate) in hub_triples:
        return True

    return False


def write_hub_report(
    hub_triples: set[tuple[str, str, str]],
    degree_counts: dict[tuple[str, str, str], int],
    node_type_map: NodeTypeMap,
    output_path: Path,
) -> None:
    """Write TSV report of filtered hub triples.

    Columns: node_id, node_name, node_category, neighbor_category, predicate, edge_count
    """
    with open(output_path, "w") as f:
        # Write header
        f.write("node_id\tnode_name\tnode_category\tneighbor_category\tpredicate\tedge_count\n")

        # Sort by edge count descending
        sorted_triples = sorted(
            hub_triples,
            key=lambda triple: degree_counts[triple],
            reverse=True,
        )

        for node_id, neighbor_type, predicate in sorted_triples:
            node_type = node_type_map.get_type(node_id)
            node_name = node_type_map.get_name(node_id)
            count = degree_counts[(node_id, neighbor_type, predicate)]
            f.write(f"{node_id}\t{node_name}\t{node_type}\t{neighbor_type}\t{predicate}\t{count}\n")
