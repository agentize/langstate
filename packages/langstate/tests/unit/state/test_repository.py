"""Unit tests for State Repository implementations.

Tests the BaseStateRepository interface and InMemoryStateRepository implementation.
"""

import pytest

from core.state.state.base import BaseState
from core.state.state.state import State
from core.state.state.schema import ValueConfidence
from core.state.repository.memory import InMemoryStateRepository


class TestInMemoryStateRepository:
    """Tests for InMemoryStateRepository base implementation."""

    @pytest.fixture
    def repository(self) -> InMemoryStateRepository[State]:
        """Create a fresh repository for each test."""
        return InMemoryStateRepository[State]()

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(
        self, repository: InMemoryStateRepository[State]
    ) -> None:
        """get should return None for non-existent state_id."""
        result = await repository.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_get(
        self, repository: InMemoryStateRepository[State]
    ) -> None:
        """save and get should work together."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        await repository.save("test_id", state)
        result = await repository.get("test_id")

        assert result is not None
        best = result.get_best_value("name")
        assert best is not None
        assert best.value == "John"

    @pytest.mark.asyncio
    async def test_save_overwrites_existing(
        self, repository: InMemoryStateRepository[State]
    ) -> None:
        """save should overwrite existing state."""
        state1 = State()
        state1.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state2 = State()
        state2.add_value("name", ValueConfidence(value="Jane", confidence=0.9))

        await repository.save("test_id", state1)
        await repository.save("test_id", state2)
        result = await repository.get("test_id")

        assert result is not None
        best = result.get_best_value("name")
        assert best is not None
        assert best.value == "Jane"

    @pytest.mark.asyncio
    async def test_delete_existing(
        self, repository: InMemoryStateRepository[State]
    ) -> None:
        """delete should remove existing state and return True."""
        state = State()
        await repository.save("test_id", state)

        result = await repository.delete("test_id")

        assert result is True
        assert await repository.get("test_id") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(
        self, repository: InMemoryStateRepository[State]
    ) -> None:
        """delete should return False for non-existent state_id."""
        result = await repository.delete("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(
        self, repository: InMemoryStateRepository[State]
    ) -> None:
        """exists should return True for existing state."""
        state = State()
        await repository.save("test_id", state)

        result = await repository.exists("test_id")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(
        self, repository: InMemoryStateRepository[State]
    ) -> None:
        """exists should return False for non-existent state."""
        result = await repository.exists("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, repository: InMemoryStateRepository[State]) -> None:
        """clear should remove all states."""
        state1 = State()
        state2 = State()
        await repository.save("id1", state1)
        await repository.save("id2", state2)

        repository.clear()

        assert await repository.get("id1") is None
        assert await repository.get("id2") is None

    @pytest.mark.asyncio
    async def test_get_or_create_existing(
        self, repository: InMemoryStateRepository[State]
    ) -> None:
        """get_or_create should return existing state."""
        existing = State()
        existing.add_value("source", ValueConfidence(value="existing", confidence=0.9))
        await repository.save("test_id", existing)

        def factory() -> State:
            new = State()
            new.add_value("source", ValueConfidence(value="factory", confidence=0.9))
            return new

        result = await repository.get_or_create("test_id", factory)

        best = result.get_best_value("source")
        assert best is not None
        assert best.value == "existing"

    @pytest.mark.asyncio
    async def test_get_or_create_new(
        self, repository: InMemoryStateRepository[State]
    ) -> None:
        """get_or_create should create and save new state."""

        def factory() -> State:
            state = State()
            state.add_value("source", ValueConfidence(value="factory", confidence=0.9))
            return state

        result = await repository.get_or_create("new_id", factory)

        best = result.get_best_value("source")
        assert best is not None
        assert best.value == "factory"
        # Should also be saved
        saved = await repository.get("new_id")
        assert saved is not None
        best_saved = saved.get_best_value("source")
        assert best_saved is not None
        assert best_saved.value == "factory"


class TestInMemoryStateRepositoryWithBaseState:
    """Tests for InMemoryStateRepository with BaseState."""

    @pytest.fixture
    def repository(self) -> InMemoryStateRepository[BaseState]:
        """Create a fresh repository for each test."""
        return InMemoryStateRepository[BaseState]()

    @pytest.mark.asyncio
    async def test_save_and_get_state(
        self, repository: InMemoryStateRepository[BaseState]
    ) -> None:
        """Should work with State."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))
        state.add_value("age", ValueConfidence(value=30, confidence=0.85))

        await repository.save("state_1", state)
        result = await repository.get("state_1")

        assert result is not None
        best_name = result.get_best_value("name")
        assert best_name is not None
        assert best_name.value == "John"

    @pytest.mark.asyncio
    async def test_multiple_states(
        self, repository: InMemoryStateRepository[BaseState]
    ) -> None:
        """Should handle multiple states."""
        state1 = State()
        state1.add_value("id", ValueConfidence(value="1", confidence=0.9))
        state2 = State()
        state2.add_value("id", ValueConfidence(value="2", confidence=0.9))

        await repository.save("state_1", state1)
        await repository.save("state_2", state2)

        result1 = await repository.get("state_1")
        result2 = await repository.get("state_2")

        assert result1 is not None
        best1 = result1.get_best_value("id")
        assert best1 is not None
        assert best1.value == "1"
        assert result2 is not None
        best2 = result2.get_best_value("id")
        assert best2 is not None
        assert best2.value == "2"


