"""
Abstract base classes for a generic observer pattern.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Tuple, TypeVar

E = TypeVar("E")  # Event payload type


class BaseObserver(Generic[E], ABC):
    """Interface for observers that react to subject notifications."""

    @abstractmethod
    async def notified(self, subject: "BaseSubject[E]", event: E) -> object:
        """Receive a notification from a subject."""
        pass


class BaseSubject(Generic[E], ABC):
    """Interface for subjects that manage observers and emit events."""

    @property
    @abstractmethod
    def observers(self) -> Tuple[BaseObserver[E], ...]:
        """Read-only snapshot of currently attached observers."""
        pass

    @abstractmethod
    def attach(self, observer: BaseObserver[E]) -> None:
        """Attach an observer to this subject."""
        pass

    @abstractmethod
    def detach(self, observer: BaseObserver[E]) -> None:
        """Detach an observer from this subject."""
        pass

    @abstractmethod
    async def notify(self, event: E) -> List[object]:
        """Notify all observers about an event."""
        pass
