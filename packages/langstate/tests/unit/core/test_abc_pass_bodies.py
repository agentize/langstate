"""Tests for abstract-method ``pass`` bodies.

Each concrete subclass below calls ``super().method()`` so that the ``pass``
statement inside every ``@abstractmethod`` is actually executed, giving
us coverage for those lines.
"""

# pyright: reportPrivateUsage=false, reportReturnType=false

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Set, Tuple

import pytest

# ═══════════════════════════════════════════════════════════════════
# graph/base.py — BaseGraphEdge, BaseGraphNode, BaseGraph
# ═══════════════════════════════════════════════════════════════════

from core.data_structure.graph.base import BaseGraph, BaseGraphEdge, BaseGraphNode


class _ConcreteEdge(BaseGraphEdge[str, str]):
    @property
    def sources(self) -> Set[BaseGraphNode[str, str]]:
        return super().sources  # type: ignore[return-value]

    @property
    def metadata(self) -> Optional[str]:
        return super().metadata  # type: ignore[return-value]

    def source_ids(self) -> Set[str]:
        return super().source_ids()  # type: ignore[return-value]


class _ConcreteNode(BaseGraphNode[str, str]):
    @property
    def id(self) -> str:
        return super().id  # type: ignore[return-value]

    @property
    def value(self) -> Optional[str]:
        return super().value  # type: ignore[return-value]

    def prerequisite_ids(self) -> Set[str]:
        return super().prerequisite_ids()  # type: ignore[return-value]

    def dependents(self) -> Set[BaseGraphNode[str, str]]:
        return super().dependents()  # type: ignore[return-value]

    def is_ready(self, satisfied: Set[str]) -> bool:
        return super().is_ready(satisfied)  # type: ignore[return-value]

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)  # type: ignore[return-value]


class _ConcreteGraph(BaseGraph[str, str]):
    @property
    def nodes(self) -> Dict[str, BaseGraphNode[str, str]]:
        return super().nodes  # type: ignore[return-value]

    def add_node(
        self, node_id: str, value: Optional[str] = None
    ) -> BaseGraphNode[str, str]:
        return super().add_node(node_id, value)  # type: ignore[return-value]

    def get_node(self, node_id: str) -> Optional[BaseGraphNode[str, str]]:
        return super().get_node(node_id)  # type: ignore[return-value]

    def remove_node(self, node_id: str) -> None:
        return super().remove_node(node_id)

    def prerequisite_ids(self, node_id: str) -> Set[str]:
        return super().prerequisite_ids(node_id)  # type: ignore[return-value]

    def dependents(self, node_id: str) -> Set[str]:
        return super().dependents(node_id)  # type: ignore[return-value]

    def ancestors(self, node_id: str) -> Set[str]:
        return super().ancestors(node_id)  # type: ignore[return-value]

    def descendants(self, node_id: str) -> Set[str]:
        return super().descendants(node_id)  # type: ignore[return-value]

    def ready_nodes(self, satisfied: Set[str]) -> Set[str]:
        return super().ready_nodes(satisfied)  # type: ignore[return-value]

    def topological_order(self) -> List[str]:
        return super().topological_order()  # type: ignore[return-value]

    def validate_acyclic(self) -> None:
        return super().validate_acyclic()

    def to_dot(self) -> str:
        return super().to_dot()  # type: ignore[return-value]

    def to_mermaid(
        self,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[str]], str]] = None,
        max_label_length: int = 30,
    ) -> str:
        return super().to_mermaid(node_label_fn, edge_label_fn, max_label_length)  # type: ignore[return-value]

    def to_json_dict(self) -> Dict[str, Any]:
        return super().to_json_dict()  # type: ignore[return-value]

    def to_json(self, pretty: bool = True, indent: int = 2) -> str:
        return super().to_json(pretty, indent)  # type: ignore[return-value]

    def to_ascii_tree(
        self,
        root_nodes: Optional[List[str]] = None,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[str]], str]] = None,
        max_depth: int = 10,
    ) -> str:
        return super().to_ascii_tree(root_nodes, node_label_fn, edge_label_fn, max_depth)  # type: ignore[return-value]


