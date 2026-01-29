"""Filter and process edges, generating redundant variants."""

import json
from pathlib import Path
from typing import Iterator

from .node_tracker import NodeTracker
from .redundant_edges import RedundantEdgeGenerator


def should_filter_edge(edge: dict, filter_predicates: list[str]) -> bool:
    """Check if edge should be filtered out based on predicate."""
    return edge["predicate"] in filter_predicates


def encode_qualifiers_simple(edge: dict) -> dict:
    """Encode qualifiers into predicate name, removing qualifier fields.

    Returns a single edge with qualifiers encoded in the predicate name.
    Does NOT generate redundant variants.
    """
    # Extract qualifiers
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

    # Build new predicate name with encoded qualifiers
    parts = [edge["predicate"]]

    if direction:
        direction_val = direction.split(":")[-1] if ":" in direction else direction
        parts.append(direction_val)

    if aspect:
        aspect_val = aspect.split(":")[-1] if ":" in aspect else aspect
        parts.append(aspect_val)

    # Create new edge
    new_edge = edge.copy()
    new_edge["predicate"] = "_".join(parts)

    # Remove qualifier fields
    if "qualifiers" in new_edge:
        del new_edge["qualifiers"]
    if "object_direction_qualifier" in new_edge:
        del new_edge["object_direction_qualifier"]
    if "object_aspect_qualifier" in new_edge:
        del new_edge["object_aspect_qualifier"]
    if "qualified_predicate" in new_edge:
        del new_edge["qualified_predicate"]

    return new_edge


def process_edges(
    input_path: Path,
    output_path: Path,
    node_tracker: NodeTracker,
    filter_predicates: list[str],
    generate_redundant: bool = True,
) -> tuple[int, int, int]:
    """Process edges: filter, optionally generate redundant edges, track nodes.

    Args:
        input_path: Path to input edges.jsonl
        output_path: Path to output edges.jsonl
        node_tracker: NodeTracker to record node usage
        filter_predicates: List of predicates to filter out
        generate_redundant: If True, generate redundant edges (ancestors, qualifier permutations).
                           If False, only encode qualifiers into predicate names.

    Returns:
        Tuple of (edges_read, edges_filtered, edges_written)
    """
    if generate_redundant:
        generator = RedundantEdgeGenerator()

    edges_read = 0
    edges_filtered = 0
    edges_written = 0

    with open(input_path) as infile, open(output_path, "w") as outfile:
        for line in infile:
            edges_read += 1

            edge = json.loads(line)

            # Filter edge if needed
            if should_filter_edge(edge, filter_predicates):
                edges_filtered += 1
                continue

            if generate_redundant:
                # Generate redundant edges (old behavior)
                for redundant_edge in generator.generate_redundant_edges(edge):
                    node_tracker.mark_edge(redundant_edge)
                    outfile.write(json.dumps(redundant_edge) + "\n")
                    edges_written += 1
            else:
                # Simple mode: just encode qualifiers, no redundant edges
                processed_edge = encode_qualifiers_simple(edge)
                node_tracker.mark_edge(processed_edge)
                outfile.write(json.dumps(processed_edge) + "\n")
                edges_written += 1

            # Progress indicator for large files
            if edges_read % 1000000 == 0:
                print(f"  Processed {edges_read:,} edges, written {edges_written:,}...")

    return edges_read, edges_filtered, edges_written
