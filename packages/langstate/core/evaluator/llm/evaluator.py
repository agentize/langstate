"""Concrete Evaluator implementation for LangState.

Runs a Mutator against a pre-state, then compares the resulting
post-state to an expected post-state field by field.
"""

import time

from ..evaluator import Evaluator
from ..schema import EvaluationContext, EvaluationResult
from ...mutator.llm.schema import MutationContext
from ...state.state.state import State


class LLMEvaluator(Evaluator):
    """Evaluator that executes a mutator and compares states.

    This implementation:
    1. Copies the pre-state so the original is not modified.
    2. Builds a ``MutationContext`` and calls ``mutator.mutate()``.
    3. Compares every field of the expected and actual post-states.
    4. Returns a detailed ``EvaluationResult``.
    """

    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Run the mutator and compare the actual result to the expected state.

        Args:
            context: EvaluationContext with mutator, states, input and metadata.

        Returns:
            EvaluationResult with comparison details and the actual post-state.
        """
        state_copy = context.pre_state.copy()

        if not isinstance(state_copy, State):
            raise TypeError(
                f"pre_state.copy() must return a State, "
                f"got {type(state_copy).__name__}"
            )

        mutation_context = MutationContext(
            input=context.mutation_input,
            state=state_copy,
            metadata=context.metadata,
        )

        # Measure mutation time
        start_time = time.monotonic()
        mutation_result = await context.mutator.mutate(mutation_context)
        end_time = time.monotonic()
        time_used = end_time - start_time

        actual_post_state = mutation_result.updated_state

        comparison = await self._compare_states(
            expected=context.expected_post_state,
            actual=actual_post_state,
        )

        # Compute accuracy score
        expected_field_count = (
            comparison.matching_fields
            + comparison.mismatched_fields
            + comparison.missing_fields
        )
        accuracy_score = (
            comparison.matching_fields / expected_field_count
            if expected_field_count > 0
            else 0.0
        )

        return EvaluationResult(
            comparison=comparison,
            actual_post_state=actual_post_state,
            accuracy_score=accuracy_score,
            time_used=time_used,
            metadata=context.metadata,
        )