class TestGraphBasePassBodies:
    def test_edge(self) -> None:
        e = _ConcreteEdge()
        assert e.sources is None
        assert e.metadata is None
        assert e.source_ids() is None

    def test_node(self) -> None:
        n = _ConcreteNode()
        assert n.id is None
        assert n.value is None
        assert n.prerequisite_ids() is None
        assert n.dependents() is None
        assert n.is_ready(set()) is None
        # __hash__ and __eq__ pass bodies return None, so we call them
        # directly without requiring proper int/bool
        n.__hash__()
        n.__eq__(n)

    def test_graph(self) -> None:
        g = _ConcreteGraph()
        assert g.nodes is None
        assert g.add_node("x") is None
        assert g.get_node("x") is None
        g.remove_node("x")
        assert g.prerequisite_ids("x") is None
        assert g.dependents("x") is None
        assert g.ancestors("x") is None
        assert g.descendants("x") is None
        assert g.ready_nodes(set()) is None
        assert g.topological_order() is None
        g.validate_acyclic()
        assert g.to_dot() is None
        assert g.to_mermaid() is None
        assert g.to_json_dict() is None
        assert g.to_json() is None
        assert g.to_ascii_tree() is None


# ═══════════════════════════════════════════════════════════════════
# dag/base.py — BaseDirectedAcyclicGraphEdge, Node, Graph
# ═══════════════════════════════════════════════════════════════════

from core.data_structure.dag.base import (
    BaseDirectedAcyclicGraph,
    BaseDirectedAcyclicGraphEdge,
    BaseDirectedAcyclicGraphNode,
)


class _DAGEdge(BaseDirectedAcyclicGraphEdge[str, str]):
    @property
    def target(self) -> BaseDirectedAcyclicGraphNode[str, str]:
        return super().target  # type: ignore[return-value]

    @property
    def sources(self) -> Set[BaseGraphNode[str, str]]:
        return super().sources  # type: ignore[return-value]

    @property
    def metadata(self) -> Optional[str]:
        return super().metadata  # type: ignore[return-value]

    def source_ids(self) -> Set[str]:
        return super().source_ids()  # type: ignore[return-value]


class _DAGNode(BaseDirectedAcyclicGraphNode[str, str]):
    @property
    def id(self) -> str:
        return super().id  # type: ignore[return-value]

    @property
    def value(self) -> Optional[str]:
        return super().value  # type: ignore[return-value]

    @property
    def depends_on(self) -> Dict[str, BaseDirectedAcyclicGraphEdge[str, str]]:
        return super().depends_on  # type: ignore[return-value]

    def prerequisites(self) -> Set[str]:
        return super().prerequisites()  # type: ignore[return-value]

    def prerequisite_ids(self) -> Set[str]:
        return super().prerequisite_ids()  # type: ignore[return-value]

    def prerequisite_nodes(self) -> Set[BaseDirectedAcyclicGraphNode[str, str]]:
        return super().prerequisite_nodes()  # type: ignore[return-value]

    def dependents(self) -> Set[BaseGraphNode[str, str]]:
        return super().dependents()  # type: ignore[return-value]

    def is_ready(self, satisfied: Set[str]) -> bool:
        return super().is_ready(satisfied)  # type: ignore[return-value]

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)  # type: ignore[return-value]


