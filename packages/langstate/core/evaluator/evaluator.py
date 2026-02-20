"""Base Evaluator implementation for LangState.

Provides shared functionality for comparing states.
"""

from typing import Optional, Set

from .base import BaseEvaluator
from .schema import FieldComparison, StateComparison
from ..state.state.base import BaseState
from ..state.state.schema import ValueConfidence


class Evaluator(BaseEvaluator):
    """Base evaluator with state comparison logic.

    This class provides common functionality for comparing expected
    and actual states field by field. Concrete evaluator
    implementations should inherit from this class and implement the
    ``evaluate`` method.
    """

    async def _compare_states(
        self,
        expected: BaseState,
        actual: BaseState,
    ) -> StateComparison:
        """Compare two states field by field.

        Args:
            expected: The expected state.
            actual:   The actual state produced by the mutator.

        Returns:
            StateComparison with per-field details and aggregate counters.
        """
        expected_fields: Set[str] = set(expected.get_all_fields().keys())
        actual_fields: Set[str] = set(actual.get_all_fields().keys())
        all_paths = expected_fields | actual_fields

        comparisons: list[FieldComparison] = []
        matching = 0
        mismatched = 0
        missing = 0
        extra = 0

        for path in sorted(all_paths):
            expected_val: Optional[ValueConfidence] = self._get_best_value(
                expected, path
            )
            actual_val: Optional[ValueConfidence] = self._get_best_value(actual, path)

            in_expected = path in expected_fields
            in_actual = path in actual_fields

            if in_expected and not in_actual:
                comparisons.append(
                    FieldComparison(
                        field_path=path,
                        matches=False,
                        expected_value=expected_val,
                        actual_value=None,
                        difference=f"Field '{path}' missing from actual state.",
                    )
                )
                missing += 1

            elif not in_expected and in_actual:
                comparisons.append(
                    FieldComparison(
                        field_path=path,
                        matches=False,
                        expected_value=None,
                        actual_value=actual_val,
                        difference=f"Field '{path}' is extra in actual state.",
                    )
                )
                extra += 1

            else:
                values_match = self._values_equal(expected_val, actual_val)
                diff: str | None = None
                if not values_match:
                    diff = (
                        f"Field '{path}': expected {expected_val}, "
                        f"got {actual_val}."
                    )
                comparisons.append(
                    FieldComparison(
                        field_path=path,
                        matches=values_match,
                        expected_value=expected_val,
                        actual_value=actual_val,
                        difference=diff,
                    )
                )
                if values_match:
                    matching += 1
                else:
                    mismatched += 1

        return StateComparison(
            fields=comparisons,
            matching_fields=matching,
            mismatched_fields=mismatched,
            missing_fields=missing,
            extra_fields=extra,
            overall_match=(mismatched == 0 and missing == 0 and extra == 0),
        )

    def _get_best_value(self, state: BaseState, path: str) -> Optional[ValueConfidence]:
        """Get the value with the highest confidence for a field.

        Args:
            state: The state to query.
            path:  The field path.

        Returns:
            The ValueConfidence with the highest confidence score, or None if
            the field is absent or has no values.
        """
        field = state.get_field(path)
        if field is None:
            return None
        values = getattr(field, "values", [])
        if not values:
            return None
        return max(values, key=lambda vc: vc.confidence)

    def _values_equal(
        self,
        a: Optional[ValueConfidence],
        b: Optional[ValueConfidence],
    ) -> bool:
        """Compare two ValueConfidence instances for equality.

        Two values are considered equal when both their ``value`` and
        ``confidence`` fields match. Two ``None`` refs are treated as equal.

        Args:
            a: First ValueConfidence (may be None).
            b: Second ValueConfidence (may be None).

        Returns:
            True if both are None, or both have the same value and confidence.
        """
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return a.value == b.value and a.confidence == b.confidence
