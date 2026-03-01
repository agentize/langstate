"""Unit tests for graph base abstract classes.

Verifies that BaseGraphEdge, BaseGraphNode, and BaseGraph
cannot be instantiated directly.
"""

import pytest

from core.data_structure.graph.base import BaseGraph, BaseGraphEdge, BaseGraphNode


class TestBaseGraphEdge:
    """Tests for BaseGraphEdge ABC."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseGraphEdge()  # type: ignore[abstract]


class TestBaseGraphNode:
    """Tests for BaseGraphNode ABC."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseGraphNode()  # type: ignore[abstract]


class TestBaseGraph:
    """Tests for BaseGraph ABC."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseGraph()  # type: ignore[abstract]
