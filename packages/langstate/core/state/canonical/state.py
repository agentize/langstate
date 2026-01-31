"""Canonical State implementation using DAH storage."""

from typing import Optional

from core.state.base.state import State
from core.state.canonical.base import BaseCanonicalState
from core.state.canonical.schema import CanonicalFieldValue


class CanonicalState(State[CanonicalFieldValue], BaseCanonicalState):
    """Canonical State implementation with DAH-based storage.
    
    Inherits DAH-based storage from State and specialized interface from BaseCanonicalState.
    Field values are stored directly as primitives in DAH nodes with paths like:
    - "name" for simple fields
    - "address.city" for nested objects
    - "guests.0.email" for array elements
    
    Values are primitives: None, str, int, float, bool
    """
    
    def copy(self) -> "CanonicalState":
        """Create a deep copy of the state.

        Returns:
            A new CanonicalState instance with deep copied data
        """
        new_state = CanonicalState()
        
        # Copy all field values
        for path, value in self.iter_fields():
            new_state._dah.add_node(path, value)
        
        # Copy all hyperedges
        for sources, target, metadata, _edge_id in self._dah.iter_hyperedges():
            try:
                new_state._dah.add_hyperedge(sources, target, metadata=metadata, check_cycle=False)
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