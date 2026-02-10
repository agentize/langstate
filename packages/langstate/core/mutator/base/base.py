"""Mutator interface for LangState.

The Mutator is responsible for:
- Receiving user input (prompts, actions from frontend)
- Interpreting the input in the context of the current interpretive state
- Updating interpretive state by adding inferences and value-confidence pairs to field snapshots
"""

from abc import ABC, abstractmethod

from .schema import MutationContext, MutationResult


class BaseMutator(ABC):
    """Abstract base class for Mutator implementations.

    The Mutator processes user input and updates the interpretive state by
    adding inferences and value-confidence pairs to field snapshots. It is
    responsible for extracting values from natural language input and assigning
    confidence scores.
    """

    @abstractmethod
    async def mutate(self, context: MutationContext) -> MutationResult:
        """Process user input and update the interpretive state graph.

        This method takes the user's input along with the current interpretive state
        and returns an updated interpretive state with inferences and value-confidence
        pairs extracted from the input added to field snapshots.

        Args:
            context: MutationContext containing agent input and current state

        Returns:
            MutationResult with the updated state graph
        """
        pass
