"""Base State interface for LangState.

The State represents the current state of the form/conversation.
This is the base interface that specialized states inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseState(ABC):
    """Abstract base class for State implementations.

    The State holds the current values and metadata for all fields.
    Specialized implementations:
    - CanonicalState: Simple key-value state for business logic
    - InterpretiveState: Rich state with inferences and confidence scores
    """

    @abstractmethod
    def get_field(self, field_id: str) -> Optional[object]:
        """Get the value/data for a specific field.

        Args:
            field_id: The field identifier

        Returns:
            Field value or data, None if not found
        """
        pass

    @abstractmethod
    def set_field(self, field_id: str, value: object) -> None:
        """Set the value/data for a specific field.

        Args:
            field_id: The field identifier
            value: The value or data to set
        """
        pass

    @abstractmethod
    def get_all_fields(self) -> Dict[str, object]:
        """Get all fields and their values/data.

        Returns:
            Dictionary of field_id to value/data
        """
        pass

    @abstractmethod
    def get_filled_fields(self) -> List[str]:
        """Get list of fields that have been filled.

        Returns:
            List of field identifiers that have values
        """
        pass

    @abstractmethod
    def get_empty_fields(self) -> List[str]:
        """Get list of fields that are still empty.

        Returns:
            List of field identifiers that don't have values
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
    def copy(self) -> "BaseState":
        """Create a copy of the state.

        Returns:
            A new State instance with copied data
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, object]:
        """Convert state to dictionary representation.

        Returns:
            Dictionary representation of the state
        """
        pass
