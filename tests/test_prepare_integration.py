"""Integration tests for graph preparation."""

import json
import tempfile
from pathlib import Path

from prepare import prepare_graph


def test_prepare_graph_filters_predicates(tmp_path):
    """Test that specified predicates are filtered out."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    # Create test data
    edges = [
        {"id": "e1", "subject": "A", "predicate": "biolink:related_to", "object": "B"},
        {"id": "e2", "subject": "C", "predicate": "biolink:subclass_of", "object": "D"},
        {"id": "e3", "subject": "E", "predicate": "biolink:affects", "object": "F"},
    ]

    nodes = [
        {"id": "A", "name": "Node A"},
        {"id": "B", "name": "Node B"},
        {"id": "C", "name": "Node C"},
        {"id": "D", "name": "Node D"},
        {"id": "E", "name": "Node E"},
        {"id": "F", "name": "Node F"},
    ]

    with open(input_dir / "edges.jsonl", "w") as f:
        for edge in edges:
            f.write(json.dumps(edge) + "\n")

    with open(input_dir / "nodes.jsonl", "w") as f:
        for node in nodes:
            f.write(json.dumps(node) + "\n")

    # Run preparation
    prepare_graph(input_dir, output_dir, filter_predicates=["biolink:subclass_of"])

    # Read output edges
    output_edges = []
    with open(output_dir / "edges.jsonl") as f:
        for line in f:
            output_edges.append(json.loads(line))

    # Check that subclass_of edge is filtered
    predicates = [e["predicate"] for e in output_edges]
    assert "biolink:subclass_of" not in predicates

    # Check that other edges are present (possibly with redundant versions)
    subjects = [e["subject"] for e in output_edges]
    assert "A" in subjects
    assert "E" in subjects


def test_prepare_graph_removes_orphaned_nodes(tmp_path):
    """Test that orphaned nodes are removed."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    # Create test data where C and D will be orphaned after filtering
    edges = [
        {"id": "e1", "subject": "A", "predicate": "biolink:related_to", "object": "B"},
        {"id": "e2", "subject": "C", "predicate": "biolink:subclass_of", "object": "D"},
    ]

    nodes = [
        {"id": "A", "name": "Node A"},
        {"id": "B", "name": "Node B"},
        {"id": "C", "name": "Node C"},
        {"id": "D", "name": "Node D"},
    ]

    with open(input_dir / "edges.jsonl", "w") as f:
        for edge in edges:
            f.write(json.dumps(edge) + "\n")

    with open(input_dir / "nodes.jsonl", "w") as f:
        for node in nodes:
            f.write(json.dumps(node) + "\n")

    # Run preparation
    prepare_graph(input_dir, output_dir)

    # Read output nodes
    output_nodes = []
    with open(output_dir / "nodes.jsonl") as f:
        for line in f:
            output_nodes.append(json.loads(line))

    node_ids = [n["id"] for n in output_nodes]

    # A and B should be present (used in remaining edge)
    assert "A" in node_ids
    assert "B" in node_ids

    # C and D should be removed (orphaned)
    assert "C" not in node_ids
    assert "D" not in node_ids


def test_prepare_graph_generates_redundant_edges(tmp_path):
    """Test that redundant edges are generated."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    # Create edge with qualifiers
    edges = [
        {
            "id": "e1",
            "subject": "Gene:1",
            "predicate": "biolink:affects",
            "object": "Disease:1",
            "object_direction_qualifier": "increased",
            "object_aspect_qualifier": "activity",
        }
    ]

    nodes = [
        {"id": "Gene:1", "name": "Gene 1"},
        {"id": "Disease:1", "name": "Disease 1"},
    ]

    with open(input_dir / "edges.jsonl", "w") as f:
        for edge in edges:
            f.write(json.dumps(edge) + "\n")

    with open(input_dir / "nodes.jsonl", "w") as f:
        for node in nodes:
            f.write(json.dumps(node) + "\n")

    # Run preparation
    prepare_graph(input_dir, output_dir)

    # Read output edges
    output_edges = []
    with open(output_dir / "edges.jsonl") as f:
        for line in f:
            output_edges.append(json.loads(line))

    # Should have multiple edges
    assert len(output_edges) > 1

    # Should have edge with encoded qualifiers
    encoded_edges = [e for e in output_edges if "increased_activity" in e["predicate"]]
    assert len(encoded_edges) > 0

    # Should have plain predicate edge
    plain_edges = [e for e in output_edges if e["predicate"] == "biolink:affects"]
    assert len(plain_edges) > 0

    # All edges should have no qualifier fields
    for edge in output_edges:
        assert "object_direction_qualifier" not in edge
        assert "object_aspect_qualifier" not in edge
