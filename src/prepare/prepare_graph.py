"""Main graph preparation orchestration."""

import json
from pathlib import Path

from .filter_edges import process_edges
from .node_tracker import NodeTracker


def process_nodes(
    input_path: Path,
    output_path: Path,
    node_tracker: NodeTracker,
) -> tuple[int, int]:
    """Process nodes: filter out orphaned nodes.

    Returns:
        Tuple of (nodes_read, nodes_written)
    """
    nodes_read = 0
    nodes_written = 0

    with open(input_path) as infile, open(output_path, "w") as outfile:
        for line in infile:
            nodes_read += 1

            node = json.loads(line)

            # Only write node if it's used in edges
            if node_tracker.is_used(node["id"]):
                outfile.write(line)
                nodes_written += 1

            # Progress indicator
            if nodes_read % 100000 == 0:
                print(f"  Processed {nodes_read:,} nodes, written {nodes_written:,}...")

    return nodes_read, nodes_written


def prepare_graph(
    input_dir: Path,
    output_dir: Path,
    filter_predicates: list[str] | None = None,
) -> None:
    """Prepare graph by filtering and augmenting.

    Args:
        input_dir: Directory containing nodes.jsonl and edges.jsonl
        output_dir: Directory to write filtered/augmented graph
        filter_predicates: List of predicates to filter out (default: ["biolink:subclass_of"])
    """
    if filter_predicates is None:
        filter_predicates = ["biolink:subclass_of"]

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate input files exist
    input_edges = input_dir / "edges.jsonl"
    input_nodes = input_dir / "nodes.jsonl"

    if not input_edges.exists():
        raise FileNotFoundError(f"Input edges file not found: {input_edges}")
    if not input_nodes.exists():
        raise FileNotFoundError(f"Input nodes file not found: {input_nodes}")

    output_edges = output_dir / "edges.jsonl"
    output_nodes = output_dir / "nodes.jsonl"

    print(f"Preparing graph:")
    print(f"  Input:  {input_dir}")
    print(f"  Output: {output_dir}")
    print(f"  Filtering predicates: {filter_predicates}")
    print()

    # Pass 1: Process edges
    print("Pass 1: Processing edges...")
    node_tracker = NodeTracker()
    edges_read, edges_filtered, edges_written = process_edges(
        input_edges,
        output_edges,
        node_tracker,
        filter_predicates,
    )

    print(f"  Edges read: {edges_read:,}")
    print(f"  Edges filtered: {edges_filtered:,}")
    print(f"  Edges written: {edges_written:,}")
    print(f"  Nodes tracked: {node_tracker.get_used_count():,}")
    print()

    # Pass 2: Process nodes
    print("Pass 2: Processing nodes...")
    nodes_read, nodes_written = process_nodes(
        input_nodes,
        output_nodes,
        node_tracker,
    )

    print(f"  Nodes read: {nodes_read:,}")
    print(f"  Nodes written: {nodes_written:,}")
    print(f"  Nodes orphaned: {nodes_read - nodes_written:,}")
    print()

    print("Graph preparation complete!")