class TestInMemoryStateRepositoryVariant:
    """Tests for InMemoryStateRepository with State (additional)."""

    @pytest.fixture
    def repository(self) -> InMemoryStateRepository[BaseState]:
        """Create a fresh repository for each test."""
        return InMemoryStateRepository[BaseState]()

    @pytest.mark.asyncio
    async def test_save_and_get_state_with_values(
        self, repository: InMemoryStateRepository[BaseState]
    ) -> None:
        """Should work with State."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        await repository.save("state_1", state)
        result = await repository.get("state_1")

        assert result is not None
        best = result.get_best_value("name")
        assert best is not None
        assert best.value == "John"
        assert best.confidence == 0.9

    @pytest.mark.asyncio
    async def test_delete_and_exists(
        self, repository: InMemoryStateRepository[BaseState]
    ) -> None:
        """delete and exists should work correctly."""
        state = State()
        await repository.save("test_id", state)

        assert await repository.exists("test_id") is True

        deleted = await repository.delete("test_id")

        assert deleted is True
        assert await repository.exists("test_id") is False


class TestRepositoryEdgeCases:
    """Tests for edge cases in repository implementations."""

    @pytest.mark.asyncio
    async def test_empty_state_id(self) -> None:
        """Should handle empty state_id."""
        repository: InMemoryStateRepository[State] = InMemoryStateRepository()
        state = State()

        await repository.save("", state)
        result = await repository.get("")

        assert result is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_state_id(self) -> None:
        """Should handle special characters in state_id."""
        repository: InMemoryStateRepository[State] = InMemoryStateRepository()
        state = State()

        special_id = "state/with:special@chars#!"
        await repository.save(special_id, state)
        result = await repository.get(special_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_operations_sequence(self) -> None:
        """Should handle sequence of operations correctly."""
        repository: InMemoryStateRepository[State] = InMemoryStateRepository()

        # Save
        state1 = State()
        state1.add_value("version", ValueConfidence(value="1", confidence=0.9))
        await repository.save("id", state1)

        # Update
        state2 = State()
        state2.add_value("version", ValueConfidence(value="2", confidence=0.9))
        await repository.save("id", state2)

        # Verify
        result = await repository.get("id")
        assert result is not None
        best = result.get_best_value("version")
        assert best is not None
        assert best.value == "2"

        # Delete
        assert await repository.delete("id") is True

        # Verify deleted
        assert await repository.get("id") is None
        assert await repository.exists("id") is False
