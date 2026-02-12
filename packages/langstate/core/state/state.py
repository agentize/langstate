"""Unified State implementation using DAH storage.

This class provides the common DAH-based storage behavior and interpretive
operations (inference + confidence values). It also remains compatible with
primitive value storage for transitional canonical-style usage.
"""

from typing import Dict, Iterator, List, Optional, Tuple
from typing_extensions import Self
from uuid import UUID

from core.data_structure.dah.dah import DirectedAcyclicHypergraph
from core.typing.generic import TFieldData
from .base import BaseState
from .interpretive.schema import Inference, InterpretiveFieldState, ValueConfidence


class State(BaseState[TFieldData]):
    """Common State implementation with DAH-based storage.

    Uses DirectedAcyclicHypergraph for storing field values:
    - Node ID: UUID (auto-generated unique identifier)
    - Node path: field path (e.g., "registrant.event.id") for addressing
    - Node value: The actual field data (primitive or InterpretiveFieldState)

    Public API uses paths for field access (get_field, set_field, etc.).
    UUIDs are internal identifiers accessible via get_field_uuid().
    """

    def __init__(self) -> None:
        """Initialize the state with empty DAH storage."""
        self._dah: DirectedAcyclicHypergraph[TFieldData, None] = (
            DirectedAcyclicHypergraph()
        )

    def get_field(self, path: str) -> Optional[TFieldData]:
        """Get the value stored at a specific field path."""
        node = self._dah.get_node(path)
        if node is None:
            return None
        return node.value

    def set_field(self, path: str, value: TFieldData) -> None:
        """Set a value at a specific field path."""
        # Ensure parent hierarchy exists
        self._ensure_parent_hierarchy(path)

        existing_node = self._dah.get_node(path)

        if existing_node is not None:
            existing_node.value = value
        else:
            self._dah.add_node(path, value)

    def _ensure_parent_hierarchy(self, path: str) -> None:
        """Internal method to create parent nodes and set up relationships."""
        parts = path.split(".")
        if len(parts) <= 1:
            return

        for i in range(1, len(parts)):
            parent_path = ".".join(parts[:i])
            child_path = ".".join(parts[: i + 1])

            parent_node = self._dah.get_node(parent_path)
            if parent_node is None:
                self._dah.add_node(parent_path, None)  # type: ignore[arg-type]

            if i < len(parts) - 1:
                child_node = self._dah.get_node(child_path)
                if child_node is None:
                    self._dah.add_node(child_path, None)  # type: ignore[arg-type]

            try:
                self._dah.add_hyperedge([parent_path], child_path, check_cycle=True)
            except ValueError:
                pass

    def remove_field(self, path: str) -> bool:
        """Remove a field and its value from the state."""
        node = self._dah.get_node(path)
        if node is None:
            return False
        self._dah.remove_node(path)
        return True

    def get_all_fields(self) -> Dict[str, Optional[TFieldData]]:
        """Get a dictionary of all field paths and their values."""
        result: Dict[str, Optional[TFieldData]] = {}
        for dah_node in self._dah.nodes.values():
            result[dah_node.path] = dah_node.value
        return result

    def iter_fields(self) -> Iterator[Tuple[str, Optional[TFieldData]]]:
        """Iterate over all fields in the state."""
        for dah_node in self._dah.nodes.values():
            yield (dah_node.path, dah_node.value)

    def get_field_uuid(self, path: str) -> Optional[UUID]:
        """Get the unique identifier (UUID) for a field."""
        node = self._dah.get_node(path)
        if node is None:
            return None
        return node.id

    def get_filled_fields(self) -> List[str]:
        """Get all field paths that have been filled with values."""
        return [
            path for path, value in self.iter_fields() if self._is_field_filled(value)
        ]

    def get_empty_fields(self) -> List[str]:
        """Get all field paths that are still empty or unfilled."""
        return [
            path
            for path, value in self.iter_fields()
            if not self._is_field_filled(value)
        ]

    def is_complete(self, required_fields: Optional[List[str]] = None) -> bool:
        """Check whether all required fields have been filled."""
        if required_fields is not None:
            fields_to_check = required_fields
        else:
            fields_to_check = [
                path for path, value in self.iter_fields() if value is not None
            ]

        for path in fields_to_check:
            value = self.get_field(path)
            if not self._is_field_filled(value):
                return False

        return True

    def to_json(self) -> str:
        """Export the entire state as a JSON string."""
        return self._dah.to_json()

    def copy(self) -> Self:
        """Create an independent copy of this state."""
        new_state = self.__class__()

        for path, value in self.iter_fields():
            if isinstance(value, InterpretiveFieldState):
                new_value: Optional[TFieldData] = value.model_copy(deep=True)  # type: ignore[assignment]
            else:
                new_value = value
            new_state._dah.add_node(path, new_value)

        for sources, target, metadata, _edge_id in self._dah.iter_hyperedges():
            try:
                new_state._dah.add_hyperedge(
                    sources, target, metadata=metadata, check_cycle=False
                )
            except ValueError:
                pass

        return new_state

    def add_field_dependency(self, parent_path: str, child_path: str) -> None:
        """Create a dependency relationship where one field depends on another."""
        if self._dah.get_node(parent_path) is None:
            self._dah.add_node(parent_path, None)  # type: ignore[arg-type]

        if self._dah.get_node(child_path) is None:
            self._dah.add_node(child_path, None)  # type: ignore[arg-type]

        self._dah.add_hyperedge([parent_path], child_path, check_cycle=True)

    def get_children(self, parent_path: str) -> List[str]:
        """Get all fields that directly depend on this parent field."""
        return list(self._dah.dependents(parent_path))

    def get_dah(self) -> DirectedAcyclicHypergraph[TFieldData, None]:
        """Get direct access to the underlying graph data structure."""
        return self._dah

    def add_inference(self, path: str, inference: Inference) -> None:
        """Add an inference to a field."""
        field_state = self._get_or_create_field_state(path)
        field_state.inference.append(inference)

    def add_value(self, path: str, value_confidence: ValueConfidence) -> None:
        """Add a value-confidence pair to a field."""
        field_state = self._get_or_create_field_state(path)
        field_state.values.append(value_confidence)

    def get_best_value(self, path: str) -> Optional[ValueConfidence]:
        """Get the value with highest confidence for a field."""
        value = self.get_field(path)
        if not isinstance(value, InterpretiveFieldState):
            return None
        if not value.values:
            return None
        return max(value.values, key=lambda vc: vc.confidence)

    def _get_or_create_field_state(self, path: str) -> InterpretiveFieldState:
        """Get or create interpretive field state for a field path."""
        value = self.get_field(path)

        if value is not None:
            if not isinstance(value, InterpretiveFieldState):
                raise TypeError(
                    "Field value is not InterpretiveFieldState; "
                    "add_inference/add_value only apply to interpretive values."
                )
            return value

        new_field_state = InterpretiveFieldState(inference=[], values=[])
        self.set_field(path, new_field_state)  # type: ignore[arg-type]

        return new_field_state

    def _is_field_filled(self, value: Optional[TFieldData]) -> bool:
        """Determine whether a field value should be considered "filled"."""
        if value is None:
            return False
        if isinstance(value, InterpretiveFieldState):
            return len(value.values) > 0
        return True
