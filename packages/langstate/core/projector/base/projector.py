"""Base Projector interface for LangState.

The Projector is responsible for:
- Projecting internal state to external representations
- Base interface for both UI projection and Canonical State projection
"""

from abc import ABC, abstractmethod

from .schema import ProjectionContext, ProjectionResult


class BaseProjector(ABC):
    """Abstract base class for all Projector implementations.

    A Projector transforms internal state into a specific output format.
    This is the base interface that specialized projectors inherit from.

    Specialized implementations:
    - ProjectorUI: Transforms state into UI components and user prompts
    - ProjectorCanonicalState: Transforms interpretive state into canonical business state
    """

    @abstractmethod
    async def project(self, context: ProjectionContext) -> ProjectionResult:
        """Project the state to the target format.

        Args:
            context: ProjectionContext containing current state

        Returns:
            ProjectionResult with the projection output
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the projector with a schema.

        This method is called when the projector is first set up,
        allowing it to configure itself based on the schema definition.

        Args:
            schema: The schema definition to use for projection
        """
        pass
