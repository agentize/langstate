"""State Repository interface for LangState.

The State Repository follows the Repository pattern (SRP, DIP) to separate
state storage concerns from business logic. This allows for different
storage backends without changing the core logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Optional, TypeVar

from ..base.base import BaseDAHState


TState = TypeVar("TState", bound=BaseDAHState[Any])


class BaseStateRepository(ABC, Generic[TState]):
    """Base interface for state repository operations.

    This interface defines the contract for state persistence operations,
    following Interface Segregation Principle (ISP) by focusing only
    on state-related operations.

    Generic over TState, works with any state type
    or custom state implementations.

    Implementations can store state in:
    - Memory (default, for single-session)
    - Database (for persistence)
    - Cache (Redis, etc.)
    - Distributed storage
    """

    @abstractmethod
    async def get(self, state_id: str) -> Optional[TState]:
        """Retrieve state by identifier.

        Args:
            state_id: Unique identifier for the state

        Returns:
            State instance or None if not found
        """
        pass

    @abstractmethod
    async def save(self, state_id: str, state: TState) -> None:
        """Save or update state.

        Args:
            state_id: Unique identifier for the state
            state: State instance to save
        """
        pass

    @abstractmethod
    async def delete(self, state_id: str) -> bool:
        """Delete state by identifier.

        Args:
            state_id: Unique identifier for the state

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, state_id: str) -> bool:
        """Check if state exists.

        Args:
            state_id: Unique identifier for the state

        Returns:
            True if state exists
        """
        pass

    async def get_or_create(
        self, state_id: str, factory: Callable[[], TState]
    ) -> TState:
        """Get existing state or create new one.

        Args:
            state_id: Unique identifier for the state
            factory: Callable to create new state if not found

        Returns:
            Existing or newly created state
        """
        existing = await self.get(state_id)
        if existing is not None:
            return existing

        new_state = factory()
        await self.save(state_id, new_state)
        return new_state
