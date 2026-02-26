"""Tests for LangState orchestrator.

Covers construction via LangStateDeps, initialize, invoke,
reset, projector management, component getters/setters,
and the schema_to_state helper.
"""

# pyright: reportPrivateUsage=false


from pathlib import Path
from typing import List, Optional, Union, cast
from unittest.mock import AsyncMock

import pytest

from core.langstate.base.base import BaseLangState
from core.langstate.base.helpers import schema_to_state
from core.langstate.base.langstate import LangState
from core.langstate.base.schema import (
    AgentInput,
    InteractionType,
    LangStateConfig,
    LangStateDeps,
    StateResultData,
)
from core.mutator.base.base import BaseMutator
from core.mutator.base.schema import MutationResult
from core.projector.base.projector import BaseProjector
from core.projector.base.schema import ProjectionContext, ProjectionResult
from core.spec_extractor.base.extractor import BaseSpecExtractor
from core.spec_extractor.base.schema import Schema, SchemaField
from core.state.repository.snapshot_repository.memory.memory import (
    InMemorySnapshotRepository,
)
from core.state.state.base import BaseState
from core.state.state.schema import ValueConfidence
from core.state.state.state import State


# ── Stub context type ──────────────────────────────────────────────


class StubContext:
    """Minimal context used by tests."""

    def __init__(self, text: str, state: State) -> None:
        self.text = text
        self.state = state


# ── Stub Mutator ───────────────────────────────────────────────────


class StubMutator(BaseMutator[StubContext]):
    """Mutator that sets a ``name`` field on the state."""

    async def mutate(self, context: StubContext) -> MutationResult:
        new_state = context.state.copy()
        new_state.add_value("name", ValueConfidence(value=context.text, confidence=0.9))
        return MutationResult(updated_state=new_state)


# ── Stub Spec Extractor ───────────────────────────────────────────


class StubSpecExtractor(BaseSpecExtractor):
    """Spec extractor that always returns the same two-field schema."""

    def __init__(self, schema: Optional[Schema] = None) -> None:
        self._schema = schema or Schema.model_validate(
            {
                "name": SchemaField(
                    field_id="name",
                    field_type="string",
                    label="Name",
                    required=True,
                ),
                "email": SchemaField(
                    field_id="email",
                    field_type="string",
                    label="Email",
                    required=True,
                ),
            }
        )

    def read(self, source: Union[str, Path]) -> Schema:
        return self._schema


# ── Stub Projector ─────────────────────────────────────────────────


class StubProjector(BaseProjector[ProjectionContext, ProjectionResult]):
    """Projector that records the last context it received."""

    def __init__(self) -> None:
        self.last_context: Optional[ProjectionContext] = None
        self.call_count: int = 0

    async def project(self, context: ProjectionContext) -> ProjectionResult:
        self.last_context = context
        self.call_count += 1
        return ProjectionResult(success=True)

    async def initialize(self, schema: Optional[Schema] = None) -> None:
        pass


# ── Helper factories ───────────────────────────────────────────────


def _context_factory(inp: AgentInput, state: BaseState) -> StubContext:
    return StubContext(text=inp.text or "", state=cast(State, state))


def _make_deps(
    mutator: Optional[BaseMutator[StubContext]] = None,
    spec_extractor: Optional[BaseSpecExtractor] = None,
    projectors: Optional[
        List[BaseProjector[ProjectionContext, ProjectionResult]]
    ] = None,
    repository: Optional[InMemorySnapshotRepository[BaseState]] = None,
) -> LangStateDeps[StubContext, AgentInput]:
    return LangStateDeps(
        mutator=mutator,
        spec_extractor=spec_extractor,
        projectors=projectors,
        repository=repository,
        context_factory=_context_factory,
    )


def _make_schema() -> Schema:
    return Schema.model_validate(
        {
            "name": SchemaField(
                field_id="name",
                field_type="string",
                label="Name",
                required=True,
            ),
            "email": SchemaField(
                field_id="email",
                field_type="string",
                label="Email",
                required=True,
            ),
        }
    )


# ══════════════════════════════════════════════════════════════════
# Tests
# ══════════════════════════════════════════════════════════════════


class TestConstruction:
    """LangState can be constructed from LangStateDeps."""

    def test_minimal_construction(self) -> None:
        deps = _make_deps()
        agent: LangState[StubContext, AgentInput] = LangState(deps)

        assert agent.mutator is None
        assert agent.spec_extractor is None
        assert agent.projectors == []
        assert agent.schema is None

    def test_full_construction(self) -> None:
        mutator = StubMutator()
        extractor = StubSpecExtractor()
        projector = StubProjector()
        repo: InMemorySnapshotRepository[BaseState] = InMemorySnapshotRepository(
            state_class=State
        )
        deps = _make_deps(
            mutator=mutator,
            spec_extractor=extractor,
            projectors=[projector],
            repository=repo,
        )
        agent: LangState[StubContext, AgentInput] = LangState(deps)

        assert agent.mutator is mutator
        assert agent.spec_extractor is extractor
        assert agent.projectors == [projector]
        assert agent.state_repository is repo

    def test_is_instance_of_base(self) -> None:
        agent: LangState[StubContext, AgentInput] = LangState(_make_deps())
        assert isinstance(agent, BaseLangState)


