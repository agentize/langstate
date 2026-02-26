"""Concrete LangState orchestrator.

Coordinates schema loading, state persistence via snapshots,
mutation, and projector notification using the observer pattern.
"""

from typing import Callable, Dict, Generic, List, Optional, Union, cast

from ...data_structure.observer.subject import Subject

from ...data_structure.observer.base import BaseObserver
from ...mutator.base.base import BaseMutator, TContext
from ...projector.base.projector import BaseProjector
from ...projector.base.schema import ProjectionContext, ProjectionResult
from ...spec_extractor.base.extractor import BaseSpecExtractor
from ...spec_extractor.base.schema import Schema
from ...state.repository.snapshot_repository.base.base import BaseSnapshotRepository
from ...state.repository.snapshot_repository.memory.memory import (
    InMemorySnapshotRepository,
)
from ...state.state.base import BaseState
from ...state.state.state import State
from ...typing.generic import TInput
from .base import BaseLangState
from .helpers import schema_to_state
from .schema import (
    InteractionRequest,
    InteractionType,
    LangStateConfig,
    LangStateDeps,
    StateResultData,
)


class LangState(
    BaseLangState[TContext, TInput],
    Subject[ProjectionContext],
    Generic[TContext, TInput],
):
    """Concrete LangState orchestrator.

    Accepts a :class:`LangStateDeps` bundle at construction time.
    State is stored and versioned through a
    :class:`BaseSnapshotRepository`.

    Type Parameters:
        TContext: Mutation context expected by the mutator.
        TInput:   External input type accepted by ``invoke``.
    """

    def __init__(self, deps: LangStateDeps[TContext, TInput]) -> None:
        self._spec_extractor = deps.spec_extractor
        self._mutator = deps.mutator
        self._context_factory: Callable[[TInput, BaseState], TContext] = (
            deps.context_factory
        )

        initial_projectors: List[BaseProjector[ProjectionContext, ProjectionResult]] = (
            deps.projectors if deps.projectors is not None else []
        )

        self._observers: List[BaseObserver[ProjectionContext]] = []
        for proj in initial_projectors:
            self._observers.append(proj)

        self._schema: Optional[Schema] = None
        self._conversation_history: List[Dict[str, str]] = []

        self._state_repository: BaseSnapshotRepository[BaseState] = (
            deps.repository
            if deps.repository is not None
            else InMemorySnapshotRepository(state_class=State)
        )
        self._state_id: str = "state"

    async def initialize(
        self, config: Union[LangStateConfig, Dict[str, object]]
    ) -> None:
        if isinstance(config, dict):
            config = LangStateConfig.model_validate(config)

        # 1. Load schema via spec extractor
        if config.schema_source is not None and self._spec_extractor is not None:
            self._schema = self._spec_extractor.read(config.schema_source)

        # 2. Convert Schema → State and persist the initial snapshot
        if self._schema is not None:
            initial_state: BaseState = schema_to_state(self._schema)
            await self._state_repository.save(self._state_id, initial_state)

        # 3. Initialize all projectors
        for proj in self.projectors:
            await proj.initialize(self._schema)

    async def invoke(
        self,
        agent_input: Optional[TInput] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> Union[InteractionRequest, StateResultData]:
        if self._mutator is None:
            raise RuntimeError("Mutator is not set.")
        if agent_input is None:
            raise ValueError("agent_input is required.")

        current_state = await self.get_state()

        # Bridge TInput → TContext using the caller-supplied factory.
        context = self._context_factory(agent_input, current_state)
        mutation_result = await self._mutator.mutate(context)

        # Persist updated state and notify projectors.
        projection_results = await self._set_state(
            mutation_result.updated_state, metadata
        )

        return StateResultData(
            state=mutation_result.updated_state,
            success=True,
            metadata={
                "mutation_metadata": mutation_result.metadata or {},
                "projection_results": [r.model_dump() for r in projection_results],
            },
        )

    async def reset(self) -> InteractionRequest:
        await self._state_repository.delete(self._state_id)

        # Re-create empty state from schema if available.
        if self._schema is not None:
            initial_state: BaseState = schema_to_state(self._schema)
            await self._state_repository.save(self._state_id, initial_state)

        self._conversation_history.clear()

        return InteractionRequest(
            interaction_type=InteractionType.COMPLETE,
            prompt="State has been reset.",
        )

    async def get_state(self) -> BaseState:
        latest = await self._state_repository.get_latest(self._state_id)
        if latest is None:
            raise RuntimeError("State not available in repository.")
        return latest.state

    @property
    def spec_extractor(self) -> Optional[BaseSpecExtractor]:
        return self._spec_extractor

    @property
    def mutator(self) -> Optional[BaseMutator[TContext]]:
        return self._mutator

    @property
    def projectors(
        self,
    ) -> List[BaseProjector[ProjectionContext, ProjectionResult]]:
        return cast(
            List[BaseProjector[ProjectionContext, ProjectionResult]],
            list(self.observers),
        )

    @property
    def schema(self) -> Optional[Schema]:
        return self._schema

    @property
    def state_repository(self) -> BaseSnapshotRepository[BaseState]:
        return self._state_repository

    def set_spec_extractor(self, spec_extractor: BaseSpecExtractor) -> None:
        self._spec_extractor = spec_extractor

    def set_mutator(self, mutator: BaseMutator[TContext]) -> None:
        self._mutator = mutator

    def set_schema(self, schema: Schema) -> None:
        self._schema = schema

    def set_state_repository(
        self, repository: BaseSnapshotRepository[BaseState]
    ) -> None:
        self._state_repository = repository

    def attach(  # type: ignore[override]
        self,
        observer: BaseObserver[ProjectionContext],
    ) -> None:
        if not isinstance(observer, BaseProjector):
            raise TypeError("LangState observers must be BaseProjector instances.")
        super().attach(cast(BaseObserver[ProjectionContext], observer))

    def detach(  # type: ignore[override]
        self,
        observer: BaseProjector[ProjectionContext, ProjectionResult],
    ) -> None:
        super().detach(observer)

    def set_projectors(
        self,
        projectors: Union[
            BaseProjector[ProjectionContext, ProjectionResult],
            List[BaseProjector[ProjectionContext, ProjectionResult]],
        ],
    ) -> None:
        self.clear_projectors()
        if isinstance(projectors, list):
            for projector in projectors:
                self.attach(projector)
        else:
            self.attach(projectors)

    def add_projector(
        self, projector: BaseProjector[ProjectionContext, ProjectionResult]
    ) -> None:
        self.attach(projector)

    def remove_projector(
        self, projector: BaseProjector[ProjectionContext, ProjectionResult]
    ) -> None:
        self.detach(projector)

    def clear_projectors(self) -> None:
        for projector in tuple(self.projectors):
            self.detach(projector)

    def get_conversation_history(self) -> List[Dict[str, str]]:
        return self._conversation_history

    async def _set_state(
        self,
        state: BaseState,
        metadata: Optional[Dict[str, object]] = None,
    ) -> List[ProjectionResult]:
        await self._state_repository.save(self._state_id, state)
        return await self._notify_projectors(metadata)

    async def _notify_projectors(
        self, metadata: Optional[Dict[str, object]] = None
    ) -> List[ProjectionResult]:
        if not self.projectors:
            return []

        latest = await self._state_repository.get_latest(self._state_id)
        if latest is None:
            return []

        current_state = latest.state

        context = ProjectionContext(
            state=current_state,
            conversation_history=self._conversation_history,
            metadata=metadata or {},
        )

        notified_results = await self.notify(context)
        return [
            result
            for result in notified_results
            if isinstance(result, ProjectionResult)
        ]
