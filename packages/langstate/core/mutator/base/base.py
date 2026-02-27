"""Mutator interface for LangState.

The Mutator is responsible for:
- Receiving user input from frontend interactions
- Interpreting the input in the context of the current state
- Updating state by adding inferences and value-confidence pairs to field snapshots
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic_core import core_schema

from .schema import MutationResult

TContext = TypeVar("TContext")


class BaseMutator(ABC, Generic[TContext]):
    """Abstract base class for Mutator implementations.

    The Mutator processes user input and updates state by
    adding inferences and value-confidence pairs to field snapshots. It is
    responsible for extracting values from natural language input and assigning
    confidence scores.

    Type Parameters:
        TContext: The context type passed to the mutate method
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any,
    ) -> core_schema.CoreSchema:
        """Generate Pydantic core schema for BaseMutator.

        Returns an is-instance schema that validates the value is an instance
        of BaseMutator without inspecting its generic type parameters.
        """
        return core_schema.is_instance_schema(cls)

    @abstractmethod
    async def mutate(self, context: TContext) -> MutationResult:
        """Process user input and update the state graph.

        This method takes the user's input along with the current state
        and returns an updated state with inferences and value-confidence
        pairs extracted from the input added to field snapshots.

        Args:
            context: Context containing agent input and current state

        Returns:
            MutationResult with the updated state graph
        """
        pass
