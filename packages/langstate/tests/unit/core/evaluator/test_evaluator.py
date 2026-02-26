"""
Comprehensive unit tests for the Evaluator implementation.

Tests cover:
- Evaluator._compare_states   (all classification branches)
- Evaluator._get_best_value   (None-field, empty-values, single, multi)
- Evaluator._values_equal     (None/None, one-None, same, different)
- LLMEvaluator.evaluate       (end-to-end, accuracy_score, copy semantics, TypeError)
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from typing import Any, Optional, Dict

import pytest

from core.evaluator.evaluator import Evaluator
from core.evaluator.llm.evaluator import LLMEvaluator
from core.evaluator.schema import (
    EvaluationContext,
    EvaluationResult,
    StateComparison,
)
from core.mutator.llm.client.base import BaseLLMClient
from core.mutator.llm.mutator import LLMMutator
from core.mutator.llm.schema import StructuredInput
from core.state.state.schema import Inference, ValueConfidence
from core.state.state.state import State

# ---------------------------------------------------------------------------
# Helpers / Mocks
# ---------------------------------------------------------------------------


class MockLLMClient(BaseLLMClient):
    """LLM client that returns a pre-configured JSON string."""

    def __init__(self, response: str = "[]") -> None:
        self._response = response

    async def generate(self, prompt: str) -> str:
        return self._response


class ConcreteEvaluator(Evaluator):
    """Minimal concrete evaluator used to test the Evaluator mixin methods."""

    async def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        raise NotImplementedError("Use LLMEvaluator for full evaluate tests")


def make_state(*field_defs: tuple[str, object, float]) -> State:
    """Build a State with (path, value, confidence) triples."""
    state = State()
    for path, value, confidence in field_defs:
        state.add_value(path, ValueConfidence(value=value, confidence=confidence))
    return state


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def evaluator() -> ConcreteEvaluator:
    return ConcreteEvaluator()


@pytest.fixture
def llm_evaluator() -> LLMEvaluator:
    return LLMEvaluator()


@pytest.fixture
def empty_state() -> State:
    return State()


@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    return MockLLMClient()


# ============================================================================
# Tests for Evaluator._values_equal
# ============================================================================


class TestEvaluatorValuesEqual:
    """Tests for the _values_equal helper."""

    def test_both_none_returns_true(self, evaluator: ConcreteEvaluator) -> None:
        """Both None values should be considered equal."""
        assert evaluator._values_equal(None, None) is True

    def test_first_none_returns_false(self, evaluator: ConcreteEvaluator) -> None:
        """None and a real value should not be equal."""
        vc = ValueConfidence(value="x", confidence=0.5)
        assert evaluator._values_equal(None, vc) is False

    def test_second_none_returns_false(self, evaluator: ConcreteEvaluator) -> None:
        """A real value and None should not be equal."""
        vc = ValueConfidence(value="x", confidence=0.5)
        assert evaluator._values_equal(vc, None) is False

    def test_same_value_and_confidence_returns_true(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """Two ValueConfidence objects with same value and confidence should be equal."""
        a = ValueConfidence(value="hello", confidence=0.9)
        b = ValueConfidence(value="hello", confidence=0.9)
        assert evaluator._values_equal(a, b) is True

    def test_different_value_returns_false(self, evaluator: ConcreteEvaluator) -> None:
        """Different values (same confidence) should not be equal."""
        a = ValueConfidence(value="hello", confidence=0.9)
        b = ValueConfidence(value="world", confidence=0.9)
        assert evaluator._values_equal(a, b) is False

    def test_different_confidence_returns_false(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """Same value with different confidence should not be equal."""
        a = ValueConfidence(value="hello", confidence=0.9)
        b = ValueConfidence(value="hello", confidence=0.5)
        assert evaluator._values_equal(a, b) is False

    def test_different_value_and_confidence_returns_false(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """Different value and confidence should not be equal."""
        a = ValueConfidence(value="a", confidence=0.1)
        b = ValueConfidence(value="b", confidence=0.9)
        assert evaluator._values_equal(a, b) is False


# ============================================================================
# Tests for Evaluator._get_best_value
# ============================================================================


class TestEvaluatorGetBestValue:
    """Tests for the _get_best_value helper."""

    def test_absent_field_returns_none(self, evaluator: ConcreteEvaluator) -> None:
        """_get_best_value for a nonexistent path should return None."""
        state = State()
        result = evaluator._get_best_value(state, "nonexistent")
        assert result is None

    def test_field_with_no_values_returns_none(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """_get_best_value for a field that exists but has no values should return None."""
        state = State()
        # set a field with an inference but zero values
        state.add_inference("field", Inference(content="some reason"))
        result = evaluator._get_best_value(state, "field")
        assert result is None

    def test_single_value_returned(self, evaluator: ConcreteEvaluator) -> None:
        """_get_best_value for a single-value field should return that value."""
        vc = ValueConfidence(value="Alice", confidence=0.8)
        state = State()
        state.add_value("name", vc)
        result = evaluator._get_best_value(state, "name")
        assert result is not None
        assert result.value == "Alice"
        assert result.confidence == 0.8

    def test_multiple_values_returns_highest_confidence(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """_get_best_value should return the ValueConfidence with the highest confidence."""
        state = State()
        state.add_value("name", ValueConfidence(value="low", confidence=0.1))
        state.add_value("name", ValueConfidence(value="high", confidence=0.95))
        state.add_value("name", ValueConfidence(value="mid", confidence=0.5))
        result = evaluator._get_best_value(state, "name")
        assert result is not None
        assert result.value == "high"
        assert result.confidence == 0.95


# ============================================================================
# Tests for Evaluator._compare_states
# ============================================================================


class TestEvaluatorCompareStates:
    """Tests for the _compare_states method covering all classification branches."""

    @pytest.mark.asyncio
    async def test_both_empty_states(self, evaluator: ConcreteEvaluator) -> None:
        """Comparing two empty states should yield an empty, fully matching comparison."""
        comparison = await evaluator._compare_states(State(), State())
        assert comparison.fields == []
        assert comparison.matching_fields == 0
        assert comparison.mismatched_fields == 0
        assert comparison.missing_fields == 0
        assert comparison.extra_fields == 0
        assert comparison.overall_match is True

    @pytest.mark.asyncio
    async def test_field_only_in_expected_is_missing(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """A field present only in expected should be classified as 'missing'."""
        expected = make_state(("city", "Oslo", 0.9))
        actual = State()
        comparison = await evaluator._compare_states(expected, actual)
        assert comparison.missing_fields == 1
        assert comparison.extra_fields == 0
        assert comparison.matching_fields == 0
        assert comparison.overall_match is False

    @pytest.mark.asyncio
    async def test_field_only_in_actual_is_extra(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """A field present only in actual should be classified as 'extra'."""
        expected = State()
        actual = make_state(("city", "Oslo", 0.9))
        comparison = await evaluator._compare_states(expected, actual)
        assert comparison.extra_fields == 1
        assert comparison.missing_fields == 0
        assert comparison.matching_fields == 0
        assert comparison.overall_match is False

    @pytest.mark.asyncio
    async def test_matching_fields(self, evaluator: ConcreteEvaluator) -> None:
        """Fields that match value and confidence should be counted as matching."""
        expected = make_state(("name", "Alice", 0.8))
        actual = make_state(("name", "Alice", 0.8))
        comparison = await evaluator._compare_states(expected, actual)
        assert comparison.matching_fields == 1
        assert comparison.mismatched_fields == 0
        assert comparison.missing_fields == 0
        assert comparison.extra_fields == 0
        assert comparison.overall_match is True

    @pytest.mark.asyncio
    async def test_mismatched_fields(self, evaluator: ConcreteEvaluator) -> None:
        """Fields with different values should be counted as mismatched."""
        expected = make_state(("name", "Alice", 0.8))
        actual = make_state(("name", "Bob", 0.8))
        comparison = await evaluator._compare_states(expected, actual)
        assert comparison.mismatched_fields == 1
        assert comparison.matching_fields == 0
        assert comparison.overall_match is False

    @pytest.mark.asyncio
    async def test_difference_string_set_on_mismatch(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """A mismatched field should have a non-None difference string."""
        expected = make_state(("name", "Alice", 0.8))
        actual = make_state(("name", "Bob", 0.8))
        comparison = await evaluator._compare_states(expected, actual)
        fc = comparison.fields[0]
        assert fc.difference is not None
        assert "name" in fc.difference

    @pytest.mark.asyncio
    async def test_difference_string_none_on_match(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """A matching field should have a None difference string."""
        expected = make_state(("name", "Alice", 0.8))
        actual = make_state(("name", "Alice", 0.8))
        comparison = await evaluator._compare_states(expected, actual)
        fc = comparison.fields[0]
        assert fc.difference is None

    @pytest.mark.asyncio
    async def test_fields_sorted_alphabetically(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """_compare_states should return fields sorted by path alphabetically."""
        expected = make_state(("z_field", "z", 1.0), ("a_field", "a", 1.0))
        actual = make_state(("z_field", "z", 1.0), ("a_field", "a", 1.0))
        comparison = await evaluator._compare_states(expected, actual)
        paths = [fc.field_path for fc in comparison.fields]
        assert paths == sorted(paths)

    @pytest.mark.asyncio
    async def test_mixed_scenario(self, evaluator: ConcreteEvaluator) -> None:
        """Mixed scenario: match + mismatch + missing + extra should all be counted."""
        expected = make_state(
            ("match", "same", 0.9),
            ("mismatch", "exp", 0.5),
            ("missing", "absent", 0.7),
        )
        actual = make_state(
            ("match", "same", 0.9),
            ("mismatch", "actual", 0.5),
            ("extra", "bonus", 0.3),
        )
        comparison = await evaluator._compare_states(expected, actual)
        assert comparison.matching_fields == 1
        assert comparison.mismatched_fields == 1
        assert comparison.missing_fields == 1
        assert comparison.extra_fields == 1
        assert comparison.overall_match is False

    @pytest.mark.asyncio
    async def test_overall_match_false_when_mismatched(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """overall_match should be False when there are mismatched fields."""
        expected = make_state(("k", "a", 0.5))
        actual = make_state(("k", "b", 0.5))
        comparison = await evaluator._compare_states(expected, actual)
        assert comparison.overall_match is False

    @pytest.mark.asyncio
    async def test_missing_field_has_no_actual_value(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """A missing-field FieldComparison should have actual_value=None."""
        expected = make_state(("x", "val", 0.8))
        comparison = await evaluator._compare_states(expected, State())
        fc = next(f for f in comparison.fields if f.field_path == "x")
        assert fc.actual_value is None
        assert fc.expected_value is not None

    @pytest.mark.asyncio
    async def test_extra_field_has_no_expected_value(
        self, evaluator: ConcreteEvaluator
    ) -> None:
        """An extra-field FieldComparison should have expected_value=None."""
        actual = make_state(("x", "val", 0.8))
        comparison = await evaluator._compare_states(State(), actual)
        fc = next(f for f in comparison.fields if f.field_path == "x")
        assert fc.expected_value is None
        assert fc.actual_value is not None


# ============================================================================
# Tests for LLMEvaluator.evaluate
# ============================================================================


class TestLLMEvaluatorEvaluate:
    """End-to-end tests for LLMEvaluator.evaluate."""

    def _make_context(
        self,
        *,
        pre_state: State,
        expected_post_state: State,
        llm_response: str = "[]",
        message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[EvaluationContext, LLMEvaluator]:
        client = MockLLMClient(response=llm_response)
        mutator = LLMMutator(client)
        evaluator = LLMEvaluator()
        ctx = EvaluationContext(
            mutator=mutator,
            pre_state=pre_state,
            expected_post_state=expected_post_state,
            mutation_input=StructuredInput(prompt="test input", message_id=message_id),
            metadata=metadata,
        )
        return ctx, evaluator

    @pytest.mark.asyncio
    async def test_returns_evaluation_result(self, empty_state: State) -> None:
        """evaluate should return an EvaluationResult."""
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=State(),
        )
        result = await ev.evaluate(ctx)
        assert isinstance(result, EvaluationResult)

    @pytest.mark.asyncio
    async def test_time_used_is_non_negative(self, empty_state: State) -> None:
        """time_used should be a non-negative float."""
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=State(),
        )
        result = await ev.evaluate(ctx)
        assert result.time_used >= 0.0

    @pytest.mark.asyncio
    async def test_accuracy_score_zero_when_no_expected_fields(
        self, empty_state: State
    ) -> None:
        """accuracy_score should be 0.0 when expected state has no fields."""
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=State(),
            llm_response="[]",
        )
        result = await ev.evaluate(ctx)
        assert result.accuracy_score == 0.0

    @pytest.mark.asyncio
    async def test_accuracy_score_one_when_all_match(self, empty_state: State) -> None:
        """accuracy_score should be 1.0 when all expected fields match actual."""
        extraction: list[dict[str, object]] = [
            {"path": "name", "value": "Alice", "confidence": 0.9, "inference": "r"}
        ]
        expected = make_state(("name", "Alice", 0.9))
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=expected,
            llm_response=json.dumps(extraction),
        )
        result = await ev.evaluate(ctx)
        assert result.accuracy_score == pytest.approx(1.0)  # type: ignore[misc]

    @pytest.mark.asyncio
    async def test_accuracy_score_partial(self, empty_state: State) -> None:
        """accuracy_score should be 0.5 when half the expected fields match."""
        extractions: list[dict[str, object]] = [
            {"path": "a", "value": "x", "confidence": 0.8, "inference": "r"},
        ]
        # expected has two fields; LLM only fills one correctly
        expected = make_state(("a", "x", 0.8), ("b", "y", 0.7))
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=expected,
            llm_response=json.dumps(extractions),
        )
        result = await ev.evaluate(ctx)
        # matching=1, missing=1, mismatched=0 → 1/2
        assert result.accuracy_score == pytest.approx(0.5)  # type: ignore[misc]

    @pytest.mark.asyncio
    async def test_pre_state_not_modified(self) -> None:
        """evaluate should not modify the original pre_state."""
        original = State()
        extraction: list[dict[str, object]] = [
            {"path": "name", "value": "Alice", "confidence": 0.9, "inference": "r"}
        ]
        ctx, ev = self._make_context(
            pre_state=original,
            expected_post_state=State(),
            llm_response=json.dumps(extraction),
        )
        await ev.evaluate(ctx)
        assert original.get_field("name") is None

    @pytest.mark.asyncio
    async def test_actual_post_state_is_returned(self, empty_state: State) -> None:
        """evaluate should include the actual post-state in the result."""
        extraction: list[dict[str, object]] = [
            {"path": "city", "value": "Oslo", "confidence": 0.8, "inference": "r"}
        ]
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=State(),
            llm_response=json.dumps(extraction),
        )
        result = await ev.evaluate(ctx)
        assert result.actual_post_state.get_field("city") is not None

    @pytest.mark.asyncio
    async def test_comparison_included_in_result(self, empty_state: State) -> None:
        """evaluate should include a StateComparison in the result."""
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=State(),
        )
        result = await ev.evaluate(ctx)
        assert isinstance(result.comparison, StateComparison)

    @pytest.mark.asyncio
    async def test_metadata_passed_through(self, empty_state: State) -> None:
        """Metadata from EvaluationContext should appear in EvaluationResult."""
        md = {"session": "s1"}
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=State(),
            metadata=md,
        )
        result = await ev.evaluate(ctx)
        assert result.metadata == md

    @pytest.mark.asyncio
    async def test_pre_state_copy_non_state_raises_type_error(self) -> None:
        """If pre_state.copy() returns a non-State, evaluate should raise TypeError."""
        original = State()

        # monkeypatch copy to return a plain object instead of State
        original.copy = lambda: object()  # type: ignore[method-assign]

        ev = LLMEvaluator()
        mutator = LLMMutator(MockLLMClient())
        ctx = EvaluationContext(
            mutator=mutator,
            pre_state=original,
            expected_post_state=State(),
            mutation_input=StructuredInput(prompt="test"),
        )
        with pytest.raises(TypeError):
            await ev.evaluate(ctx)

    @pytest.mark.asyncio
    async def test_overall_match_true_when_exact_match(
        self, empty_state: State
    ) -> None:
        """overall_match should be True when all expected fields match actual."""
        extraction: list[dict[str, object]] = [
            {"path": "x", "value": "42", "confidence": 1.0, "inference": "r"}
        ]
        expected = make_state(("x", "42", 1.0))
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=expected,
            llm_response=json.dumps(extraction),
        )
        result = await ev.evaluate(ctx)
        assert result.comparison.overall_match is True

    @pytest.mark.asyncio
    async def test_overall_match_false_on_missing_field(
        self, empty_state: State
    ) -> None:
        """overall_match should be False when expected field is not produced."""
        expected = make_state(("required", "value", 0.9))
        ctx, ev = self._make_context(
            pre_state=empty_state,
            expected_post_state=expected,
            llm_response="[]",
        )
        result = await ev.evaluate(ctx)
        assert result.comparison.overall_match is False
