"""
Comprehensive unit tests for the Observer pattern implementation.

Tests cover:
- BaseObserver / BaseSubject abstract interfaces (cannot be instantiated directly)
- Subject.__init__  (empty, with initial observer list)
- Subject.observers  (snapshot tuple semantics)
- Subject.attach     (idempotency by identity)
- Subject.detach     (removal by identity, unknown observer is silent)
- Subject.notify     (order, results list, snapshot semantics)
"""

from __future__ import annotations

import pytest
from typing import Generic, List, TypeVar

from core.data_structure.observer.base import BaseObserver, BaseSubject
from core.data_structure.observer.subject import Subject

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

E = TypeVar("E")


class ConcreteObserver(BaseObserver[E], Generic[E]):
    """Test observer that records every notification it receives."""

    def __init__(self, return_value: object = None) -> None:
        self.calls: List[tuple[object, object]] = []
        self._return_value = return_value

    async def notified(self, subject: BaseSubject[E], event: E) -> object:  # type: ignore[override]
        self.calls.append((subject, event))
        return self._return_value


class ErrorObserver(BaseObserver[E], Generic[E]):
    """Test observer whose notified() raises an exception."""

    async def notified(self, subject: BaseSubject[E], event: E) -> object:  # type: ignore[override]
        raise RuntimeError("observer error")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def observer_a() -> ConcreteObserver[str]:
    return ConcreteObserver[str](return_value="a_result")


@pytest.fixture
def observer_b() -> ConcreteObserver[str]:
    return ConcreteObserver[str](return_value="b_result")


@pytest.fixture
def empty_subject() -> Subject[str]:
    return Subject[str]()


# ============================================================================
# Tests for abstract base classes
# ============================================================================


class TestAbstractBaseClasses:
    """Verify that the abstract interfaces cannot be instantiated directly."""

    def test_base_observer_cannot_be_instantiated(self) -> None:
        """BaseObserver is abstract and should raise TypeError on direct instantiation."""
        with pytest.raises(TypeError):
            BaseObserver()  # type: ignore[abstract]

    def test_base_subject_cannot_be_instantiated(self) -> None:
        """BaseSubject is abstract and should raise TypeError on direct instantiation."""
        with pytest.raises(TypeError):
            BaseSubject()  # type: ignore[abstract]


# ============================================================================
# Tests for Subject.__init__
# ============================================================================


class TestSubjectInit:
    """Tests for Subject initialisation."""

    def test_empty_init_has_no_observers(self) -> None:
        """Subject created without arguments should have an empty observer list."""
        subject: Subject[str] = Subject()
        assert subject.observers == ()

    def test_init_with_none_has_no_observers(self) -> None:
        """Subject created with observers=None should have an empty observer list."""
        subject: Subject[str] = Subject(observers=None)
        assert subject.observers == ()

    def test_init_with_observers_list_attaches_all(
        self,
        observer_a: ConcreteObserver[str],
        observer_b: ConcreteObserver[str],
    ) -> None:
        """Subject created with a list of observers should attach all of them."""
        subject: Subject[str] = Subject(observers=[observer_a, observer_b])
        assert observer_a in subject.observers
        assert observer_b in subject.observers
        assert len(subject.observers) == 2

    def test_init_with_single_observer(self, observer_a: ConcreteObserver[str]) -> None:
        """Subject created with a single-element list should contain exactly one observer."""
        subject: Subject[str] = Subject(observers=[observer_a])
        assert len(subject.observers) == 1
        assert subject.observers[0] is observer_a

    def test_init_with_duplicate_observer_attaches_once(
        self, observer_a: ConcreteObserver[str]
    ) -> None:
        """Initialising with the same observer twice should attach it only once."""
        subject: Subject[str] = Subject(observers=[observer_a, observer_a])
        assert len(subject.observers) == 1


# ============================================================================
# Tests for Subject.observers property
# ============================================================================


class TestSubjectObserversProperty:
    """Tests for the observers snapshot property."""

    def test_observers_returns_tuple(
        self, empty_subject: Subject[str], observer_a: ConcreteObserver[str]
    ) -> None:
        """observations property should return a tuple, not a list."""
        empty_subject.attach(observer_a)
        result = empty_subject.observers
        assert isinstance(result, tuple)

    def test_observers_snapshot_does_not_reflect_later_attach(
        self,
        empty_subject: Subject[str],
        observer_a: ConcreteObserver[str],
        observer_b: ConcreteObserver[str],
    ) -> None:
        """Snapshot taken before attach should not include the new observer."""
        empty_subject.attach(observer_a)
        snapshot = empty_subject.observers
        empty_subject.attach(observer_b)
        # The previously captured tuple is a snapshot and stays unchanged
        assert observer_b not in snapshot
        assert len(snapshot) == 1

    def test_observers_is_ordered_by_registration(
        self,
        empty_subject: Subject[str],
        observer_a: ConcreteObserver[str],
        observer_b: ConcreteObserver[str],
    ) -> None:
        """Observers should be returned in registration (FIFO) order."""
        empty_subject.attach(observer_a)
        empty_subject.attach(observer_b)
        assert empty_subject.observers[0] is observer_a
        assert empty_subject.observers[1] is observer_b