class _DAGraph(BaseDirectedAcyclicGraph[str, str]):
    @property
    def nodes(self) -> Dict[str, BaseGraphNode[str, str]]:
        return super().nodes  # type: ignore[return-value]

    def add_node(
        self, node_id: str, value: Optional[str] = None
    ) -> BaseDirectedAcyclicGraphNode[str, str]:
        return super().add_node(node_id, value)  # type: ignore[return-value]

    def get_node(
        self, node_id: str
    ) -> Optional[BaseDirectedAcyclicGraphNode[str, str]]:
        return super().get_node(node_id)  # type: ignore[return-value]

    def add_edge(
        self,
        prereq_id: str,
        dep_id: str,
        *,
        metadata: Optional[str] = None,
        check_cycle: bool = True,
    ) -> None:
        return super().add_edge(
            prereq_id, dep_id, metadata=metadata, check_cycle=check_cycle
        )

    def remove_edge(self, prereq_id: str, dep_id: str) -> None:
        return super().remove_edge(prereq_id, dep_id)

    def remove_node(self, node_id: str) -> None:
        return super().remove_node(node_id)

    def prerequisites(self, node_id: str) -> Set[str]:
        return super().prerequisites(node_id)  # type: ignore[return-value]

    def prerequisite_ids(self, node_id: str) -> Set[str]:
        return super().prerequisite_ids(node_id)  # type: ignore[return-value]

    def dependents(self, node_id: str) -> Set[str]:
        return super().dependents(node_id)  # type: ignore[return-value]

    def ancestors(self, node_id: str) -> Set[str]:
        return super().ancestors(node_id)  # type: ignore[return-value]

    def descendants(self, node_id: str) -> Set[str]:
        return super().descendants(node_id)  # type: ignore[return-value]

    def ready_nodes(self, satisfied: Set[str]) -> Set[str]:
        return super().ready_nodes(satisfied)  # type: ignore[return-value]

    def topological_order(self) -> List[str]:
        return super().topological_order()  # type: ignore[return-value]

    def validate_acyclic(self) -> None:
        return super().validate_acyclic()

    def iter_edges(self) -> Iterator[Tuple[str, str, Optional[str]]]:
        return super().iter_edges()  # type: ignore[return-value]

    def to_dot(self) -> str:
        return super().to_dot()  # type: ignore[return-value]

    def to_ascii_tree(
        self,
        root_nodes: Optional[List[str]] = None,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[str]], str]] = None,
        max_depth: int = 10,
    ) -> str:
        return super().to_ascii_tree(root_nodes, node_label_fn, edge_label_fn, max_depth)  # type: ignore[return-value]

    def to_mermaid(
        self,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[str]], str]] = None,
        max_label_length: int = 30,
        root_nodes: Optional[List[str]] = None,
    ) -> str:
        return super().to_mermaid(node_label_fn, edge_label_fn, max_label_length, root_nodes)  # type: ignore[return-value]

    def to_json_dict(self) -> Dict[str, Any]:
        return super().to_json_dict()  # type: ignore[return-value]

    def to_json(self, pretty: bool = True, indent: int = 2) -> str:
        return super().to_json(pretty, indent)  # type: ignore[return-value]


class TestDAGBasePassBodies:
    def test_edge(self) -> None:
        e = _DAGEdge()
        assert e.target is None
        assert e.sources is None
        assert e.metadata is None
        assert e.source_ids() is None

    def test_node(self) -> None:
        n = _DAGNode()
        assert n.id is None
        assert n.value is None
        assert n.depends_on is None
        assert n.prerequisites() is None
        assert n.prerequisite_ids() is None
        assert n.prerequisite_nodes() is None
        assert n.is_ready(set()) is None
        n.__hash__()
        n.__eq__(n)

    def test_graph(self) -> None:
        g = _DAGraph()
        assert g.add_node("x") is None
        assert g.get_node("x") is None
        g.add_edge("a", "b")
        g.remove_edge("a", "b")
        g.remove_node("x")
        assert g.prerequisites("x") is None
        assert g.prerequisite_ids("x") is None
        assert g.dependents("x") is None
        assert g.ancestors("x") is None
        assert g.descendants("x") is None
        assert g.ready_nodes(set()) is None
        assert g.topological_order() is None
        g.validate_acyclic()
        assert g.iter_edges() is None
        assert g.to_dot() is None
        assert g.to_mermaid() is None
        assert g.to_json_dict() is None
        assert g.to_json() is None
        assert g.to_ascii_tree() is None


