"""Evaluator interface for LangState.

The Evaluator is responsible for:
- Running a Mutator against a given pre-state and input
- Comparing the actual post-state produced by the Mutator to an expected post-state
- Producing a detailed field-by-field comparison report
"""

from abc import ABC, abstractmethod

from .schema import EvaluationContext, EvaluationResult, StateComparison
from ..state.interpretive.base import BaseInterpretiveState


class BaseEvaluator(ABC):
    """Abstract base class for Evaluator implementations.

    The Evaluator executes a Mutator with a pre-state, then compares
    the resulting post-state against an expected post-state to produce
    a detailed evaluation report.

    Typical usage::

        evaluator = MyEvaluator()
        result = await evaluator.evaluate(EvaluationContext(
            mutator=my_mutator,
            pre_state=pre,
            expected_post_state=expected,
            mutation_input=StructuredInput(prompt="my name is John"),
        ))
        print(result.comparison.overall_match)
    """

    @abstractmethod
    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Run the mutator and compare the actual result to the expected state.

        The method executes ``context.mutator.mutate()`` using the provided
        ``pre_state`` and ``mutation_input``, then delegates to
        ``_compare_states`` to build a field-by-field comparison between the
        expected and actual post-states.

        Args:
            context: EvaluationContext containing the mutator, pre-state,
                     expected post-state, mutation input and optional metadata.

        Returns:
            EvaluationResult with the detailed comparison and the actual
            post-state produced by the mutator.
        """
        pass

    @abstractmethod
    async def _compare_states(
        self,
        expected: BaseInterpretiveState,
        actual: BaseInterpretiveState,
    ) -> StateComparison:
        """Compare two interpretive states field by field.

        Iterates over every field path present in either state, retrieves the
        best value for each, and classifies the field as matching, mismatched,
        missing (present only in expected) or extra (present only in actual).

        Args:
            expected: The expected interpretive state.
            actual:   The actual interpretive state produced by the mutator.

        Returns:
            StateComparison with per-field details and aggregate counters.
        """
        pass
