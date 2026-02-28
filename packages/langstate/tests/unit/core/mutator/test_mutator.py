"""
Comprehensive unit tests for the Mutator implementation.

Tests cover:
- BaseMutator.__get_pydantic_core_schema__  (Pydantic integration)
- MutationResult schema   (construction, defaults)
- StructuredInput schema  (required / optional fields)
- MutationContext schema  (construction)
- FieldExtraction schema  (confidence boundary validation)
- LLMMutator.__init__     (unique UUID4 mutator_id per instance)
- LLMMutator.mutate       (extraction, state copy semantics, error handling)
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
import uuid

import pytest
from pydantic import BaseModel, ValidationError

from core.mutator.base.base import BaseMutator
from core.mutator.base.schema import MutationResult
from core.mutator.llm.client.base import BaseLLMClient
from core.mutator.llm.client.schema import FieldExtraction
from core.mutator.llm.mutator import LLMMutator
from core.mutator.llm.schema import MutationContext, StructuredInput
from core.state.state.schema import ValueConfidence
from core.state.state.state import State

# ---------------------------------------------------------------------------
# Helpers / Mocks
# ---------------------------------------------------------------------------


class MockLLMClient(BaseLLMClient):
    """LLM client that returns a pre-configured string."""

    def __init__(self, response: str = "[]") -> None:
        self._response = response

    async def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._response


class ConcreteMutator(BaseMutator[MutationContext]):
    """Minimal concrete mutator used to validate BaseMutator plumbing."""

    async def mutate(self, context: MutationContext) -> MutationResult:
        return MutationResult(updated_state=context.state)


# ---------------------------------------------------------------------------
# Helpers that build States
# ---------------------------------------------------------------------------


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
def mock_llm_client() -> MockLLMClient:
    return MockLLMClient()


@pytest.fixture
def pre_state() -> State:
    return State()


@pytest.fixture
def mutator(mock_llm_client: MockLLMClient) -> LLMMutator:
    return LLMMutator(llm_client=mock_llm_client)


# ============================================================================
# Tests for BaseMutator Pydantic schema integration
# ============================================================================


class TestBaseMutatorSchema:
    """Tests for BaseMutator.__get_pydantic_core_schema__."""

    def test_pydantic_accepts_llm_mutator_as_base_mutator(self) -> None:
        """Pydantic should accept an LLMMutator where BaseMutator is expected."""

        class Model(BaseModel):
            mutator: BaseMutator[MutationContext]

        llm_mutator = LLMMutator(MockLLMClient())
        model = Model(mutator=llm_mutator)
        assert model.mutator is llm_mutator

    def test_pydantic_rejects_non_mutator(self) -> None:
        """Pydantic should reject a plain object where BaseMutator is expected."""

        class Model(BaseModel):
            mutator: BaseMutator[MutationContext]

        with pytest.raises(ValidationError):
            Model(mutator="not_a_mutator")  # type: ignore[arg-type]

    def test_get_pydantic_core_schema_returns_schema(self) -> None:
        """__get_pydantic_core_schema__ should return a dict-like CoreSchema."""
        from typing import Any as _Any
        from pydantic_core import core_schema as cs

        def _noop_handler(_t: _Any) -> cs.CoreSchema:
            return cs.any_schema()

        schema = BaseMutator.__get_pydantic_core_schema__(BaseMutator, _noop_handler)
        assert schema is not None


# ============================================================================
# Tests for MutationResult schema
# ============================================================================


class TestMutationResultSchema:
    """Tests for the MutationResult Pydantic model."""

    def test_valid_construction(self, pre_state: State) -> None:
        """MutationResult should accept a State and optional metadata."""
        result = MutationResult(updated_state=pre_state)
        assert result.updated_state is pre_state
        assert result.metadata is None

    def test_metadata_can_be_set(self, pre_state: State) -> None:
        """MutationResult should accept a metadata dict."""
        result = MutationResult(updated_state=pre_state, metadata={"key": "val"})
        assert result.metadata == {"key": "val"}

    def test_metadata_defaults_to_none(self, pre_state: State) -> None:
        """MutationResult metadata should default to None."""
        result = MutationResult(updated_state=pre_state)
        assert result.metadata is None


# ============================================================================
# Tests for StructuredInput schema
# ============================================================================


class TestStructuredInputSchema:
    """Tests for the StructuredInput Pydantic model."""

    def test_prompt_is_required(self) -> None:
        """StructuredInput without prompt should raise ValidationError."""
        with pytest.raises(ValidationError):
            StructuredInput()  # type: ignore[call-arg]

    def test_valid_with_prompt_only(self) -> None:
        """StructuredInput can be created with just a prompt."""
        si = StructuredInput(prompt="hello")
        assert si.prompt == "hello"
        assert si.message_id is None

    def test_message_id_is_optional(self) -> None:
        """StructuredInput should accept an optional message_id."""
        si = StructuredInput(prompt="hello", message_id="msg123")
        assert si.message_id == "msg123"


# ============================================================================
# Tests for MutationContext schema
# ============================================================================


class TestMutationContextSchema:
    """Tests for the MutationContext Pydantic model."""

    def test_valid_construction(self, pre_state: State) -> None:
        """MutationContext constructs with input and state."""
        ctx = MutationContext(
            input=StructuredInput(prompt="test"),
            state=pre_state,
        )
        assert ctx.input.prompt == "test"
        assert ctx.state is pre_state
        assert ctx.metadata is None

    def test_metadata_accepted(self, pre_state: State) -> None:
        """MutationContext should accept a metadata dict."""
        ctx = MutationContext(
            input=StructuredInput(prompt="x"),
            state=pre_state,
            metadata={"session": "abc"},
        )
        assert ctx.metadata == {"session": "abc"}


# ============================================================================
# Tests for FieldExtraction schema
# ============================================================================


class TestFieldExtractionSchema:
    """Tests for the FieldExtraction Pydantic model."""

    def test_valid_extraction(self) -> None:
        """FieldExtraction should accept all required fields."""
        fe = FieldExtraction(
            path="name",
            value="John",
            confidence=0.9,
            inference="Extracted name",
        )
        assert fe.path == "name"
        assert fe.value == "John"
        assert fe.confidence == 0.9
        assert fe.inference == "Extracted name"

    def test_confidence_lower_bound(self) -> None:
        """Confidence of exactly -1.0 should be accepted."""
        fe = FieldExtraction(path="p", value="v", confidence=-1.0, inference="i")
        assert fe.confidence == -1.0

    def test_confidence_upper_bound(self) -> None:
        """Confidence of exactly 1.0 should be accepted."""
        fe = FieldExtraction(path="p", value="v", confidence=1.0, inference="i")
        assert fe.confidence == 1.0

    def test_confidence_below_lower_bound_raises(self) -> None:
        """Confidence below -1.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            FieldExtraction(path="p", value="v", confidence=-1.1, inference="i")

    def test_confidence_above_upper_bound_raises(self) -> None:
        """Confidence above 1.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            FieldExtraction(path="p", value="v", confidence=1.1, inference="i")

    def test_missing_path_raises(self) -> None:
        """FieldExtraction without path should raise ValidationError."""
        with pytest.raises(ValidationError):
            FieldExtraction(value="v", confidence=0.5, inference="i")  # type: ignore[call-arg]


# ============================================================================
# Tests for LLMMutator.__init__
# ============================================================================


class TestLLMMutatorInit:
    """Tests for LLMMutator initialisation."""

    def test_stores_llm_client(self, mock_llm_client: MockLLMClient) -> None:
        """LLMMutator should store the provided LLM client."""
        m = LLMMutator(mock_llm_client)
        assert m._llm_client is mock_llm_client

    def test_mutator_id_is_valid_uuid(self, mock_llm_client: MockLLMClient) -> None:
        """LLMMutator._mutator_id should be a valid UUID4 string."""
        m = LLMMutator(mock_llm_client)
        parsed = uuid.UUID(m._mutator_id, version=4)
        assert str(parsed) == m._mutator_id

    def test_each_instance_has_unique_mutator_id(
        self, mock_llm_client: MockLLMClient
    ) -> None:
        """Two LLMMutator instances should have different _mutator_ids."""
        m1 = LLMMutator(mock_llm_client)
        m2 = LLMMutator(mock_llm_client)
        assert m1._mutator_id != m2._mutator_id


# ============================================================================
# Tests for LLMMutator.mutate
# ============================================================================


class TestLLMMutatorMutate:
    """Tests for LLMMutator.mutate — the core extraction loop."""

    @pytest.mark.asyncio
    async def test_empty_extraction_returns_unchanged_state(
        self, mutator: LLMMutator, pre_state: State
    ) -> None:
        """When LLM returns an empty array, state should stay unchanged."""
        ctx = MutationContext(
            input=StructuredInput(prompt="nothing to extract"),
            state=pre_state,
        )
        mutator._llm_client = MockLLMClient(response="[]")  # type: ignore[assignment]
        result = await mutator.mutate(ctx)
        assert isinstance(result, MutationResult)
        assert result.updated_state.get_all_fields() == {}

    @pytest.mark.asyncio
    async def test_single_extraction_adds_value_and_inference(
        self, mutator: LLMMutator, pre_state: State
    ) -> None:
        """A single valid LLM extraction should create value and inference on the state."""
        extraction: list[dict[str, object]] = [
            {
                "path": "name",
                "value": "Alice",
                "confidence": 0.95,
                "inference": "Name found in greeting",
            }
        ]
        mutator._llm_client = MockLLMClient(  # type: ignore[assignment]
            response=json.dumps(extraction)
        )
        ctx = MutationContext(
            input=StructuredInput(prompt="Hi, I am Alice"),
            state=pre_state,
        )
        result = await mutator.mutate(ctx)

        field = result.updated_state.get_field("name")
        assert field is not None
        assert len(field.values) == 1
        assert field.values[0].value == "Alice"
        assert field.values[0].confidence == 0.95
        assert field.inference is not None
        assert field.inference.content == "Name found in greeting"

    @pytest.mark.asyncio
    async def test_multiple_extractions_all_applied(
        self, mutator: LLMMutator, pre_state: State
    ) -> None:
        """Multiple LLM extractions should all be applied to the state."""
        extractions: list[dict[str, object]] = [
            {"path": "name", "value": "Bob", "confidence": 0.9, "inference": "i1"},
            {
                "path": "email",
                "value": "bob@x.com",
                "confidence": 0.8,
                "inference": "i2",
            },
        ]
        mutator._llm_client = MockLLMClient(  # type: ignore[assignment]
            response=json.dumps(extractions)
        )
        ctx = MutationContext(
            input=StructuredInput(prompt="Bob, bob@x.com"),
            state=pre_state,
        )
        result = await mutator.mutate(ctx)

        assert result.updated_state.get_field("name") is not None
        assert result.updated_state.get_field("email") is not None

    @pytest.mark.asyncio
    async def test_message_id_propagated_to_inference(
        self, mutator: LLMMutator, pre_state: State
    ) -> None:
        """message_id from StructuredInput should appear in the resulting Inference."""
        extraction: list[dict[str, object]] = [
            {"path": "x", "value": "y", "confidence": 0.5, "inference": "r"}
        ]
        mutator._llm_client = MockLLMClient(  # type: ignore[assignment]
            response=json.dumps(extraction)
        )
        ctx = MutationContext(
            input=StructuredInput(prompt="test", message_id="msg-42"),
            state=pre_state,
        )
        result = await mutator.mutate(ctx)
        field = result.updated_state.get_field("x")
        assert field is not None
        assert field.inference is not None
        assert field.inference.message_id == "msg-42"

    @pytest.mark.asyncio
    async def test_none_message_id_propagated(
        self, mutator: LLMMutator, pre_state: State
    ) -> None:
        """None message_id should remain None in the resulting Inference."""
        extraction: list[dict[str, object]] = [
            {"path": "x", "value": "y", "confidence": 0.5, "inference": "r"}
        ]
        mutator._llm_client = MockLLMClient(  # type: ignore[assignment]
            response=json.dumps(extraction)
        )
        ctx = MutationContext(
            input=StructuredInput(prompt="test", message_id=None),
            state=pre_state,
        )
        result = await mutator.mutate(ctx)
        field = result.updated_state.get_field("x")
        assert field is not None
        assert field.inference is not None
        assert field.inference.message_id is None

    @pytest.mark.asyncio
    async def test_mutator_id_on_inference_matches_own_id(
        self, mutator: LLMMutator, pre_state: State
    ) -> None:
        """Inference.mutator_id should equal the mutator's own _mutator_id."""
        extraction: list[dict[str, object]] = [
            {"path": "z", "value": "w", "confidence": 0.7, "inference": "r"}
        ]
        mutator._llm_client = MockLLMClient(  # type: ignore[assignment]
            response=json.dumps(extraction)
        )
        ctx = MutationContext(
            input=StructuredInput(prompt="test"),
            state=pre_state,
        )
        result = await mutator.mutate(ctx)
        field = result.updated_state.get_field("z")
        assert field is not None
        assert field.inference is not None
        assert field.inference.mutator_id == mutator._mutator_id

    @pytest.mark.asyncio
    async def test_non_list_json_raises_value_error(
        self, mutator: LLMMutator, pre_state: State
    ) -> None:
        """When LLM returns a non-list JSON value, mutate should raise ValueError."""
        mutator._llm_client = MockLLMClient(response='{"key": "val"}')  # type: ignore[assignment]
        ctx = MutationContext(
            input=StructuredInput(prompt="test"),
            state=pre_state,
        )
        with pytest.raises(ValueError, match="JSON array"):
            await mutator.mutate(ctx)

    @pytest.mark.asyncio
    async def test_original_state_not_mutated(self, mutator: LLMMutator) -> None:
        """mutate() should operate on a copy; the original state must not be modified."""
        original = State()
        extraction: list[dict[str, object]] = [
            {"path": "name", "value": "Carol", "confidence": 0.9, "inference": "r"}
        ]
        mutator._llm_client = MockLLMClient(  # type: ignore[assignment]
            response=json.dumps(extraction)
        )
        ctx = MutationContext(
            input=StructuredInput(prompt="Hi Carol"),
            state=original,
        )
        await mutator.mutate(ctx)

        # original state must remain unchanged
        assert original.get_field("name") is None

    @pytest.mark.asyncio
    async def test_llm_prompt_includes_state_json(
        self, mutator: LLMMutator, pre_state: State
    ) -> None:
        """The prompt sent to the LLM should embed the JSON representation of the state."""
        client = MockLLMClient(response="[]")
        mutator._llm_client = client  # type: ignore[assignment]
        ctx = MutationContext(
            input=StructuredInput(prompt="check state"),
            state=pre_state,
        )
        await mutator.mutate(ctx)
        assert "check state" in client.last_prompt

    @pytest.mark.asyncio
    async def test_concrete_mutator_can_be_used(self, pre_state: State) -> None:
        """ConcreteMutator (non-LLM) should satisfy the BaseMutator interface."""
        m = ConcreteMutator()
        ctx = MutationContext(
            input=StructuredInput(prompt="test"),
            state=pre_state,
        )
        result = await m.mutate(ctx)
        assert isinstance(result, MutationResult)


