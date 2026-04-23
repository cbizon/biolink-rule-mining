"""Tests for type-stratified degree filtering."""

from pathlib import Path
import tempfile
import json

from prepare.degree_filter import (
    NodeTypeMap,
    TypeStratifiedDegreeCounter,
    should_filter_hub_edge,
)


def test_node_type_map():
    """Test loading node types from file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        # Test both list and string categories
        # Gene is most specific
        f.write(json.dumps({"id": "N1", "name": "BRCA1", "category": ["biolink:Gene", "biolink:NamedThing"]}) + "\n")
        f.write(json.dumps({"id": "N2", "name": "Diabetes", "category": "biolink:Disease"}) + "\n")
        # SmallMolecule is most specific
        f.write(json.dumps({"id": "N3", "name": "Aspirin", "category": ["biolink:SmallMolecule", "biolink:ChemicalEntity"]}) + "\n")
        # Gene+Protein pseudotype
        f.write(json.dumps({"id": "N4", "name": "TP53", "category": ["biolink:Gene", "biolink:Protein"]}) + "\n")
        nodes_path = Path(f.name)

    try:
        node_map = NodeTypeMap()
        count = node_map.load_from_file(nodes_path)

        assert count == 4
        # Should get most specific type or pseudotype
        assert node_map.get_type("N1") == "Gene"
        assert node_map.get_type("N2") == "biolink:Disease"
        assert node_map.get_type("N3") == "SmallMolecule"
        assert node_map.get_type("N4") == "Gene+Protein"  # Pseudotype
        assert node_map.get_type("N5") is None

        # Check names
        assert node_map.get_name("N1") == "BRCA1"
        assert node_map.get_name("N2") == "Diabetes"
        assert node_map.get_name("N4") == "TP53"
    finally:
        nodes_path.unlink()


def test_degree_counter():
    """Test counting degrees per (node, neighbor_type, predicate) triple."""
    node_map = NodeTypeMap()
    node_map._node_to_type = {
        "G1": "biolink:Gene",
        "G2": "biolink:Gene",
        "D1": "biolink:Disease",
        "D2": "biolink:Disease",
        "D3": "biolink:Disease",
    }

    counter = TypeStratifiedDegreeCounter(node_map)

    # G1 connects to 3 diseases with "associated_with"
    counter.count_edge({"subject": "G1", "object": "D1", "predicate": "biolink:associated_with"})
    counter.count_edge({"subject": "G1", "object": "D2", "predicate": "biolink:associated_with"})
    counter.count_edge({"subject": "G1", "object": "D3", "predicate": "biolink:associated_with"})

    # G1 connects to 1 disease with "causes" (different predicate)
    counter.count_edge({"subject": "G1", "object": "D1", "predicate": "biolink:causes"})

    # G2 connects to 1 disease
    counter.count_edge({"subject": "G2", "object": "D1", "predicate": "biolink:associated_with"})

    counts = counter.get_all_counts()

    # G1 -> (Disease, associated_with) should have count 3
    assert counts[("G1", "biolink:Disease", "biolink:associated_with")] == 3
    # G1 -> (Disease, causes) should have count 1
    assert counts[("G1", "biolink:Disease", "biolink:causes")] == 1
    # G2 -> (Disease, associated_with) should have count 1
    assert counts[("G2", "biolink:Disease", "biolink:associated_with")] == 1

    # D1 -> (Gene, associated_with) should have count 2 (from G1 and G2)
    assert counts[("D1", "biolink:Gene", "biolink:associated_with")] == 2
    # D1 -> (Gene, causes) should have count 1 (from G1)
    assert counts[("D1", "biolink:Gene", "biolink:causes")] == 1


def test_get_hub_triples():
    """Test identifying hub triples above threshold."""
    node_map = NodeTypeMap()
    node_map._node_to_type = {
        "G1": "biolink:Gene",
        "G2": "biolink:Gene",
        "D1": "biolink:Disease",
        "D2": "biolink:Disease",
        "D3": "biolink:Disease",
    }

    counter = TypeStratifiedDegreeCounter(node_map)

    # G1 connects to 3 diseases with predicate "p"
    for d in ["D1", "D2", "D3"]:
        counter.count_edge({"subject": "G1", "object": d, "predicate": "p"})

    # G1 connects to 1 disease with predicate "q"
    counter.count_edge({"subject": "G1", "object": "D1", "predicate": "q"})

    # G2 connects to 1 disease
    counter.count_edge({"subject": "G2", "object": "D1", "predicate": "p"})

    # With threshold 2, G1 -> (Disease, p) is a hub, but G1 -> (Disease, q) is not
    hub_triples = counter.get_hub_triples(max_degree=2)
    assert ("G1", "biolink:Disease", "p") in hub_triples
    assert ("G1", "biolink:Disease", "q") not in hub_triples
    assert ("G2", "biolink:Disease", "p") not in hub_triples


def test_should_filter_hub_edge():
    """Test filtering edges based on hub triples."""
    node_map = NodeTypeMap()
    node_map._node_to_type = {
        "G1": "biolink:Gene",
        "G2": "biolink:Gene",
        "D1": "biolink:Disease",
    }

    # G1 -> (Disease, p) is a hub triple
    hub_triples = {("G1", "biolink:Disease", "p")}

    # Edge with G1 as subject, Disease as object, predicate p should be filtered
    edge1 = {"subject": "G1", "object": "D1", "predicate": "p"}
    assert should_filter_hub_edge(edge1, hub_triples, node_map) is True

    # Edge with G1 as subject, Disease as object, but different predicate should NOT be filtered
    edge2 = {"subject": "G1", "object": "D1", "predicate": "q"}
    assert should_filter_hub_edge(edge2, hub_triples, node_map) is False

    # Edge with G2 as subject, Disease as object should NOT be filtered
    edge3 = {"subject": "G2", "object": "D1", "predicate": "p"}
    assert should_filter_hub_edge(edge3, hub_triples, node_map) is False

    # Edge in reverse (D1 -> G1) with predicate p should also be filtered (bidirectional)
    edge4 = {"subject": "D1", "object": "G1", "predicate": "p"}
    assert should_filter_hub_edge(edge4, hub_triples, node_map) is True


def test_compound_predicates_with_qualifiers():
    """Test that qualifiers are properly encoded in compound predicates."""
    node_map = NodeTypeMap()
    node_map._node_to_type = {
        "C1": "biolink:SmallMolecule",
        "G1": "biolink:Gene",
        "G2": "biolink:Gene",
    }

    counter = TypeStratifiedDegreeCounter(node_map)

    # Same predicate but with different qualifiers should be counted separately
    counter.count_edge({
        "subject": "C1",
        "object": "G1",
        "predicate": "biolink:affects",
        "object_direction_qualifier": "biolink:increased",
        "object_aspect_qualifier": "biolink:activity"
    })

    counter.count_edge({
        "subject": "C1",
        "object": "G2",
        "predicate": "biolink:affects",
        "object_direction_qualifier": "biolink:decreased",
        "object_aspect_qualifier": "biolink:activity"
    })

    counts = counter.get_all_counts()

    # Should have separate counts for different compound predicates
    assert counts[("C1", "biolink:Gene", "biolink:affects--increased--activity")] == 1
    assert counts[("C1", "biolink:Gene", "biolink:affects--decreased--activity")] == 1

    # Hub filtering should be predicate-specific
    hub_triples = counter.get_hub_triples(max_degree=1)
    # Neither should be a hub (both have count 1, threshold is > 1)
    assert len(hub_triples) == 0
