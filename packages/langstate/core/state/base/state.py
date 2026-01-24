"""Base State interface for LangState.

The State represents the current state of the form/conversation.
This is the base interface that specialized states inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional

from packages.langstate.core.typing.generic import TFieldData


class BaseState(ABC, Generic[TFieldData]):
    """Abstract base class for State implementations.

    The State holds the current values and metadata for all fields.
    Specialized implementations:
    - CanonicalState: Simple key-value state for business logic
    - InterpretiveState: Rich state with inferences and confidence scores
    """

    @abstractmethod
    def get_field(self, field_id: str) -> Optional[TFieldData]:
        """Get the value/data for a specific field.

        Args:
            field_id: The field identifier

        Returns:
            Field value or data, None if not found
        """
        pass

    @abstractmethod
    def set_field(self, field_id: str, value: TFieldData) -> None:
        """Set the value/data for a specific field.

        Args:
            field_id: The field identifier
            value: The value or data to set
        """
        pass

    @abstractmethod
    def get_all_fields(self) -> Dict[str, TFieldData]:
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
    def copy(self) -> "BaseState[TFieldData]":
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


class State(BaseState[TFieldData]):
    """Common base implementation of State with shared methods.
    
    This class provides the common functionality for all state types.
    Subclasses should implement type-specific methods and behaviors.
    """

    def __init__(self) -> None:
        """Initialize the state with empty data storage."""
        self._data: Dict[str, TFieldData] = {}

    def get_field(self, field_id: str) -> Optional[TFieldData]:
        """Get the value/data for a specific field.

        Args:
            field_id: The field identifier

        Returns:
            Field value or data, None if not found
        """
        return self._data.get(field_id)

    def set_field(self, field_id: str, value: TFieldData) -> None:
        """Set the value/data for a specific field.

        Args:
            field_id: The field identifier
            value: The value or data to set
        """
        self._data[field_id] = value

    def get_all_fields(self) -> Dict[str, TFieldData]:
        """Get all fields and their values/data.

        Returns:
            Dictionary of field_id to value/data
        """
        return self._data.copy()

    def get_filled_fields(self) -> List[str]:
        """Get list of fields that have been filled.

        Returns:
            List of field identifiers that have values
        """
        return [field_id for field_id, value in self._data.items() if self._is_field_filled(value)]

    def get_empty_fields(self) -> List[str]:
        """Get list of fields that are still empty.

        Returns:
            List of field identifiers that don't have values
        """
        return [field_id for field_id, value in self._data.items() if not self._is_field_filled(value)]

    def is_complete(self, required_fields: Optional[List[str]] = None) -> bool:
        """Check if the state is complete.

        Args:
            required_fields: Optional list of required field IDs.
                If None, checks all fields.

        Returns:
            True if all required fields have values
        """
        fields_to_check = required_fields if required_fields is not None else list(self._data.keys())
        
        for field_id in fields_to_check:
            value = self._data.get(field_id)
            if not self._is_field_filled(value):
                return False
        
        return True

    def copy(self) -> "State[TFieldData]":
        """Create a copy of the state.

        Returns:
            A new State instance with copied data
        """
        new_state = self.__class__()
        new_state._data = self._data.copy()
        return new_state

    def to_dict(self) -> Dict[str, object]:
        """Convert state to dictionary representation.

        Returns:
            Dictionary representation of the state
        """
        return {field_id: self._field_to_dict(value) for field_id, value in self._data.items()}

    def _is_field_filled(self, value: Optional[TFieldData]) -> bool:
        """Check if a field value is considered filled.
        
        Subclasses can override this to define custom fill logic.

        Args:
            value: The field value to check

        Returns:
            True if the field is filled
        """
        return value is not None

    def _field_to_dict(self, value: TFieldData) -> object:
        """Convert a field value to dictionary representation.
        
        Subclasses can override this to define custom serialization.

        Args:
            value: The field value to convert

        Returns:
            Dictionary representation of the value
        """
        return value
