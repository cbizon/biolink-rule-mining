"""Tests for node_tracker module."""

from prepare.node_tracker import NodeTracker


def test_node_tracker_marks_edges():
    tracker = NodeTracker()

    edge1 = {"subject": "Gene:1", "object": "Disease:1"}
    edge2 = {"subject": "Gene:2", "object": "Disease:1"}

    tracker.mark_edge(edge1)
    tracker.mark_edge(edge2)

    assert tracker.is_used("Gene:1")
    assert tracker.is_used("Gene:2")
    assert tracker.is_used("Disease:1")
    assert not tracker.is_used("Gene:3")


def test_node_tracker_count():
    tracker = NodeTracker()

    tracker.mark_edge({"subject": "A", "object": "B"})
    tracker.mark_edge({"subject": "C", "object": "D"})
    tracker.mark_edge({"subject": "A", "object": "C"})  # A and C already seen

    assert tracker.get_used_count() == 4  # A, B, C, D
