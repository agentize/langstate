"""Canonical State implementation for LangState.

The Canonical State represents the resolved business state with simple key-value pairs.
Format: {key: value}

This is the state used for executing actions and represents the final resolved values.
"""

from typing import Dict, List, Optional

from ..base.state import BaseState
from .schema import CanonicalFieldState, CanonicalStateData


class CanonicalState(BaseState):
    """Canonical State implementation.

    The Canonical State stores resolved field values in a simple key-value format.
    This is the business state used for executing actions.

    Format:
        {field_id: value}

    Example:
        state = CanonicalState()
        state.set_field("name", "John Doe")
        state.set_field("email", "john@example.com")

        # Get value
        name = state.get_field("name")  # "John Doe"

        # Convert to dict
        data = state.to_dict()  # {"name": "John Doe", "email": "john@example.com"}
    """

    def __init__(self, initial_data: Optional[Dict[str, object]] = None) -> None:
        """Initialize canonical state.

        Args:
            initial_data: Optional initial field values
        """
        self._data = CanonicalStateData()
        if initial_data:
            for field_id, value in initial_data.items():
                self.set_field(field_id, value)

    def get_field(self, field_id: str) -> Optional[object]:
        """Get the value for a specific field.

        Args:
            field_id: The field identifier

        Returns:
            Field value, None if not found
        """
        field_state = self._data.fields.get(field_id)
        return field_state.value if field_state else None

    def set_field(self, field_id: str, value: object) -> None:
        """Set the value for a specific field.

        Args:
            field_id: The field identifier
            value: The value to set
        """
        self._data.fields[field_id] = CanonicalFieldState(
            field_id=field_id, value=value
        )

    def get_all_fields(self) -> Dict[str, object]:
        """Get all fields and their values.

        Returns:
            Dictionary of field_id to value
        """
        return {
            field_id: field_state.value
            for field_id, field_state in self._data.fields.items()
        }

    def get_filled_fields(self) -> List[str]:
        """Get list of fields that have been filled.

        Returns:
            List of field identifiers that have non-None values
        """
        return [
            field_id
            for field_id, field_state in self._data.fields.items()
            if field_state.value is not None
        ]

    def get_empty_fields(self) -> List[str]:
        """Get list of fields that are still empty.

        Returns:
            List of field identifiers that have None values
        """
        return [
            field_id
            for field_id, field_state in self._data.fields.items()
            if field_state.value is None
        ]

    def is_complete(self, required_fields: Optional[List[str]] = None) -> bool:
        """Check if the state is complete.

        Args:
            required_fields: Optional list of required field IDs.
                If None, checks all fields.

        Returns:
            True if all required fields have values
        """
        fields_to_check = required_fields or list(self._data.fields.keys())
        for field_id in fields_to_check:
            field_state = self._data.fields.get(field_id)
            if not field_state or field_state.value is None:
                return False
        return True

    def copy(self) -> "CanonicalState":
        """Create a copy of the state.

        Returns:
            A new CanonicalState instance with copied data
        """
        new_state = CanonicalState()
        for field_id, field_state in self._data.fields.items():
            new_state.set_field(field_id, field_state.value)
        new_state._data.metadata = self._data.metadata.copy()
        return new_state

    def to_dict(self) -> Dict[str, object]:
        """Convert state to dictionary representation.

        Returns:
            Dictionary of field_id to value
        """
        return self.get_all_fields()
