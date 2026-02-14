from __future__ import annotations

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

class Subject(BaseSubject[E], Generic[E]):
    """Simple subject that manages a list of observers."""

    __slots__ = ("_observers",)

    def __init__(self, observers: List[BaseObserver[E]] | None = None) -> None:
        self._observers: List[BaseObserver[E]] = []
        if observers:
            for observer in observers:
                self.attach(observer)

    @property
    def observers(self) -> Tuple[BaseObserver[E], ...]:
        """Snapshot of attached observers in registration order."""
        return tuple(self._observers)

    def attach(self, observer: BaseObserver[E]) -> None:
        """Attach an observer if it is not already registered."""
        if any(existing is observer for existing in self._observers):
            return
        self._observers.append(observer)

    def detach(self, observer: BaseObserver[E]) -> None:
        """Detach an observer if it is registered."""
        for index, existing in enumerate(self._observers):
            if existing is observer:
                del self._observers[index]
                break

    async def notify(self, event: E) -> List[object]:
        """Notify all observers in registration order."""
        results: List[object] = []
        for observer in tuple(self._observers):
            results.append(await observer.notified(self, event))
        return results
