"""Canonical State interface for LangState.

The Canonical State represents the resolved business state with simple key-value pairs.
Format: {key: value}

This is the state used for executing actions and represents the final resolved values.
"""

from abc import abstractmethod
from typing import Dict, List, Optional

from ..base.state import BaseState


class CanonicalState(BaseState[object]):
    """Canonical State interface.

    The Canonical State stores resolved field values in a simple key-value format.
    This is the business state used for executing actions.

    Format:
        {field_id: value}

    Example:
        state = CanonicalStateImpl()
        state.set_field("name", "John Doe")
        state.set_field("email", "john@example.com")

        # Get value
        name = state.get_field("name")  # "John Doe"

        # Convert to dict
        data = state.to_dict()  # {"name": "John Doe", "email": "john@example.com"}
    """

    @abstractmethod
    def get_field(self, field_id: str) -> Optional[object]:
        """Get the value for a specific field.

        Args:
            field_id: The field identifier

        Returns:
            Field value, None if not found
        """
        pass

    @abstractmethod
    def set_field(self, field_id: str, value: object) -> None:
        """Set the value for a specific field.

        Args:
            field_id: The field identifier
            value: The value to set
        """
        pass

    @abstractmethod
    def get_all_fields(self) -> Dict[str, object]:
        """Get all fields and their values.

        Returns:
            Dictionary of field_id to value
        """
        pass

    @abstractmethod
    def get_filled_fields(self) -> List[str]:
        """Get list of fields that have been filled.

        Returns:
            List of field identifiers that have non-None values
        """
        pass

    @abstractmethod
    def get_empty_fields(self) -> List[str]:
        """Get list of fields that are still empty.

        Returns:
            List of field identifiers that have None values
        """
        pass

    @abstractmethod
    def is_complete(self, required_fields: Optional[List[str]] = None) -> bool:
        """Check if the state is complete.

        Args:
            required_fields: Optional list of required field IDs.
                If None, checks all fields.

        Returns:
            True if all required fields have values
        """
        pass

    @abstractmethod
    def copy(self) -> "CanonicalState":
        """Create a copy of the state.

        Returns:
            A new CanonicalState instance with copied data
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, object]:
        """Convert state to dictionary representation.

        Returns:
            Dictionary of field_id to value
        """
        pass