# ═══════════════════════════════════════════════════════════════════
# dah/base.py — BaseDirectedAcyclicHypergraphEdge, Node, Graph
# ═══════════════════════════════════════════════════════════════════

from core.data_structure.dah.base import (
    BaseDirectedAcyclicHypergraph,
    BaseDirectedAcyclicHypergraphEdge,
    BaseDirectedAcyclicHypergraphNode,
)


class _DAHEdge(BaseDirectedAcyclicHypergraphEdge[str, str]):
    @property
    def id(self) -> str:
        return super().id  # type: ignore[return-value]

    @property
    def sources(self) -> Set[BaseGraphNode[str, str]]:
        return super().sources  # type: ignore[return-value]

    @property
    def metadata(self) -> Optional[str]:
        return super().metadata  # type: ignore[return-value]

    def source_ids(self) -> Set[str]:
        return super().source_ids()  # type: ignore[return-value]


class _DAHNode(BaseDirectedAcyclicHypergraphNode[str, str]):
    @property
    def id(self) -> str:
        return super().id  # type: ignore[return-value]

    @property
    def value(self) -> Optional[str]:
        return super().value  # type: ignore[return-value]

    @property
    def in_edges(self) -> Dict[str, BaseDirectedAcyclicHypergraphEdge[str, str]]:
        return super().in_edges  # type: ignore[return-value]

    def prerequisite_ids(self) -> Set[str]:
        return super().prerequisite_ids()  # type: ignore[return-value]

    def hyperedges(self) -> List[BaseDirectedAcyclicHypergraphEdge[str, str]]:
        return super().hyperedges()  # type: ignore[return-value]

    def is_ready(self, satisfied: Set[str]) -> bool:
        return super().is_ready(satisfied)  # type: ignore[return-value]

    def dependents(self) -> Set[BaseGraphNode[str, str]]:
        return super().dependents()  # type: ignore[return-value]

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)  # type: ignore[return-value]


class _DAHGraph(BaseDirectedAcyclicHypergraph[str, str]):
    @property
    def nodes(self) -> Dict[str, BaseGraphNode[str, str]]:
        return super().nodes  # type: ignore[return-value]

    def add_node(
        self, node_id: str, value: Optional[str] = None
    ) -> BaseDirectedAcyclicHypergraphNode[str, str]:
        return super().add_node(node_id, value)  # type: ignore[return-value]

    def get_node(
        self, node_id: str
    ) -> Optional[BaseDirectedAcyclicHypergraphNode[str, str]]:
        return super().get_node(node_id)  # type: ignore[return-value]

    def add_hyperedge(
        self,
        sources: Iterable[str],
        target_id: str,
        *,
        metadata: Optional[str] = None,
        edge_id: Optional[str] = None,
        check_cycle: bool = True,
    ) -> str:
        return super().add_hyperedge(sources, target_id, metadata=metadata, edge_id=edge_id, check_cycle=check_cycle)  # type: ignore[return-value]

    def remove_hyperedge(self, edge_id: str, target_id: str) -> None:
        return super().remove_hyperedge(edge_id, target_id)

    def remove_node(self, node_id: str) -> None:
        return super().remove_node(node_id)

    def prerequisite_ids(self, node_id: str) -> Set[str]:
        return super().prerequisite_ids(node_id)  # type: ignore[return-value]

    def dependents(self, node_id: str) -> Set[str]:
        return super().dependents(node_id)  # type: ignore[return-value]

    def ancestors(self, node_id: str) -> Set[str]:
        return super().ancestors(node_id)  # type: ignore[return-value]

    def descendants(self, node_id: str) -> Set[str]:
        return super().descendants(node_id)  # type: ignore[return-value]

    def ready_nodes(self, satisfied: Set[str]) -> Set[str]:
        return super().ready_nodes(satisfied)  # type: ignore[return-value]

    def topological_order(self) -> List[str]:
        return super().topological_order()  # type: ignore[return-value]

    def validate_acyclic(self) -> None:
        return super().validate_acyclic()

    def iter_hyperedges(self) -> Iterator[Tuple[Set[str], str, Optional[str], str]]:
        return super().iter_hyperedges()  # type: ignore[return-value]

    def add_edge(
        self,
        prereq_id: str,
        dep_id: str,
        *,
        metadata: Optional[str] = None,
        check_cycle: bool = True,
    ) -> str:
        return super().add_edge(prereq_id, dep_id, metadata=metadata, check_cycle=check_cycle)  # type: ignore[return-value]

    def ensure_node_hierarchy(self, path: str) -> None:
        return super().ensure_node_hierarchy(path)

    def to_dot(self) -> str:
        return super().to_dot()  # type: ignore[return-value]

    def to_mermaid(
        self,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[str]], str]] = None,
        max_label_length: int = 30,
    ) -> str:
        return super().to_mermaid(node_label_fn, edge_label_fn, max_label_length)  # type: ignore[return-value]

    def to_json_dict(self) -> Dict[str, Any]:
        return super().to_json_dict()  # type: ignore[return-value]

    def to_json(self, pretty: bool = True, indent: int = 2) -> str:
        return super().to_json(pretty, indent)  # type: ignore[return-value]

    def to_ascii_tree(
        self,
        root_nodes: Optional[List[str]] = None,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[str]], str]] = None,
        max_depth: int = 10,
    ) -> str:
        return super().to_ascii_tree(root_nodes, node_label_fn, edge_label_fn, max_depth)  # type: ignore[return-value]


