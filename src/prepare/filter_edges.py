"""Filter and process edges, generating redundant variants."""

import json
from pathlib import Path
from typing import Iterator

from .node_tracker import NodeTracker
from .redundant_edges import RedundantEdgeGenerator


def should_filter_edge(edge: dict, filter_predicates: list[str]) -> bool:
    """Check if edge should be filtered out based on predicate."""
    return edge["predicate"] in filter_predicates


def process_edges(
    input_path: Path,
    output_path: Path,
    node_tracker: NodeTracker,
    filter_predicates: list[str],
) -> tuple[int, int, int]:
    """Process edges: filter, generate redundant edges, track nodes.

    Returns:
        Tuple of (edges_read, edges_filtered, edges_written)
    """
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

            # Generate redundant edges
            for redundant_edge in generator.generate_redundant_edges(edge):
                # Track nodes
                node_tracker.mark_edge(redundant_edge)

                # Write edge
                outfile.write(json.dumps(redundant_edge) + "\n")
                edges_written += 1

            # Progress indicator for large files
            if edges_read % 1000000 == 0:
                print(f"  Processed {edges_read:,} edges, written {edges_written:,}...")

    return edges_read, edges_filtered, edges_written
