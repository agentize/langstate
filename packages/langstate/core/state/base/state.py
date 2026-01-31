"""Base State interface for LangState.

The State represents the current state of the form/conversation.
This is the base interface that specialized states inherit from.

State uses DAH (Directed Acyclic Hypergraph) for internal storage where:
- Each node has a UUID (id) for unique identification
- Each node has a path (e.g., "guests.1.name") for addressing
- Nested fields use dot notation: parent.child or parent.index for arrays
- Field relationships can be modeled via hyperedges
- Values are stored directly (primitives for canonical, InterpretiveFieldState for interpretive)
"""

from typing import Dict, Iterator, List, Optional, Tuple
from uuid import UUID

from core.data_structure.dah.dah import DirectedAcyclicHypergraph
from core.state.base.base import BaseState
from core.typing.generic import TFieldData


class State(BaseState[TFieldData]):
    """Common base implementation of State with DAH-based storage.

    This class provides the common functionality for all state types.
    Uses DirectedAcyclicHypergraph for storing field values:
    - Node ID: UUID (auto-generated unique identifier)
    - Node path: field path (e.g., "registrant.event.id") for addressing
    - Node value: The actual field data (primitive for canonical, InterpretiveFieldState for interpretive)

    Public API uses paths for field access (get_field, set_field, etc.).
    UUIDs are internal identifiers accessible via get_field_uuid().

    Subclasses should implement type-specific methods and behaviors.
    """

    def __init__(self) -> None:
        """Initialize the state with empty DAH storage."""
        self._dah: DirectedAcyclicHypergraph[TFieldData, None] = (
            DirectedAcyclicHypergraph()
        )

    def get_field(self, path: str) -> Optional[TFieldData]:
        """Get the value/data for a specific field by path.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")

        Returns:
            Field value or data, None if not found
        """
        node = self._dah.get_node(path)
        if node is None:
            return None
        return node.value

    def set_field(self, path: str, value: TFieldData) -> None:
        """Set the value/data for a specific field by path.

        Creates new node if path doesn't exist, updates value if it does.
        Automatically creates parent nodes and dependencies for nested paths.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")
            value: The value or data to set
        """
        # Ensure parent hierarchy exists
        self._ensure_parent_hierarchy(path)

        existing_node = self._dah.get_node(path)

        if existing_node is not None:
            # Update existing node's value
            existing_node.value = value
        else:
            # Create new node
            self._dah.add_node(path, value)

    def _ensure_parent_hierarchy(self, path: str) -> None:
        """Ensure all parent nodes exist and have dependencies set up.

        Args:
            path: The full field path
        """
        parts = path.split(".")
        if len(parts) <= 1:
            return

        # Create all intermediate parent nodes and dependencies
        for i in range(1, len(parts)):
            parent_path = ".".join(parts[:i])
            child_path = ".".join(parts[: i + 1])

            # Ensure parent node exists
            parent_node = self._dah.get_node(parent_path)
            if parent_node is None:
                self._dah.add_node(parent_path, None)

            # Ensure child node exists (if not the final leaf)
            if i < len(parts) - 1:
                child_node = self._dah.get_node(child_path)
                if child_node is None:
                    self._dah.add_node(child_path, None)

            # Add dependency from parent to child
            try:
                self._dah.add_hyperedge([parent_path], child_path, check_cycle=True)
            except ValueError:
                # Edge already exists or would create cycle, skip
                pass

    def remove_field(self, path: str) -> bool:
        """Remove a field by path.

        Args:
            path: The field path to remove

        Returns:
            True if field was removed, False if not found
        """
        node = self._dah.get_node(path)
        if node is None:
            return False
        self._dah.remove_node(path)
        return True

    def get_all_fields(self) -> Dict[str, Optional[TFieldData]]:
        """Get all fields and their values/data.

        Returns:
            Dictionary of path to value/data for all fields (including None values)
        """
        result: Dict[str, Optional[TFieldData]] = {}
        for dah_node in self._dah.nodes.values():
            # Include all nodes - leaf fields can have None as a valid value
            result[dah_node.path] = dah_node.value
        return result

    def iter_fields(self) -> Iterator[Tuple[str, Optional[TFieldData]]]:
        """Iterate over all fields including those with None values.

        Yields:
            Tuples of (path, value) for all nodes in the DAH
        """
        for dah_node in self._dah.nodes.values():
            yield (dah_node.path, dah_node.value)

    def get_field_uuid(self, path: str) -> Optional[UUID]:
        """Get the UUID for a field by its path.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")

        Returns:
            UUID of the field node, None if not found
        """
        node = self._dah.get_node(path)
        if node is None:
            return None
        return node.id

    def get_filled_fields(self) -> List[str]:
        """Get list of field paths that have been filled.

        Returns:
            List of field paths that have values
        """
        return [
            path for path, value in self.iter_fields() if self._is_field_filled(value)
        ]

    def get_empty_fields(self) -> List[str]:
        """Get list of field paths that are still empty.

        Returns:
            List of field paths that don't have values
        """
        return [
            path
            for path, value in self.iter_fields()
            if not self._is_field_filled(value)
        ]

    def is_complete(self, required_fields: Optional[List[str]] = None) -> bool:
        """Check if the state is complete.

        Args:
            required_fields: Optional list of required field paths.
                If None, checks all fields with non-None values.

        Returns:
            True if all required fields have values
        """
        if required_fields is not None:
            fields_to_check = required_fields
        else:
            # Only check fields with non-None values (exclude parent container nodes)
            fields_to_check = [
                path for path, value in self.iter_fields() if value is not None
            ]

        for path in fields_to_check:
            value = self.get_field(path)
            if not self._is_field_filled(value):
                return False

        return True

    def copy(self) -> "State[TFieldData]":
        """Create a copy of the state.

        Returns:
            A new State instance with copied data
        """
        new_state = self.__class__()

        # Copy all nodes
        for path, value in self.iter_fields():
            new_state._dah.add_node(path, value)

        # Copy all hyperedges
        for sources, target, metadata, _edge_id in self._dah.iter_hyperedges():
            try:
                new_state._dah.add_hyperedge(
                    sources, target, metadata=metadata, check_cycle=False
                )
            except ValueError:
                pass

        return new_state

    def add_field_dependency(self, parent_path: str, child_path: str) -> None:
        """Add a dependency relationship between fields.

        Args:
            parent_path: The parent field path
            child_path: The child field path that depends on parent
        """
        # Ensure both nodes exist
        if self._dah.get_node(parent_path) is None:
            self._dah.add_node(parent_path, None)

        if self._dah.get_node(child_path) is None:
            self._dah.add_node(child_path, None)

        self._dah.add_hyperedge([parent_path], child_path, check_cycle=True)

    def get_children(self, parent_path: str) -> List[str]:
        """Get all direct child field paths of a parent.

        Args:
            parent_path: The parent field path

        Returns:
            List of child field paths
        """
        return list(self._dah.dependents(parent_path))

    def get_dah(self) -> DirectedAcyclicHypergraph[TFieldData, None]:
        """Get the underlying DAH structure.

        Returns:
            The DirectedAcyclicHypergraph instance
        """
        return self._dah

    def _is_field_filled(self, value: Optional[TFieldData]) -> bool:
        """Check if a field value is considered filled.

        Subclasses can override this to define custom fill logic.

        Args:
            value: The field value to check

        Returns:
            True if the field is filled
        """
        return value is not None