class TestDAHBasePassBodies:
    def test_edge(self) -> None:
        e = _DAHEdge()
        assert e.id is None
        assert e.sources is None
        assert e.metadata is None
        assert e.source_ids() is None

    def test_node(self) -> None:
        n = _DAHNode()
        assert n.id is None
        assert n.value is None
        assert n.in_edges is None
        assert n.prerequisite_ids() is None
        assert n.hyperedges() is None
        assert n.is_ready(set()) is None
        assert n.dependents() is None
        n.__hash__()
        n.__eq__(n)

    def test_graph(self) -> None:
        g = _DAHGraph()
        assert g.nodes is None
        assert g.add_node("x") is None
        assert g.get_node("x") is None
        assert g.add_hyperedge(["a"], "b") is None
        g.remove_hyperedge("e", "t")
        g.remove_node("x")
        assert g.prerequisite_ids("x") is None
        assert g.dependents("x") is None
        assert g.ancestors("x") is None
        assert g.descendants("x") is None
        assert g.ready_nodes(set()) is None
        assert g.topological_order() is None
        g.validate_acyclic()
        assert g.iter_hyperedges() is None
        assert g.add_edge("a", "b") is None
        g.ensure_node_hierarchy("a.b")
        assert g.to_dot() is None
        assert g.to_mermaid() is None
        assert g.to_json_dict() is None
        assert g.to_json() is None
        assert g.to_ascii_tree() is None


# ═══════════════════════════════════════════════════════════════════
# observer/base.py — BaseObserver, BaseSubject
# ═══════════════════════════════════════════════════════════════════

from core.data_structure.observer.base import BaseObserver, BaseSubject


class _ConcreteObserver(BaseObserver[str]):
    async def notified(self, subject: BaseSubject[str], event: str) -> object:
        return await super().notified(subject, event)


class _ConcreteSubject(BaseSubject[str]):
    @property
    def observers(self) -> Tuple[BaseObserver[str], ...]:
        return super().observers  # type: ignore[return-value]

    def attach(self, observer: BaseObserver[str]) -> None:
        return super().attach(observer)

    def detach(self, observer: BaseObserver[str]) -> None:
        return super().detach(observer)

    async def notify(self, event: str) -> List[object]:
        return await super().notify(event)