# ============================================================================
# Tests for Subject.attach
# ============================================================================


class TestSubjectAttach:
    """Tests for Subject.attach."""

    def test_attach_adds_observer(
        self, empty_subject: Subject[str], observer_a: ConcreteObserver[str]
    ) -> None:
        """Attaching a new observer should make it appear in observers."""
        empty_subject.attach(observer_a)
        assert observer_a in empty_subject.observers

    def test_attach_same_observer_twice_is_noop(
        self, empty_subject: Subject[str], observer_a: ConcreteObserver[str]
    ) -> None:
        """Re-attaching the same observer (by identity) should not duplicate it."""
        empty_subject.attach(observer_a)
        empty_subject.attach(observer_a)
        assert len(empty_subject.observers) == 1

    def test_attach_equal_but_different_instance_is_added(
        self, empty_subject: Subject[str]
    ) -> None:
        """Two distinct observer instances with same type should both be attached."""
        obs1: ConcreteObserver[str] = ConcreteObserver()
        obs2: ConcreteObserver[str] = ConcreteObserver()
        empty_subject.attach(obs1)
        empty_subject.attach(obs2)
        assert len(empty_subject.observers) == 2

    def test_attach_multiple_distinct_observers(
        self,
        empty_subject: Subject[str],
        observer_a: ConcreteObserver[str],
        observer_b: ConcreteObserver[str],
    ) -> None:
        """Attaching two distinct observers should result in two entries."""
        empty_subject.attach(observer_a)
        empty_subject.attach(observer_b)
        observers = empty_subject.observers
        assert observer_a in observers
        assert observer_b in observers
        assert len(observers) == 2


# ============================================================================
# Tests for Subject.detach
# ============================================================================


class TestSubjectDetach:
    """Tests for Subject.detach."""

    def test_detach_removes_observer(
        self, empty_subject: Subject[str], observer_a: ConcreteObserver[str]
    ) -> None:
        """Detaching an attached observer should remove it from observers."""
        empty_subject.attach(observer_a)
        empty_subject.detach(observer_a)
        assert observer_a not in empty_subject.observers

    def test_detach_unknown_observer_is_silent(
        self, empty_subject: Subject[str], observer_a: ConcreteObserver[str]
    ) -> None:
        """Detaching an observer that was never attached should not raise."""
        empty_subject.detach(observer_a)  # Should not raise

    def test_detach_only_removes_first_matching_identity(
        self, empty_subject: Subject[str]
    ) -> None:
        """detach removes only the matched instance, leaving others intact."""
        obs1: ConcreteObserver[str] = ConcreteObserver()
        obs2: ConcreteObserver[str] = ConcreteObserver()
        empty_subject.attach(obs1)
        empty_subject.attach(obs2)
        empty_subject.detach(obs1)
        assert obs1 not in empty_subject.observers
        assert obs2 in empty_subject.observers
        assert len(empty_subject.observers) == 1

    def test_detach_twice_removes_once_then_silent(
        self, empty_subject: Subject[str], observer_a: ConcreteObserver[str]
    ) -> None:
        """Detaching the same observer twice: first succeeds, second is a no-op."""
        empty_subject.attach(observer_a)
        empty_subject.detach(observer_a)
        empty_subject.detach(observer_a)  # Should not raise
        assert observer_a not in empty_subject.observers

    def test_detach_after_empty_init(
        self, empty_subject: Subject[str], observer_a: ConcreteObserver[str]
    ) -> None:
        """Detaching from a freshly created subject should be silent."""
        empty_subject.detach(observer_a)
        assert empty_subject.observers == ()


# ============================================================================
# Tests for Subject.notify
# ============================================================================


