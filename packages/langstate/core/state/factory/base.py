"""State Factory interface for LangState.

The State Factory follows the Factory pattern (SRP) to separate
state creation from business logic. This allows for different
state implementations without changing the core logic.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...schema_reader.base.schema import Schema

from ..canonical.base import BaseCanonicalState
from ..interpretive.base import BaseInterpretiveState


class BaseStateFactory(ABC):
    """Interface for state factory operations.

    This interface defines the contract for creating state instances,
    following Single Responsibility Principle (SRP) by focusing only
    on state creation.

    Implementations can create states:
    - From schema definitions
    - From existing data (restoration)
    - With different initial configurations
    """

    @abstractmethod
    def create_canonical_state(
        self,
        schema: "Schema",
    ) -> BaseCanonicalState:
        """Create a new canonical state instance.

        Args:
            schema: Optional schema to initialize from
            initial_values: Optional initial field values

        Returns:
            New CanonicalState instance
        """
        pass

    @abstractmethod
    def create_interpretive_state(
        self,
        canonical_state: BaseCanonicalState,
    ) -> BaseInterpretiveState:
        """Create a new interpretive state instance.

        Args:
            schema: Optional schema to initialize from
            canonical_state: Optional canonical state to derive values from

        Returns:
            New InterpretiveState instance
        """
        pass

