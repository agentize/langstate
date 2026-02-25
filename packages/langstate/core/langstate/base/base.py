"""Abstract base class for the LangState orchestrator.

Defines the public interface that all LangState implementations must satisfy.
"""

from abc import abstractmethod
from typing import Dict, Generic, List, Optional, Union

from ...data_structure.observer.base import BaseSubject
from ...mutator.base.base import BaseMutator, TContext
from ...projector.base.projector import BaseProjector
from ...projector.base.schema import ProjectionContext, ProjectionResult
from ...spec_extractor.base.extractor import BaseSpecExtractor
from ...spec_extractor.base.schema import Schema
from ...state.repository.snapshot_repository.base.base import BaseSnapshotRepository
from ...state.state.base import BaseState
from ...typing.generic import TInput
from .schema import (
    InteractionRequest,
    LangStateConfig,
    StateResultData,
)


class BaseLangState(
    BaseSubject[ProjectionContext],
    Generic[TContext, TInput],
):
    """Abstract base for the LangState orchestrator.

    Type Parameters:
        TContext: The mutation context type consumed by the mutator.
        TInput:   The external input type accepted by ``invoke``.

    Implementations must:
    - Accept dependencies via constructor (mutator, spec_extractor, projectors,
      repository, context_factory).
    - Store and retrieve state through a ``BaseSnapshotRepository``.
    - Notify projectors whenever the state changes.
    """

    @abstractmethod
    async def initialize(
        self, config: Union[LangStateConfig, Dict[str, object]]
    ) -> None:
        """Load a schema, build initial state, and persist it."""

    @abstractmethod
    async def invoke(
        self,
        agent_input: Optional[TInput] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> Union[InteractionRequest, StateResultData]:
        """Process external input going through mutator → state → projectors."""

    @abstractmethod
    async def reset(self) -> InteractionRequest:
        """Drop the current state and re-create an empty one."""

    @abstractmethod
    async def get_state(self) -> BaseState:
        """Return the current state from the repository."""

    @property
    @abstractmethod
    def spec_extractor(self) -> Optional[BaseSpecExtractor]:
        """Return the current spec extractor (may be ``None``)."""

    @property
    @abstractmethod
    def mutator(self) -> Optional[BaseMutator[TContext]]:
        """Return the current mutator (may be ``None``)."""

    @property
    @abstractmethod
    def projectors(self) -> List[BaseProjector[ProjectionContext, ProjectionResult]]:
        """Return a list of currently attached projectors."""

    @property
    @abstractmethod
    def schema(self) -> Optional[Schema]:
        """Return the loaded schema (may be ``None`` before ``initialize``)."""

    @property
    @abstractmethod
    def state_repository(self) -> BaseSnapshotRepository[BaseState]:
        """Return the snapshot repository backing this instance."""

    @abstractmethod
    def set_spec_extractor(self, spec_extractor: BaseSpecExtractor) -> None:
        """Replace the spec extractor."""

    @abstractmethod
    def remove_spec_extractor(self) -> None:
        """Remove the current spec extractor."""

    @abstractmethod
    def set_mutator(self, mutator: BaseMutator[TContext]) -> None:
        """Replace the mutator."""

    @abstractmethod
    def remove_mutator(self) -> None:
        """Remove the current mutator."""

    @abstractmethod
    def set_schema(self, schema: Schema) -> None:
        """Set the schema directly (bypassing spec extractor)."""

    @abstractmethod
    def set_state_repository(
        self, repository: BaseSnapshotRepository[BaseState]
    ) -> None:
        """Replace the snapshot repository."""

    @abstractmethod
    def set_projectors(
        self,
        projectors: Union[
            BaseProjector[ProjectionContext, ProjectionResult],
            List[BaseProjector[ProjectionContext, ProjectionResult]],
        ],
    ) -> None:
        """Replace all projectors with the given one(s)."""

    @abstractmethod
    def add_projector(
        self, projector: BaseProjector[ProjectionContext, ProjectionResult]
    ) -> None:
        """Add a projector (equivalent to ``attach``)."""

    @abstractmethod
    def remove_projector(
        self, projector: BaseProjector[ProjectionContext, ProjectionResult]
    ) -> None:
        """Remove a projector (equivalent to ``detach``)."""

    @abstractmethod
    def clear_projectors(self) -> None:
        """Remove all projectors."""