class TestInitialize:
    """initialize loads schema, converts to State, and persists."""

    @pytest.mark.asyncio
    async def test_initialize_with_schema_source(self) -> None:
        extractor = StubSpecExtractor()
        deps = _make_deps(mutator=StubMutator(), spec_extractor=extractor)
        agent: LangState[StubContext, AgentInput] = LangState(deps)

        await agent.initialize({"schema_source": "some/path.yaml"})

        assert agent.schema is not None
        assert "name" in agent.schema.root
        assert "email" in agent.schema.root

        # State should exist in repository
        state = await agent.get_state()
        assert state.get_field("name") is not None
        assert state.get_field("email") is not None

    @pytest.mark.asyncio
    async def test_initialize_uses_get_latest(self) -> None:
        """After initialize the state must be retrievable via get_latest."""
        extractor = StubSpecExtractor()
        repo: InMemorySnapshotRepository[BaseState] = InMemorySnapshotRepository(
            state_class=State
        )
        deps = _make_deps(
            mutator=StubMutator(),
            spec_extractor=extractor,
            repository=repo,
        )
        agent: LangState[StubContext, AgentInput] = LangState(deps)

        await agent.initialize(LangStateConfig(schema_source="path"))

        snapshot = await repo.get_latest("state")
        assert snapshot is not None
        assert snapshot.state.get_field("name") is not None

    @pytest.mark.asyncio
    async def test_initialize_calls_projector_initialize(self) -> None:
        projector = StubProjector()
        projector.initialize = AsyncMock()  # type: ignore[method-assign]
        deps = _make_deps(
            spec_extractor=StubSpecExtractor(),
            projectors=[projector],
        )
        agent: LangState[StubContext, AgentInput] = LangState(deps)

        await agent.initialize({"schema_source": "path"})

        projector.initialize.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_initialize_with_langstate_config_object(self) -> None:
        deps = _make_deps(spec_extractor=StubSpecExtractor())
        agent: LangState[StubContext, AgentInput] = LangState(deps)

        config = LangStateConfig(schema_source="any_path")
        await agent.initialize(config)

        assert agent.schema is not None


class TestInvoke:
    """invoke bridges TInput → TContext → mutator → state → projectors."""

    @pytest.mark.asyncio
    async def test_invoke_calls_mutator_and_returns_result(self) -> None:
        deps = _make_deps(
            mutator=StubMutator(),
            spec_extractor=StubSpecExtractor(),
        )
        agent: LangState[StubContext, AgentInput] = LangState(deps)
        await agent.initialize({"schema_source": "path"})

        result = await agent.invoke(AgentInput.from_text("Alice"))

        assert isinstance(result, StateResultData)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_invoke_persists_updated_state(self) -> None:
        repo: InMemorySnapshotRepository[BaseState] = InMemorySnapshotRepository(
            state_class=State
        )
        deps = _make_deps(
            mutator=StubMutator(),
            spec_extractor=StubSpecExtractor(),
            repository=repo,
        )
        agent: LangState[StubContext, AgentInput] = LangState(deps)
        await agent.initialize({"schema_source": "path"})

        await agent.invoke(AgentInput.from_text("Alice"))

        snapshot = await repo.get_latest("state")
        assert snapshot is not None
        name_field = snapshot.state.get_field("name")
        assert name_field is not None
        assert any(vc.value == "Alice" for vc in name_field.values)

    @pytest.mark.asyncio
    async def test_invoke_notifies_projectors(self) -> None:
        projector = StubProjector()
        deps = _make_deps(
            mutator=StubMutator(),
            spec_extractor=StubSpecExtractor(),
            projectors=[projector],
        )
        agent: LangState[StubContext, AgentInput] = LangState(deps)
        await agent.initialize({"schema_source": "path"})

        await agent.invoke(AgentInput.from_text("Bob"))

        assert projector.call_count >= 1
        assert projector.last_context is not None

    @pytest.mark.asyncio
    async def test_invoke_raises_without_mutator(self) -> None:
        deps = _make_deps(spec_extractor=StubSpecExtractor())
        agent: LangState[StubContext, AgentInput] = LangState(deps)
        await agent.initialize({"schema_source": "path"})

        with pytest.raises(RuntimeError, match="Mutator is not set"):
            await agent.invoke(AgentInput.from_text("test"))