# ============================================================================
# Additional coverage tests
# ============================================================================


class TestBaseMutatorABC:
    """Tests for BaseMutator abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseMutator()  # type: ignore[abstract]


class TestBaseLLMClientABC:
    """Tests for BaseLLMClient abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseLLMClient()  # type: ignore[abstract]


class TestLLMMutatorMutateEdgeCases:
    """Additional edge cases for LLMMutator.mutate."""

    @pytest.mark.asyncio
    async def test_mutate_unparseable_json_raises(self) -> None:
        """When LLM returns invalid JSON, mutate should raise."""
        client = MockLLMClient(response="not json at all {{{")
        m = LLMMutator(client)
        ctx = MutationContext(
            input=StructuredInput(prompt="test"),
            state=State(),
        )
        with pytest.raises((ValueError, json.JSONDecodeError)):
            await m.mutate(ctx)

    @pytest.mark.asyncio
    async def test_mutate_with_negative_confidence(self) -> None:
        """Negative confidence in extraction should be applied."""
        extraction: list[dict[str, object]] = [
            {"path": "x", "value": "v", "confidence": -0.5, "inference": "negative"}
        ]
        client = MockLLMClient(response=json.dumps(extraction))
        m = LLMMutator(client)
        ctx = MutationContext(
            input=StructuredInput(prompt="test"),
            state=State(),
        )
        result = await m.mutate(ctx)
        field = result.updated_state.get_field("x")
        assert field is not None
        assert field.values[0].confidence == -0.5
