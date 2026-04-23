"""Main graph preparation orchestration."""

import json
from pathlib import Path

from .filter_edges import process_edges, process_edges_with_hub_filter, count_degrees
from .node_tracker import NodeTracker
from .degree_filter import NodeTypeMap, TypeStratifiedDegreeCounter, write_hub_report


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
    generate_redundant: bool = True,
    max_degree_per_type: int | None = None,
) -> None:
    """Prepare graph by filtering and optionally augmenting.

    Args:
        input_dir: Directory containing nodes.jsonl and edges.jsonl
        output_dir: Directory to write filtered/augmented graph
        filter_predicates: List of predicates to filter out (default: ["biolink:subclass_of"])
        generate_redundant: If True, generate redundant edges (ancestors, qualifier permutations).
                           If False, only encode qualifiers into predicate names.
        max_degree_per_type: If set, filter edges from nodes with >N edges to any specific node type
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
    print(f"  Generate redundant edges: {generate_redundant}")
    print(f"  Max degree per type: {max_degree_per_type if max_degree_per_type else 'None (disabled)'}")
    print()

    # If type-stratified filtering is enabled, use multi-pass pipeline
    if max_degree_per_type is not None:
        _prepare_graph_with_degree_filter(
            input_edges,
            input_nodes,
            output_edges,
            output_nodes,
            output_dir,
            filter_predicates,
            generate_redundant,
            max_degree_per_type,
        )
    else:
        # Original single-pass pipeline
        _prepare_graph_simple(
            input_edges,
            input_nodes,
            output_edges,
            output_nodes,
            filter_predicates,
            generate_redundant,
        )

    print("Graph preparation complete!")


def _prepare_graph_simple(
    input_edges: Path,
    input_nodes: Path,
    output_edges: Path,
    output_nodes: Path,
    filter_predicates: list[str],
    generate_redundant: bool,
) -> None:
    """Original simple pipeline without degree filtering."""
    # Pass 1: Process edges
    print("Pass 1: Processing edges...")
    node_tracker = NodeTracker()
    edges_read, edges_filtered, edges_written = process_edges(
        input_edges,
        output_edges,
        node_tracker,
        filter_predicates,
        generate_redundant,
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


def _prepare_graph_with_degree_filter(
    input_edges: Path,
    input_nodes: Path,
    output_edges: Path,
    output_nodes: Path,
    output_dir: Path,
    filter_predicates: list[str],
    generate_redundant: bool,
    max_degree_per_type: int,
) -> None:
    """Multi-pass pipeline with type-stratified degree filtering."""
    # Pass 1: Load node types
    print("Pass 1: Loading node types...")
    node_type_map = NodeTypeMap()
    nodes_loaded = node_type_map.load_from_file(input_nodes)
    print(f"  Node types loaded: {nodes_loaded:,}")
    print()

    # Pass 2: Count type-stratified degrees
    print("Pass 2: Counting type-stratified degrees...")
    degree_counter = TypeStratifiedDegreeCounter(node_type_map)
    edges_read, edges_filtered = count_degrees(
        input_edges,
        degree_counter,
        filter_predicates,
    )
    print(f"  Edges read: {edges_read:,}")
    print(f"  Edges filtered (predicates): {edges_filtered:,}")
    print()

    # Pass 3: Identify hub triples
    print("Pass 3: Identifying hub nodes...")
    hub_triples = degree_counter.get_hub_triples(max_degree_per_type)
    print(f"  Hub (node, type, predicate) triples found: {len(hub_triples):,}")

    if hub_triples:
        # Write hub report
        hub_report_path = output_dir / "hub_nodes_filtered.tsv"
        write_hub_report(
            hub_triples,
            degree_counter.get_all_counts(),
            node_type_map,
            hub_report_path,
        )
        print(f"  Hub report written to: {hub_report_path}")
    print()

    # Pass 4: Process edges with hub filtering
    print("Pass 4: Processing edges with hub filter...")
    node_tracker = NodeTracker()
    edges_read, edges_filtered_pred, edges_filtered_hub, edges_written = (
        process_edges_with_hub_filter(
            input_edges,
            output_edges,
            node_tracker,
            filter_predicates,
            generate_redundant,
            hub_triples,
            node_type_map,
        )
    )
    print(f"  Edges read: {edges_read:,}")
    print(f"  Edges filtered (predicates): {edges_filtered_pred:,}")
    print(f"  Edges filtered (hub nodes): {edges_filtered_hub:,}")
    print(f"  Edges written: {edges_written:,}")
    print(f"  Nodes tracked: {node_tracker.get_used_count():,}")
    print()

    # Pass 5: Process nodes
    print("Pass 5: Processing nodes...")
    nodes_read, nodes_written = process_nodes(
        input_nodes,
        output_nodes,
        node_tracker,
    )
    print(f"  Nodes read: {nodes_read:,}")
    print(f"  Nodes written: {nodes_written:,}")
    print(f"  Nodes orphaned: {nodes_read - nodes_written:,}")
    print()