class TestReset:
    """reset clears the state and returns an InteractionRequest."""

    @pytest.mark.asyncio
    async def test_reset_clears_state(self) -> None:
        deps = _make_deps(
            mutator=StubMutator(),
            spec_extractor=StubSpecExtractor(),
        )
        agent: LangState[StubContext, AgentInput] = LangState(deps)
        await agent.initialize({"schema_source": "path"})
        await agent.invoke(AgentInput.from_text("Alice"))

        result = await agent.reset()

        assert result.interaction_type == InteractionType.COMPLETE
        # State should be fresh (no filled fields).
        state = await agent.get_state()
        filled = list(state.get_filled_fields())
        assert len(filled) == 0

    @pytest.mark.asyncio
    async def test_reset_clears_conversation_history(self) -> None:
        deps = _make_deps(
            mutator=StubMutator(),
            spec_extractor=StubSpecExtractor(),
        )
        agent: LangState[StubContext, AgentInput] = LangState(deps)
        await agent.initialize({"schema_source": "path"})
        agent._conversation_history.append({"role": "user", "content": "hi"})

        await agent.reset()

        assert agent.get_conversation_history() == []


class TestComponentManagement:
    """Getters/setters for mutator, spec_extractor, schema, repository."""

    def test_set_mutator(self) -> None:
        agent: LangState[StubContext, AgentInput] = LangState(_make_deps())
        mutator = StubMutator()

        agent.set_mutator(mutator)
        assert agent.mutator is mutator

    def test_set_spec_extractor(self) -> None:
        agent: LangState[StubContext, AgentInput] = LangState(_make_deps())
        ext = StubSpecExtractor()

        agent.set_spec_extractor(ext)
        assert agent.spec_extractor is ext

    def test_set_schema_directly(self) -> None:
        agent: LangState[StubContext, AgentInput] = LangState(_make_deps())
        schema = _make_schema()

        agent.set_schema(schema)
        assert agent.schema is schema

    def test_set_state_repository(self) -> None:
        agent: LangState[StubContext, AgentInput] = LangState(_make_deps())
        repo: InMemorySnapshotRepository[BaseState] = InMemorySnapshotRepository(
            state_class=State
        )

        agent.set_state_repository(repo)
        assert agent.state_repository is repo


class TestProjectorManagement:
    """sub/unsub projectors via add/remove/set/clear."""

    def test_add_and_remove_projector(self) -> None:
        agent: LangState[StubContext, AgentInput] = LangState(_make_deps())
        proj = StubProjector()

        agent.add_projector(proj)
        assert proj in agent.projectors

        agent.remove_projector(proj)
        assert proj not in agent.projectors

    def test_set_projectors_replaces_all(self) -> None:
        p1, p2, p3 = StubProjector(), StubProjector(), StubProjector()
        agent: LangState[StubContext, AgentInput] = LangState(
            _make_deps(projectors=[p1])
        )

        agent.set_projectors([p2, p3])

        assert p1 not in agent.projectors
        assert p2 in agent.projectors
        assert p3 in agent.projectors

    def test_set_projectors_with_single(self) -> None:
        p1 = StubProjector()
        agent: LangState[StubContext, AgentInput] = LangState(_make_deps())

        agent.set_projectors(p1)
        assert agent.projectors == [p1]

    def test_clear_projectors(self) -> None:
        p1, p2 = StubProjector(), StubProjector()
        agent: LangState[StubContext, AgentInput] = LangState(
            _make_deps(projectors=[p1, p2])
        )

        agent.clear_projectors()
        assert agent.projectors == []

    def test_attach_rejects_non_projector(self) -> None:
        agent: LangState[StubContext, AgentInput] = LangState(_make_deps())
        with pytest.raises(TypeError, match="BaseProjector"):
            agent.attach("not a projector")  # type: ignore[arg-type]


class TestSchemaToState:
    """schema_to_state helper correctly converts Schema → State."""

    def test_creates_empty_fields(self) -> None:
        schema = _make_schema()
        state = schema_to_state(schema)

        assert state.get_field("name") is not None
        assert state.get_field("email") is not None
        # Fields should be empty InterpretiveField instances.
        name_field = state.get_field("name")
        assert name_field is not None
        assert len(name_field.values) == 0

    def test_handles_dependencies(self) -> None:
        schema = Schema.model_validate(
            {
                "city": SchemaField(
                    field_id="city",
                    field_type="string",
                    label="City",
                ),
                "country": SchemaField(
                    field_id="country",
                    field_type="string",
                    label="Country",
                    validation_rules={"depends_on": ["city"]},
                ),
            }
        )
        state = schema_to_state(schema)

        children = list(state.get_children("city"))
        assert "country" in children


class TestGetState:
    """get_state uses get_latest on the snapshot repository."""

    @pytest.mark.asyncio
    async def test_get_state_raises_when_empty(self) -> None:
        agent: LangState[StubContext, AgentInput] = LangState(_make_deps())
        with pytest.raises(RuntimeError, match="State not available"):
            await agent.get_state()

    @pytest.mark.asyncio
    async def test_get_state_returns_latest_snapshot(self) -> None:
        deps = _make_deps(
            mutator=StubMutator(),
            spec_extractor=StubSpecExtractor(),
        )
        agent: LangState[StubContext, AgentInput] = LangState(deps)
        await agent.initialize({"schema_source": "path"})

        state = await agent.get_state()
        assert isinstance(state, BaseState)
