"""Unit tests for State Repository implementations.

Tests the IStateRepository interface and InMemoryStateRepository implementation.
"""

import pytest

from core.state.canonical.state import CanonicalState
from core.state.interpretive.schema import ValueConfidence
from core.state.interpretive.state import InterpretiveState
from core.state.repository.memory import (
    InMemoryCanonicalStateRepository,
    InMemoryInterpretiveStateRepository,
    InMemoryStateRepository,
)


class TestInMemoryStateRepository:
    """Tests for InMemoryStateRepository base implementation."""

    @pytest.fixture
    def repository(self) -> InMemoryStateRepository[CanonicalState]:
        """Create a fresh repository for each test."""
        return InMemoryStateRepository[CanonicalState]()

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """get should return None for non-existent state_id."""
        result = await repository.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_get(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """save and get should work together."""
        state = CanonicalState()
        state.set_field("name", "John")

        await repository.save("test_id", state)
        result = await repository.get("test_id")

        assert result is not None
        assert result.get_field("name") == "John"

    @pytest.mark.asyncio
    async def test_save_overwrites_existing(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """save should overwrite existing state."""
        state1 = CanonicalState()
        state1.set_field("name", "John")
        state2 = CanonicalState()
        state2.set_field("name", "Jane")

        await repository.save("test_id", state1)
        await repository.save("test_id", state2)
        result = await repository.get("test_id")

        assert result is not None
        assert result.get_field("name") == "Jane"

    @pytest.mark.asyncio
    async def test_delete_existing(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """delete should remove existing state and return True."""
        state = CanonicalState()
        await repository.save("test_id", state)

        result = await repository.delete("test_id")

        assert result is True
        assert await repository.get("test_id") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """delete should return False for non-existent state_id."""
        result = await repository.delete("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """exists should return True for existing state."""
        state = CanonicalState()
        await repository.save("test_id", state)

        result = await repository.exists("test_id")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """exists should return False for non-existent state."""
        result = await repository.exists("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_clear(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """clear should remove all states."""
        state1 = CanonicalState()
        state2 = CanonicalState()
        await repository.save("id1", state1)
        await repository.save("id2", state2)

        repository.clear()

        assert await repository.get("id1") is None
        assert await repository.get("id2") is None

    @pytest.mark.asyncio
    async def test_get_or_create_existing(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """get_or_create should return existing state."""
        existing = CanonicalState()
        existing.set_field("source", "existing")
        await repository.save("test_id", existing)

        def factory() -> CanonicalState:
            new = CanonicalState()
            new.set_field("source", "factory")
            return new

        result = await repository.get_or_create("test_id", factory)

        assert result.get_field("source") == "existing"

    @pytest.mark.asyncio
    async def test_get_or_create_new(
        self, repository: InMemoryStateRepository[CanonicalState]
    ) -> None:
        """get_or_create should create and save new state."""

        def factory() -> CanonicalState:
            state = CanonicalState()
            state.set_field("source", "factory")
            return state

        result = await repository.get_or_create("new_id", factory)

        assert result.get_field("source") == "factory"
        # Should also be saved
        saved = await repository.get("new_id")
        assert saved is not None
        assert saved.get_field("source") == "factory"


class TestInMemoryCanonicalStateRepository:
    """Tests for InMemoryCanonicalStateRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryCanonicalStateRepository:
        """Create a fresh repository for each test."""
        return InMemoryCanonicalStateRepository()

    @pytest.mark.asyncio
    async def test_save_and_get_canonical_state(
        self, repository: InMemoryCanonicalStateRepository
    ) -> None:
        """Should work with CanonicalState."""
        state = CanonicalState()
        state.set_field("name", "John")
        state.set_field("age", 30)

        await repository.save("canonical_1", state)
        result = await repository.get("canonical_1")

        assert result is not None
        assert result.get_field("name") == "John"
        assert result.get_field("age") == 30

    @pytest.mark.asyncio
    async def test_multiple_states(
        self, repository: InMemoryCanonicalStateRepository
    ) -> None:
        """Should handle multiple states."""
        state1 = CanonicalState()
        state1.set_field("id", "1")
        state2 = CanonicalState()
        state2.set_field("id", "2")

        await repository.save("state_1", state1)
        await repository.save("state_2", state2)

        result1 = await repository.get("state_1")
        result2 = await repository.get("state_2")

        assert result1 is not None
        assert result1.get_field("id") == "1"
        assert result2 is not None
        assert result2.get_field("id") == "2"


class TestInMemoryInterpretiveStateRepository:
    """Tests for InMemoryInterpretiveStateRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryInterpretiveStateRepository:
        """Create a fresh repository for each test."""
        return InMemoryInterpretiveStateRepository()

    @pytest.mark.asyncio
    async def test_save_and_get_interpretive_state(
        self, repository: InMemoryInterpretiveStateRepository
    ) -> None:
        """Should work with InterpretiveState."""
        state = InterpretiveState()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        await repository.save("interpretive_1", state)
        result = await repository.get("interpretive_1")

        assert result is not None
        best = result.get_best_value("name")
        assert best is not None
        assert best.value == "John"
        assert best.confidence == 0.9

    @pytest.mark.asyncio
    async def test_delete_and_exists(
        self, repository: InMemoryInterpretiveStateRepository
    ) -> None:
        """delete and exists should work correctly."""
        state = InterpretiveState()
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
        repository: InMemoryStateRepository[CanonicalState] = InMemoryStateRepository()
        state = CanonicalState()

        await repository.save("", state)
        result = await repository.get("")

        assert result is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_state_id(self) -> None:
        """Should handle special characters in state_id."""
        repository: InMemoryStateRepository[CanonicalState] = InMemoryStateRepository()
        state = CanonicalState()

        special_id = "state/with:special@chars#!"
        await repository.save(special_id, state)
        result = await repository.get(special_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_operations_sequence(self) -> None:
        """Should handle sequence of operations correctly."""
        repository: InMemoryStateRepository[CanonicalState] = InMemoryStateRepository()

        # Save
        state1 = CanonicalState()
        state1.set_field("version", "1")
        await repository.save("id", state1)

        # Update
        state2 = CanonicalState()
        state2.set_field("version", "2")
        await repository.save("id", state2)

        # Verify
        result = await repository.get("id")
        assert result is not None
        assert result.get_field("version") == "2"

        # Delete
        assert await repository.delete("id") is True

        # Verify deleted
        assert await repository.get("id") is None
        assert await repository.exists("id") is False
