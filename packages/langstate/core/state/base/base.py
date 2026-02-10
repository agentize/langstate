from abc import ABC, abstractmethod
from typing import Dict, Generic, Iterator, List, Optional, Tuple
from typing_extensions import Self
from core.typing.generic import TFieldData


class BaseState(ABC, Generic[TFieldData]):
    """Abstract base class for State implementations.

    The State holds the current values directly in DAH.
    Uses DAH for internal storage where path is the key.

    Specialized implementations:
    - CanonicalState: Simple key-value state for business logic (values are primitives)
    - InterpretiveState: Rich state with inferences and confidence scores (values are InterpretiveFieldState)
    """

    @abstractmethod
    def get_field(self, path: str) -> Optional[TFieldData]:
        """Get the value/data for a specific field by path.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")

        Returns:
            Field value or data, None if not found
        """
        pass

    @abstractmethod
    def set_field(self, path: str, value: TFieldData) -> None:
        """Set the value/data for a specific field by path.

        Args:
            path: The field path (e.g., "name" or "guests.0.email")
            value: The value or data to set
        """
        pass

    @abstractmethod
    def remove_field(self, path: str) -> bool:
        """Remove a field by path.

        Args:
            path: The field path to remove

        Returns:
            True if field was removed, False if not found
        """
        pass

    @abstractmethod
    def get_all_fields(self) -> Dict[str, Optional[TFieldData]]:
        """Get all fields and their values/data.

        Returns:
            Dictionary of path to value/data (values can be None for unset leaf fields)
        """
        pass

    @abstractmethod
    def iter_fields(self) -> Iterator[Tuple[str, Optional[TFieldData]]]:
        """Iterate over all fields.

        Yields:
            Tuples of (path, value) where value can be None for unset leaf fields
        """
        pass

    @abstractmethod
    def get_filled_fields(self) -> List[str]:
        """Get list of field paths that have been filled.

        Returns:
            List of field paths that have values
        """
        pass

    @abstractmethod
    def get_empty_fields(self) -> List[str]:
        """Get list of field paths that are still empty.

        Returns:
            List of field paths that don't have values
        """
        pass

    @abstractmethod
    def is_complete(self, required_fields: Optional[List[str]] = None) -> bool:
        """Check if the state is complete.

        Args:
            required_fields: Optional list of required field paths.
                If None, checks all fields.

        Returns:
            True if all required fields have values
        """
        pass

    @abstractmethod
    def to_json(self) -> str:
        """Export the state to a JSON string.

        Returns:
            JSON string representation of the state
        """
        pass

    @abstractmethod
    def copy(self) -> Self:
        """Create a copy of the state.

        Returns:
            A new State instance with copied data
        """
        pass

    @abstractmethod
    def add_field_dependency(self, parent_path: str, child_path: str) -> None:
        """Add a dependency relationship between fields.

        Args:
            parent_path: The parent field path
            child_path: The child field path that depends on parent
        """
        pass

    @abstractmethod
    def get_children(self, parent_path: str) -> List[str]:
        """Get all direct child field paths of a parent.

        Args:
            parent_path: The parent field path

        Returns:
            List of child field paths
        """
        pass
