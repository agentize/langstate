from core.data_structure.observer.base import BaseObserver, BaseSubject, E


from typing import Generic, List, Tuple


class Subject(BaseSubject[E], Generic[E]):
    """Simple subject that manages a list of observers."""

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
