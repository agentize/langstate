from __future__ import annotations

"""
Directed Acyclic Hypergraph data structure.
"""

from .base import (
    BaseDirectedAcyclicHypergraph,
    BaseDirectedAcyclicHypergraphEdge,
    BaseDirectedAcyclicHypergraphNode,
)
from .dah import DirectedAcyclicHypergraph
from .schema import (
    DirectedAcyclicHypergraphEdge,
    DirectedAcyclicHypergraphNode,
)

__all__ = [
    # Base interfaces
    "BaseDirectedAcyclicHypergraph",
    "BaseDirectedAcyclicHypergraphEdge",
    "BaseDirectedAcyclicHypergraphNode",
    # Implementation
    "DirectedAcyclicHypergraph",
    # Schema classes
    "DirectedAcyclicHypergraphEdge",
    "DirectedAcyclicHypergraphNode",
]
