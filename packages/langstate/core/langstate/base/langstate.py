"""Main LangState orchestrator.

LangState coordinates schema loading, state persistence, mutation, and projector
notification using the observer pattern.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, cast
from typing import Callable, Dict, Generic, List, Optional, Union

from ...mutator.base.base import TContext

from ...data_structure.observer.base import Subject
from ...mutator import BaseMutator
from ...projector import BaseProjector, ProjectionContext, ProjectionResult
from ...spec_extractor import BaseSpecExtractor, Schema
from ...state import BaseState, StateSchema
from ...state.repository import BaseStateRepository, InMemoryStateRepository
from .schema import (
    AgentInput,
    InteractionRequest,
    LangStateConfig,
    StateResultData,
)


class LangState(ABC, Generic[TContext]):
    """Abstract base class for the main LangState orchestrator (Agent).

    LangState is intentionally state-type agnostic at the top level:
    it manages one current state object and notifies all projector observers
    whenever that state changes.
    """

    def __init__(
        self,
        spec_extractor: Optional[BaseSpecExtractor] = None,
        mutator: Optional[BaseMutator] = None,
        projectors: Optional[Union[BaseProjector, List[BaseProjector]]] = None,
    ) -> None:
        """Initialize LangState with optional components."""
        self._spec_extractor = spec_extractor
        self._mutator = mutator

        if projectors is None:
            initial_projectors: List[BaseProjector] = []
        elif isinstance(projectors, list):
            initial_projectors = projectors
        else:
            initial_projectors = [projectors]
        Subject.__init__(self, observers=initial_projectors)

        self._schema: Optional[Schema] = None
        self._conversation_history: List[Dict[str, str]] = []
        self._state_repository: BaseStateRepository[BaseState] = (
            InMemoryStateRepository()
        )
        self._state_id = "state"

    @abstractmethod
    async def initialize(self, config: LangStateConfig) -> None:
        """Initialize LangState with configuration."""
        pass

    @abstractmethod
    async def invoke(
        self,
        agent_input: Optional[AgentInput] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> Union[InteractionRequest, StateResultData]:
        """Invoke the orchestrator with structured input."""
        pass

    async def get_state(self) -> BaseState:
        """Get the current state."""
        state = await self._state_repository.get(self._state_id)
        if state is None or not isinstance(state, BaseState):
            raise RuntimeError("State not available in repository.")
        return state

    def set_spec_extractor(self, spec_extractor: BaseSpecExtractor) -> None:
        """Set a custom SpecExtractor implementation."""
        self._spec_extractor = spec_extractor

    def remove_spec_extractor(self) -> None:
        """Remove the current spec extractor."""
        self._spec_extractor = None

    def set_schema(self, schema: Schema) -> None:
        """Set the schema directly."""
        self._schema = schema

    def set_mutator(self, mutator: BaseMutator[TContext]) -> None:
        """Set a custom Mutator implementation.

        Args:
            mutator: Custom Mutator instance
        """
        self._mutator = mutator

    def remove_mutator(self) -> None:
        """Remove the current mutator."""
        self._mutator = None

    def attach(self, observer: BaseProjector) -> None:  # type: ignore[override]
        """Attach a projector observer."""
        if not isinstance(observer, BaseProjector):
            raise TypeError("LangState observers must be BaseProjector instances.")
        super().attach(observer)

    def detach(self, observer: BaseProjector) -> None:  # type: ignore[override]
        """Detach a projector observer."""
        super().detach(observer)

    def set_projectors(self, projectors: Union[BaseProjector, List[BaseProjector]]) -> None:
        """Set projector(s), replacing existing projectors."""
        self.clear_projectors()
        if isinstance(projectors, list):
            for projector in projectors:
                self.attach(projector)
        else:
            self.attach(projectors)

    def add_projector(self, projector: BaseProjector) -> None:
        """Add a projector to the list of projectors."""
        self.attach(projector)

    def remove_projector(self, projector: BaseProjector) -> None:
        """Remove a projector from the list of projectors."""
        self.detach(projector)

    def clear_projectors(self) -> None:
        """Remove all projectors."""
        for projector in tuple(self.projectors):
            self.detach(projector)

    @abstractmethod
    async def reset(self) -> InteractionRequest:
        """Reset the state and start over."""
        pass

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self._conversation_history

    @property
    def spec_extractor(self) -> Optional[BaseSpecExtractor]:
        """Get the current spec extractor."""
        return self._spec_extractor

    @property
    def mutator(self) -> Optional[BaseMutator[TContext]]:
        """Get the current mutator."""
        return self._mutator

    @property
    def projectors(self) -> List[BaseProjector]:
        """Get the list of current projectors."""
        return cast(List[BaseProjector], list(self.observers))

    @property
    def schema(self) -> Optional[Schema]:
        """Get the current schema."""
        return self._schema

    @property
    def state_repository(self) -> BaseStateRepository[BaseState]:
        """Get the state repository."""
        return self._state_repository

    def set_state_repository(
        self, repository: BaseStateRepository[BaseState]
    ) -> None:
        """Set a custom state repository."""
        self._state_repository = repository

    async def _set_state(
        self,
        state: BaseState,
        metadata: Optional[Dict[str, object]] = None,
    ) -> List[ProjectionResult]:
        """Save current state and notify projectors."""
        await self._state_repository.save(self._state_id, state)
        return await self._notify_projectors(metadata)

    async def _notify_projectors(
        self, metadata: Optional[Dict[str, object]] = None
    ) -> List[ProjectionResult]:
        """Notify all projectors via observer protocol."""
        if not self.projectors:
            return []

        current_state = await self._state_repository.get(self._state_id)
        if current_state is None or not isinstance(current_state, BaseState):
            return []

        state_values = {
            path: value for path, value in current_state.iter_fields() if value is not None
        }
        context = ProjectionContext(
            state=StateSchema.model_validate(state_values),
            conversation_history=self._conversation_history,
            metadata=metadata or {},
        )

        notified_results = await self.notify(context)
        return [
            result for result in notified_results if isinstance(result, ProjectionResult)
        ]
