"""Canonical State implementation using DAH storage."""

from typing import Any, Optional, cast
from typing_extensions import Self

from core.spec_extractor.base.schema import Schema, SchemaField
from core.state.state import State
from core.state.canonical.base import BaseCanonicalState
from core.state.canonical.schema import CanonicalFieldValue


class CanonicalState(BaseCanonicalState, State[CanonicalFieldValue]):
    """Canonical State implementation with DAH-based storage.

    Inherits DAH-based storage from State and specialized interface from BaseCanonicalState.
    Field values are stored directly as primitives in DAH nodes with paths like:
    - "name" for simple fields
    - "address.city" for nested objects
    - "guests.0.email" for array elements

    Values are primitives: None, str, int, float, bool
    """

    @classmethod
    def from_schema(cls, schema: Schema) -> "CanonicalState":
        """Create a canonical state initialized from a Schema."""
        state = cls()
        _initialize_leaf_fields(state, schema.root, prefix="")
        return state

    def copy(self) -> Self:
        """Create a deep copy of the state.

        Returns:
            A new CanonicalState instance with deep copied data
        """
        new_state = self.__class__()

        # Copy all field values
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

    def _is_field_filled(self, value: Optional[CanonicalFieldValue]) -> bool:
        """Check if a field value is considered filled.

        Args:
            value: The field value to check

        Returns:
            True if the field has a value
        """
        return value is not None


def _initialize_leaf_fields(
    state: CanonicalState, fields: dict[str, SchemaField], prefix: str
) -> None:
    """Recursively initialize only leaf fields with primitive values."""
    for field_id, field in fields.items():
        full_path = f"{prefix}{field_id}" if prefix else field_id
        default_value = field.default_value

        is_nested_schema = False
        if isinstance(default_value, dict) and default_value:
            dict_value = cast(dict[str, Any], default_value)
            first_value = next(iter(dict_value.values()), None)

            if isinstance(first_value, SchemaField):
                nested_fields = cast(dict[str, SchemaField], dict_value)
                _initialize_leaf_fields(state, nested_fields, prefix=f"{full_path}.")
                is_nested_schema = True

        if not is_nested_schema:
            state.set_field(full_path, cast(CanonicalFieldValue, default_value))