class TestObserverBasePassBodies:
    @pytest.mark.asyncio
    async def test_observer(self) -> None:
        obs = _ConcreteObserver()
        sub = _ConcreteSubject()
        result = await obs.notified(sub, "evt")
        assert result is None

    @pytest.mark.asyncio
    async def test_subject(self) -> None:
        sub = _ConcreteSubject()
        assert sub.observers is None
        sub.attach(_ConcreteObserver())
        sub.detach(_ConcreteObserver())
        result = await sub.notify("evt")
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# state/base/base.py — BaseDAHState
# ═══════════════════════════════════════════════════════════════════

from core.state.base.base import BaseDAHState


class _ConcreteDAHState(BaseDAHState[str]):
    def get_field(self, path: str) -> Optional[str]:
        return super().get_field(path)  # type: ignore[return-value]

    def set_field(self, path: str, value: str) -> None:
        return super().set_field(path, value)

    def remove_field(self, path: str) -> bool:
        return super().remove_field(path)  # type: ignore[return-value]

    def get_all_fields(self) -> Dict[str, Optional[str]]:
        return super().get_all_fields()  # type: ignore[return-value]

    def iter_fields(self) -> Iterator[Tuple[str, Optional[str]]]:
        return super().iter_fields()  # type: ignore[return-value]

    def get_filled_fields(self) -> List[str]:
        return super().get_filled_fields()  # type: ignore[return-value]

    def get_empty_fields(self) -> List[str]:
        return super().get_empty_fields()  # type: ignore[return-value]

    def is_complete(self, required_fields: Optional[List[str]] = None) -> bool:
        return super().is_complete(required_fields)  # type: ignore[return-value]

    def to_json(self) -> str:
        return super().to_json()  # type: ignore[return-value]

    def copy(self) -> _ConcreteDAHState:
        return super().copy()  # type: ignore[return-value]

    @classmethod
    def from_json(cls, json_str: str) -> _ConcreteDAHState:
        return super().from_json(json_str)  # type: ignore[return-value]

    def add_field_dependency(self, parent_path: str, child_path: str) -> None:
        return super().add_field_dependency(parent_path, child_path)

    def get_children(self, parent_path: str) -> List[str]:
        return super().get_children(parent_path)  # type: ignore[return-value]


class TestBaseDAHStatePassBodies:
    def test_all_methods(self) -> None:
        s = _ConcreteDAHState()
        assert s.get_field("x") is None
        s.set_field("x", "v")
        assert s.remove_field("x") is None
        assert s.get_all_fields() is None
        assert s.iter_fields() is None
        assert s.get_filled_fields() is None
        assert s.get_empty_fields() is None
        assert s.is_complete() is None
        assert s.to_json() is None
        assert s.copy() is None
        assert _ConcreteDAHState.from_json("{}") is None
        s.add_field_dependency("a", "b")
        assert s.get_children("a") is None


# ═══════════════════════════════════════════════════════════════════
# state/state/base.py — BaseState (add_inference, add_value)
# ═══════════════════════════════════════════════════════════════════

from core.state.state.base import BaseState
from core.state.state.schema import Inference, ValueConfidence


class _ConcreteBaseState(BaseState):
    # Inherit from BaseDAHState
    def get_field(self, path: str) -> Any:
        return None

    def set_field(self, path: str, value: Any) -> None:
        pass

    def remove_field(self, path: str) -> bool:
        return False

    def get_all_fields(self) -> Dict[str, Any]:
        return {}

    def iter_fields(self) -> Iterator[Tuple[str, Any]]:
        return iter([])

    def get_filled_fields(self) -> List[str]:
        return []

    def get_empty_fields(self) -> List[str]:
        return []

    def is_complete(self, required_fields: Optional[List[str]] = None) -> bool:
        return False

    def to_json(self) -> str:
        return "{}"

    def copy(self) -> _ConcreteBaseState:
        return _ConcreteBaseState()

    @classmethod
    def from_json(cls, json_str: str) -> _ConcreteBaseState:
        return cls()

    def add_field_dependency(self, parent_path: str, child_path: str) -> None:
        pass

    def get_children(self, parent_path: str) -> List[str]:
        return []

    def add_inference(self, path: str, inference: Inference) -> None:
        super().add_inference(path, inference)

    def add_value(self, path: str, value_confidence: ValueConfidence) -> None:
        super().add_value(path, value_confidence)


