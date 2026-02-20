"""In-memory State Repository implementation.

This module provides an in-memory implementation of the state repository
for single-session or testing scenarios.
"""

from typing import Any, Dict, Optional, TypeVar

from ..base.base import BaseDAHState
from .base import BaseStateRepository

TState = TypeVar("TState", bound=BaseDAHState[Any])


class InMemoryStateRepository(BaseStateRepository[TState]):
    """In-memory implementation of state repository.

    Stores states in a dictionary. Suitable for single-session scenarios
    or testing. Not suitable for distributed or persistent storage.
    """

    def __init__(self) -> None:
        """Initialize the in-memory storage."""
        self._storage: Dict[str, TState] = {}

    async def get(self, state_id: str) -> Optional[TState]:
        """Retrieve state from memory.

        Args:
            state_id: Unique identifier for the state

        Returns:
            State instance or None if not found
        """
        return self._storage.get(state_id)

    async def save(self, state_id: str, state: TState) -> None:
        """Save state to memory.

        Args:
            state_id: Unique identifier for the state
            state: State instance to save
        """
        self._storage[state_id] = state

    async def delete(self, state_id: str) -> bool:
        """Delete state from memory.

        Args:
            state_id: Unique identifier for the state

        Returns:
            True if deleted, False if not found
        """
        if state_id in self._storage:
            del self._storage[state_id]
            return True
        return False

    async def exists(self, state_id: str) -> bool:
        """Check if state exists in memory.

        Args:
            state_id: Unique identifier for the state

        Returns:
            True if state exists
        """
        return state_id in self._storage

    def clear(self) -> None:
        """Clear all states from memory."""
        self._storage.clear()
