"""Base Projector interface for LangState."""

from abc import abstractmethod
from typing import Optional, TYPE_CHECKING, TypeVar, Generic

from ...data_structure.observer.base import BaseObserver, BaseSubject
from .schema import ProjectionContext, ProjectionResult

PC = TypeVar("PC", bound=ProjectionContext)
PR = TypeVar("PR", bound=ProjectionResult)

if TYPE_CHECKING:
    from ...spec_extractor.base.schema import Schema


class BaseProjector(BaseObserver[PC], Generic[PC, PR]):
    """Abstract base class for all Projector implementations.

    A Projector transforms current state into a specific output format.
    Specialized projector types can provide domain-specific contracts.
    """

    @abstractmethod
    async def project(self, context: PC) -> PR:
        """Project the state to the target format.

        Args:
            context: PC containing current state

        Returns:
            PR with the projection output
        """
        pass

    @abstractmethod
    async def initialize(self, schema: Optional["Schema"] = None) -> None:
        """Initialize the projector with a schema.

        This method is called when the projector is first set up,
        allowing it to configure itself based on the schema definition.

        Args:
            schema: The schema definition to use for projection
        """
        pass

    async def notified(self, subject: BaseSubject[PC], event: PC) -> object:
        """Observer hook executed by the shared Subject protocol."""
        return await self.project(event)