class TestBaseStatePassBodies:
    def test_add_inference(self) -> None:
        s = _ConcreteBaseState()
        s.add_inference("x", Inference(content="hello"))

    def test_add_value(self) -> None:
        s = _ConcreteBaseState()
        s.add_value("x", ValueConfidence(value="v", confidence=0.5))


# ═══════════════════════════════════════════════════════════════════
# state/repository/base.py — BaseRepository
# ═══════════════════════════════════════════════════════════════════

from core.state.repository.base import BaseRepository
from core.state.state.state import State


class _ConcreteRepository(BaseRepository[State]):
    async def get(self, state_id: str) -> Optional[State]:
        return await super().get(state_id)  # type: ignore[return-value]

    async def save(self, state_id: str, state: State) -> None:
        return await super().save(state_id, state)

    async def delete(self, state_id: str) -> bool:
        return await super().delete(state_id)  # type: ignore[return-value]

    async def exists(self, state_id: str) -> bool:
        return await super().exists(state_id)  # type: ignore[return-value]


class TestBaseRepositoryPassBodies:
    @pytest.mark.asyncio
    async def test_all_methods(self) -> None:
        r = _ConcreteRepository()
        assert await r.get("id") is None
        await r.save("id", State())
        assert await r.delete("id") is None
        assert await r.exists("id") is None


# ═══════════════════════════════════════════════════════════════════
# evaluator/base.py — BaseEvaluator
# ═══════════════════════════════════════════════════════════════════

from core.evaluator.base import BaseEvaluator
from core.evaluator.schema import EvaluationContext, EvaluationResult, StateComparison


class _ConcreteEvaluator(BaseEvaluator):
    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        return await super().evaluate(context)  # type: ignore[return-value]

    async def _compare_states(
        self, expected: BaseState, actual: BaseState
    ) -> StateComparison:
        return await super()._compare_states(expected, actual)  # type: ignore[return-value]


class TestBaseEvaluatorPassBodies:
    @pytest.mark.asyncio
    async def test_evaluate(self) -> None:
        e = _ConcreteEvaluator()
        result = await e.evaluate(None)  # type: ignore[arg-type]
        assert result is None

    @pytest.mark.asyncio
    async def test_compare_states(self) -> None:
        e = _ConcreteEvaluator()
        result = await e._compare_states(None, None)  # type: ignore[arg-type]
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# mutator/base/base.py — BaseMutator
# ═══════════════════════════════════════════════════════════════════

from core.mutator.base.base import BaseMutator
from core.mutator.base.schema import MutationResult


class _ConcreteMutator(BaseMutator[str]):
    async def mutate(self, context: str) -> MutationResult:
        return await super().mutate(context)  # type: ignore[return-value]


class TestBaseMutatorPassBodies:
    @pytest.mark.asyncio
    async def test_mutate(self) -> None:
        m = _ConcreteMutator()
        result = await m.mutate("ctx")
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# mutator/llm/client/base.py — BaseLLMClient
# ═══════════════════════════════════════════════════════════════════

from core.mutator.llm.client.base import BaseLLMClient


class _ConcreteLLMClient(BaseLLMClient):
    async def generate(self, prompt: str) -> str:
        return await super().generate(prompt)  # type: ignore[return-value]


class TestBaseLLMClientPassBodies:
    @pytest.mark.asyncio
    async def test_generate(self) -> None:
        c = _ConcreteLLMClient()
        result = await c.generate("hello")
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# projector/base/projector.py — BaseProjector
# ═══════════════════════════════════════════════════════════════════

from core.projector.base.projector import BaseProjector
from core.projector.base.schema import ProjectionContext, ProjectionResult


