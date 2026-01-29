"""Tests for redundant_edges module."""

from prepare.redundant_edges import RedundantEdgeGenerator


def test_encode_qualifiers_both():
    gen = RedundantEdgeGenerator()

    predicate = gen.encode_qualifiers_in_predicate(
        "biolink:affects",
        "increased",
        "activity"
    )

    assert predicate == "biolink:affects_increased_activity"


def test_encode_qualifiers_direction_only():
    gen = RedundantEdgeGenerator()

    predicate = gen.encode_qualifiers_in_predicate(
        "biolink:affects",
        "increased",
        None
    )

    assert predicate == "biolink:affects_increased"


def test_encode_qualifiers_aspect_only():
    gen = RedundantEdgeGenerator()

    predicate = gen.encode_qualifiers_in_predicate(
        "biolink:affects",
        None,
        "activity"
    )

    assert predicate == "biolink:affects_activity"


def test_encode_qualifiers_none():
    gen = RedundantEdgeGenerator()

    predicate = gen.encode_qualifiers_in_predicate(
        "biolink:affects",
        None,
        None
    )

    assert predicate == "biolink:affects"


def test_encode_qualifiers_strips_namespace():
    gen = RedundantEdgeGenerator()

    predicate = gen.encode_qualifiers_in_predicate(
        "biolink:affects",
        "GO:0001234",
        "GOCC:0005678"
    )

    assert predicate == "biolink:affects_0001234_0005678"


def test_create_edge_variant_removes_qualifiers():
    gen = RedundantEdgeGenerator()

    original = {
        "subject": "Gene:1",
        "predicate": "biolink:affects",
        "object": "Disease:1",
        "qualifiers": {"object_direction_qualifier": "increased"},
        "object_direction_qualifier": "increased",
    }

    variant = gen.create_edge_variant(original, "biolink:affects", "increased", None)

    assert variant["predicate"] == "biolink:affects_increased"
    assert "qualifiers" not in variant
    assert "object_direction_qualifier" not in variant
    assert variant["subject"] == "Gene:1"
    assert variant["object"] == "Disease:1"


def test_generate_redundant_edges_no_qualifiers():
    gen = RedundantEdgeGenerator()

    edge = {
        "subject": "Gene:1",
        "predicate": "biolink:related_to",
        "object": "Disease:1",
    }

    redundant = list(gen.generate_redundant_edges(edge))

    # Should have at least original edge
    assert len(redundant) >= 1

    # First edge should be original
    assert redundant[0] == edge


def test_generate_redundant_edges_with_qualifiers():
    gen = RedundantEdgeGenerator()

    edge = {
        "subject": "Gene:1",
        "predicate": "biolink:affects",
        "object": "Disease:1",
        "object_direction_qualifier": "increased",
        "object_aspect_qualifier": "activity",
    }

    redundant = list(gen.generate_redundant_edges(edge))

    # Should have multiple edges
    assert len(redundant) > 1

    # Find edge with encoded qualifiers
    encoded_edges = [e for e in redundant if "increased_activity" in e["predicate"]]
    assert len(encoded_edges) > 0

    # Find edge with just predicate (no qualifiers)
    plain_edges = [e for e in redundant if e["predicate"] == "biolink:affects"]
    assert len(plain_edges) > 0

    # All edges should have no qualifier fields
    for e in redundant:
        assert "qualifiers" not in e
        assert "object_direction_qualifier" not in e
        assert "object_aspect_qualifier" not in e