class TestSubjectNotify:
    """Tests for Subject.notify."""

    @pytest.mark.asyncio
    async def test_notify_with_no_observers_returns_empty_list(
        self, empty_subject: Subject[str]
    ) -> None:
        """notify when no observers are attached should return an empty list."""
        results = await empty_subject.notify("event")
        assert results == []

    @pytest.mark.asyncio
    async def test_notify_calls_single_observer(
        self,
        empty_subject: Subject[str],
        observer_a: ConcreteObserver[str],
    ) -> None:
        """notify should call notified() on the single attached observer."""
        empty_subject.attach(observer_a)
        await empty_subject.notify("hello")
        assert len(observer_a.calls) == 1

    @pytest.mark.asyncio
    async def test_notify_passes_subject_and_event(
        self,
        empty_subject: Subject[str],
        observer_a: ConcreteObserver[str],
    ) -> None:
        """notify should pass both the subject and the event to the observer."""
        empty_subject.attach(observer_a)
        event = "my_event"
        await empty_subject.notify(event)
        received_subject, received_event = observer_a.calls[0]
        assert received_subject is empty_subject
        assert received_event == event

    @pytest.mark.asyncio
    async def test_notify_returns_list_of_observer_results(
        self,
        empty_subject: Subject[str],
        observer_a: ConcreteObserver[str],
        observer_b: ConcreteObserver[str],
    ) -> None:
        """notify should accumulate and return every observer's return value."""
        empty_subject.attach(observer_a)
        empty_subject.attach(observer_b)
        results = await empty_subject.notify("evt")
        assert results == ["a_result", "b_result"]

    @pytest.mark.asyncio
    async def test_notify_order_matches_registration_order(
        self,
        empty_subject: Subject[str],
        observer_a: ConcreteObserver[str],
        observer_b: ConcreteObserver[str],
    ) -> None:
        """notify should call observers in registration (FIFO) order."""
        order: List[str] = []
        obs1: ConcreteObserver[str] = ConcreteObserver(return_value="first")
        obs2: ConcreteObserver[str] = ConcreteObserver(return_value="second")

        async def record_a(subject: BaseSubject[str], event: str) -> object:  # type: ignore[override]
            order.append("a")
            return "first"

        async def record_b(subject: BaseSubject[str], event: str) -> object:  # type: ignore[override]
            order.append("b")
            return "second"

        obs1.notified = record_a  # type: ignore[method-assign]
        obs2.notified = record_b  # type: ignore[method-assign]

        empty_subject.attach(obs1)
        empty_subject.attach(obs2)
        await empty_subject.notify("e")
        assert order == ["a", "b"]

    @pytest.mark.asyncio
    async def test_notify_multiple_events_accumulate_calls(
        self,
        empty_subject: Subject[str],
        observer_a: ConcreteObserver[str],
    ) -> None:
        """Each notify call should independently call all observers."""
        empty_subject.attach(observer_a)
        await empty_subject.notify("event1")
        await empty_subject.notify("event2")
        assert len(observer_a.calls) == 2
        assert observer_a.calls[0][1] == "event1"
        assert observer_a.calls[1][1] == "event2"

    @pytest.mark.asyncio
    async def test_notify_uses_snapshot_not_live_list(
        self,
        empty_subject: Subject[str],
        observer_a: ConcreteObserver[str],
        observer_b: ConcreteObserver[str],
    ) -> None:
        """If an observer detaches itself during notify, remaining calls proceed normally."""

        class SelfDetachingObserver(BaseObserver[str]):
            def __init__(self, subject: Subject[str]) -> None:
                self._subject = subject
                self.called = False

            async def notified(self, subject: BaseSubject[str], event: str) -> object:
                self.called = True
                self._subject.detach(self)
                return "detached"

        self_detacher: SelfDetachingObserver = SelfDetachingObserver(empty_subject)
        empty_subject.attach(self_detacher)
        empty_subject.attach(observer_b)

        # Should complete without error even though the first observer detaches itself
        results = await empty_subject.notify("e")
        assert self_detacher.called is True
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_notify_propagates_observer_exception(
        self, empty_subject: Subject[str]
    ) -> None:
        """If an observer raises inside notified(), the exception should propagate."""
        err_obs: ErrorObserver[str] = ErrorObserver[str]()
        empty_subject.attach(err_obs)
        with pytest.raises(RuntimeError, match="observer error"):
            await empty_subject.notify("event")

    @pytest.mark.asyncio
    async def test_notify_with_non_string_event(self) -> None:
        """Subject should work with any event type, including integers."""
        subject: Subject[int] = Subject[int]()
        obs: ConcreteObserver[int] = ConcreteObserver[int](return_value=42)
        subject.attach(obs)
        results = await subject.notify(99)
        assert results == [42]
        assert obs.calls[0][1] == 99