class _ConcreteProjector(BaseProjector[ProjectionContext, ProjectionResult]):
    async def project(self, context: ProjectionContext) -> ProjectionResult:
        return await super().project(context)  # type: ignore[return-value]

    async def initialize(self, schema: Optional[Schema] = None) -> None:
        return await super().initialize(schema)


class TestBaseProjectorPassBodies:
    @pytest.mark.asyncio
    async def test_project(self) -> None:
        p = _ConcreteProjector()
        result = await p.project(None)  # type: ignore[arg-type]
        assert result is None

    @pytest.mark.asyncio
    async def test_initialize(self) -> None:
        p = _ConcreteProjector()
        await p.initialize(None)


# ═══════════════════════════════════════════════════════════════════
# projector/ui/projector.py — BaseProjectorUI
# ═══════════════════════════════════════════════════════════════════

from core.projector.ui.projector import BaseProjectorUI
from core.projector.ui.schema import (
    UIComponent,
    UIProjectionContext,
    UIProjectionResult,
)


class _ConcreteProjectorUI(BaseProjectorUI):
    async def project(self, context: UIProjectionContext) -> UIProjectionResult:
        return await super().project(context)  # type: ignore[return-value]

    async def generate_prompt(self, context: UIProjectionContext) -> str:
        return await super().generate_prompt(context)  # type: ignore[return-value]

    def map_field_to_component(self, field_key: str) -> UIComponent:
        return super().map_field_to_component(field_key)  # type: ignore[return-value]

    async def initialize(self, schema: Optional[Schema] = None) -> None:
        pass


class TestBaseProjectorUIPassBodies:
    @pytest.mark.asyncio
    async def test_project(self) -> None:
        p = _ConcreteProjectorUI()
        result = await p.project(None)  # type: ignore[arg-type]
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_prompt(self) -> None:
        p = _ConcreteProjectorUI()
        result = await p.generate_prompt(None)  # type: ignore[arg-type]
        assert result is None

    def test_map_field_to_component(self) -> None:
        p = _ConcreteProjectorUI()
        result = p.map_field_to_component("field")
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# spec_extractor/base/extractor.py — BaseSpecExtractor
# ═══════════════════════════════════════════════════════════════════

from pathlib import Path
from typing import Union

from core.spec_extractor.base.extractor import BaseSpecExtractor
from core.spec_extractor.base.schema import Schema


class _ConcreteSpecExtractor(BaseSpecExtractor):
    def read(self, source: Union[str, Path]) -> Schema:
        return super().read(source)  # type: ignore[return-value]


class TestBaseSpecExtractorPassBodies:
    def test_read(self) -> None:
        e = _ConcreteSpecExtractor()
        result = e.read("source")
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# action/base/action.py — BaseAction (execute, validate, rollback)
# ═══════════════════════════════════════════════════════════════════

from core.action.base.action import BaseAction
from core.action.base.schema import ActionContext, ActionResult


class _ConcreteAction(BaseAction):
    async def execute(self, context: ActionContext) -> ActionResult:
        return await super().execute(context)  # type: ignore[return-value]

    async def validate(self, context: ActionContext) -> Tuple[bool, Optional[str]]:
        return await super().validate(context)  # type: ignore[return-value]

    async def rollback(self, context: ActionContext) -> bool:
        return await super().rollback(context)  # type: ignore[return-value]


class TestBaseActionPassBodies:
    @pytest.mark.asyncio
    async def test_execute(self) -> None:
        a = _ConcreteAction()
        result = await a.execute(None)  # type: ignore[arg-type]
        assert result is None

    @pytest.mark.asyncio
    async def test_validate(self) -> None:
        a = _ConcreteAction()
        result = await a.validate(None)  # type: ignore[arg-type]
        assert result is None

    @pytest.mark.asyncio
    async def test_rollback(self) -> None:
        a = _ConcreteAction()
        result = await a.rollback(None)  # type: ignore[arg-type]
        assert result is None
