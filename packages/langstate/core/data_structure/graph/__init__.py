"""
Common graph data structure interfaces.

This module provides base abstractions for directed graph structures,
including simple graphs (DAG) and hypergraphs (DAH).
"""

from .base import BaseGraph, BaseGraphEdge, BaseGraphNode

__all__ = [
    "BaseGraph",
    "BaseGraphEdge",
    "BaseGraphNode",
]
