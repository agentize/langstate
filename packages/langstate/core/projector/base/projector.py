"""Base Projector interface for LangState.

The Projector is responsible for:
- Projecting internal state to external representations
- Base interface for both UI projection and Canonical State projection
"""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, TypeVar, Generic

from .schema import ProjectionContext, ProjectionResult

PC = TypeVar("PC", bound=ProjectionContext)
PR = TypeVar("PR", bound=ProjectionResult)

if TYPE_CHECKING:
    from ...schema_reader.base.schema import Schema


class BaseProjector(ABC, Generic[PC, PR]):
    """Abstract base class for all Projector implementations.

    A Projector transforms internal state into a specific output format.
    This is the base interface that specialized projectors inherit from.

    Specialized implementations:
    - ProjectorUI: Transforms state into UI components and user prompts
    - ProjectorCanonicalState: Transforms interpretive state into canonical business state
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
