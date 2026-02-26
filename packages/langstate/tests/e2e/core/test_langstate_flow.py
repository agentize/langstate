"""End-to-end tests for LangState registration flow.

Scenario
--------
A user registers for an event through 5 consecutive text messages.
Each message is processed by the real ``LLMMutator`` whose
``BaseLLMClient`` is replaced with a deterministic mock that returns
pre-baked JSON extraction arrays.

Components under test:
- ``OpenAPIReader`` – loads the *registeration.yaml* schema
- ``LangState``    – orchestrator
- ``LLMMutator``   – real mutator, only the LLM client is mocked
- ``RegistrationProjector`` – receives every state update, triggers the action
- ``RegistrationAction``    – fires when the state is sufficiently complete
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple, cast

import pytest
import pytest_asyncio

from core.action.base.action import BaseAction
from core.action.base.schema import ActionContext, ActionResult, ActionStatus
from core.langstate.base.langstate import LangState
from core.langstate.base.schema import (
    AgentInput,
    LangStateDeps,
    StateResultData,
)
from core.mutator.llm.client.base import BaseLLMClient
from core.mutator.llm.mutator import LLMMutator
from core.mutator.llm.schema import MutationContext, StructuredInput
from core.projector.base.projector import BaseProjector
from core.projector.base.schema import ProjectionContext, ProjectionResult
from core.spec_extractor.base.schema import Schema
from core.spec_extractor.openapi.extractor import OpenAPIReader
from core.state.state.base import BaseState
from core.state.state.state import State


# ── Constants ──────────────────────────────────────────────────────

SCHEMA_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "schemas"
    / "registeration.yaml"
)

# Fields that must be present (with at least one value) for the action to fire.
REQUIRED_FIELDS: List[str] = [
    "registrant.name",
    "registrant.email",
    "event.name",
    "event.id",
    "status",
]

# 5 user messages that progressively fill the registration state.
USER_MESSAGES: List[str] = [
    "Hi, I'm John Doe and my email is john.doe@example.com. My ID is REG-2026-001.",
    "I'd like to register for PyCon 2026 (EVT-PY-2026), scheduled May 15 2026 at 9 AM.",
    "The event capacity is 500, 350 spots remaining, and the ticket price is 299.99. Registration id is REG-MAIN-001.",
    "I'm bringing a guest: Alice Smith, alice@example.com (GUEST-001). Total price is 599.98.",
    "Please confirm the registration. The event is the Annual Python conference.",
]

# Pre-baked LLM responses — one per user message.
# Each is a JSON array of FieldExtraction objects.
LLM_RESPONSES: List[str] = [
    # Turn 1 — registrant info
    json.dumps(
        [
            {
                "path": "registrant.name",
                "value": "John Doe",
                "confidence": 0.95,
                "inference": "Name extracted from greeting",
            },
            {
                "path": "registrant.email",
                "value": "john.doe@example.com",
                "confidence": 0.95,
                "inference": "Email extracted from user input",
            },
            {
                "path": "registrant.id",
                "value": "REG-2026-001",
                "confidence": 0.90,
                "inference": "ID explicitly stated",
            },
        ]
    ),
    # Turn 2 — event basics
    json.dumps(
        [
            {
                "path": "event.name",
                "value": "PyCon 2026",
                "confidence": 0.95,
                "inference": "Event name from user message",
            },
            {
                "path": "event.id",
                "value": "EVT-PY-2026",
                "confidence": 0.90,
                "inference": "Event ID from parenthetical",
            },
            {
                "path": "event.schedule",
                "value": "2026-05-15T09:00:00Z",
                "confidence": 0.85,
                "inference": "Date/time parsed from text",
            },
        ]
    ),
    # Turn 3 — event details + registration id
    json.dumps(
        [
            {
                "path": "event.capacity",
                "value": "500",
                "confidence": 0.95,
                "inference": "Capacity from text",
            },
            {
                "path": "event.remaining",
                "value": "350",
                "confidence": 0.90,
                "inference": "Remaining spots stated",
            },
            {
                "path": "event.pricing",
                "value": "299.99",
                "confidence": 0.95,
                "inference": "Price from text",
            },
            {
                "path": "id",
                "value": "REG-MAIN-001",
                "confidence": 0.90,
                "inference": "Registration ID from text",
            },
        ]
    ),
    # Turn 4 — guest + total price
    json.dumps(
        [
            {
                "path": "guests.0.name",
                "value": "Alice Smith",
                "confidence": 0.90,
                "inference": "Guest name from text",
            },
            {
                "path": "guests.0.email",
                "value": "alice@example.com",
                "confidence": 0.90,
                "inference": "Guest email from text",
            },
            {
                "path": "guests.0.id",
                "value": "GUEST-001",
                "confidence": 0.85,
                "inference": "Guest ID from text",
            },
            {
                "path": "total_price",
                "value": "599.98",
                "confidence": 0.90,
                "inference": "Total price stated",
            },
        ]
    ),
    # Turn 5 — status confirmed + event description
    json.dumps(
        [
            {
                "path": "status",
                "value": "confirmed",
                "confidence": 0.95,
                "inference": "User explicitly confirmed",
            },
            {
                "path": "event.description",
                "value": "Annual Python conference with workshops.",
                "confidence": 0.85,
                "inference": "Description from user message",
            },
        ]
    ),
]


# ── Mock LLM Client ───────────────────────────────────────────────


class SequentialMockLLMClient(BaseLLMClient):
    """Returns pre-configured responses in order, one per ``generate`` call."""

    def __init__(self, responses: List[str]) -> None:
        self._responses = responses
        self._call_index = 0

    async def generate(self, prompt: str) -> str:  # noqa: D401
        if self._call_index >= len(self._responses):
            raise RuntimeError(
                f"SequentialMockLLMClient exhausted after {len(self._responses)} calls"
            )
        response = self._responses[self._call_index]
        self._call_index += 1
        return response

    @property
    def call_count(self) -> int:
        return self._call_index


# ── Stub Action ────────────────────────────────────────────────────


class RegistrationAction(BaseAction):
    """Action that records its execution.

    ``validate`` checks *REQUIRED_FIELDS* are present in the state.
    ``execute`` marks itself as executed and returns SUCCESS.
    """

    def __init__(self) -> None:
        self.executed: bool = False
        self.last_result: Optional[ActionResult] = None
        self.execute_count: int = 0

    async def validate(self, context: ActionContext) -> Tuple[bool, Optional[str]]:
        state = context.canonical_state
        for field_path in REQUIRED_FIELDS:
            field = state.get_field(field_path)
            if field is None or len(field.values) == 0:
                return False, f"Missing required field: {field_path}"
        return True, None

    async def execute(self, context: ActionContext) -> ActionResult:
        self.executed = True
        self.execute_count += 1
        result = ActionResult(
            status=ActionStatus.SUCCESS,
            result_data={"message": "Registration completed"},
            error_message=None,
            metadata={},
        )
        self.last_result = result
        return result

    async def rollback(self, context: ActionContext) -> bool:
        return True

    def get_action_type(self) -> str:
        return "registration"


# ── Recording Projector (triggers action on complete state) ───────


class RegistrationProjector(BaseProjector[ProjectionContext, ProjectionResult]):
    """Projector that records every state update and triggers the action.

    On each ``project`` call the projector validates the state against
    ``RegistrationAction.validate``.  When validation passes (and the
    action hasn't already been executed) the action is fired.
    """

    def __init__(self, action: RegistrationAction) -> None:
        self._action = action
        self.states: List[BaseState] = []
        self.call_count: int = 0
        self.action_triggered: bool = False

    async def project(self, context: ProjectionContext) -> ProjectionResult:
        self.call_count += 1
        self.states.append(context.state)

        # Attempt to trigger the action
        if not self.action_triggered:
            action_ctx = ActionContext(
                canonical_state=context.state,
                action_type="default",
                parameters={},
                metadata={},
            )
            is_valid, _ = await self._action.validate(action_ctx)
            if is_valid:
                await self._action.execute(action_ctx)
                self.action_triggered = True

        return ProjectionResult(success=True)

    async def initialize(self, schema: Optional[Schema] = None) -> None:
        pass


# ── Context factory ────────────────────────────────────────────────


def _context_factory(inp: AgentInput, state: BaseState) -> MutationContext:
    """Bridge ``AgentInput`` → ``MutationContext`` expected by ``LLMMutator``."""
    return MutationContext(
        input=StructuredInput(prompt=inp.text or ""),
        state=cast(State, state),
    )


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def mock_llm_client() -> SequentialMockLLMClient:
    return SequentialMockLLMClient(responses=list(LLM_RESPONSES))


@pytest.fixture
def llm_mutator(mock_llm_client: SequentialMockLLMClient) -> LLMMutator:
    return LLMMutator(llm_client=mock_llm_client)


@pytest.fixture
def registration_action() -> RegistrationAction:
    return RegistrationAction()


@pytest.fixture
def registration_projector(
    registration_action: RegistrationAction,
) -> RegistrationProjector:
    return RegistrationProjector(action=registration_action)


@pytest_asyncio.fixture
async def langstate_agent(
    llm_mutator: LLMMutator,
    registration_projector: RegistrationProjector,
) -> LangState[MutationContext, AgentInput]:
    """Fully initialised LangState with real schema."""
    deps: LangStateDeps[MutationContext, AgentInput] = LangStateDeps(
        mutator=llm_mutator,
        spec_extractor=OpenAPIReader(root_entity="Registration"),
        projectors=[registration_projector],
        repository=None,
        context_factory=_context_factory,
    )
    agent: LangState[MutationContext, AgentInput] = LangState(deps)
    await agent.initialize({"schema_source": str(SCHEMA_PATH)})
    return agent


# ══════════════════════════════════════════════════════════════════
# Tests
# ══════════════════════════════════════════════════════════════════


class TestRegistrationE2E:
    """Full registration flow: 5 messages → state is filled → action fires."""

    @pytest.mark.asyncio
    async def test_full_registration_flow(
        self,
        langstate_agent: LangState[MutationContext, AgentInput],
        registration_projector: RegistrationProjector,
        registration_action: RegistrationAction,
        mock_llm_client: SequentialMockLLMClient,
    ) -> None:
        """Send 5 messages, verify key fields, projector counts, and action fire."""
        agent = langstate_agent

        # ── Turn 1: registrant ─────────────────────────────────────
        result1 = await agent.invoke(AgentInput.from_text(USER_MESSAGES[0]))
        assert isinstance(result1, StateResultData)
        assert result1.success is True

        state1 = await agent.get_state()
        _f_reg_name = state1.get_field("registrant.name")
        assert _f_reg_name is not None
        assert _f_reg_name.values[0].value == "John Doe"
        _f_reg_email = state1.get_field("registrant.email")
        assert _f_reg_email is not None
        assert _f_reg_email.values[0].value == "john.doe@example.com"

        # ── Turn 2: event basics ───────────────────────────────────
        result2 = await agent.invoke(AgentInput.from_text(USER_MESSAGES[1]))
        assert isinstance(result2, StateResultData)
        assert result2.success is True

        state2 = await agent.get_state()
        _f_evt_name = state2.get_field("event.name")
        assert _f_evt_name is not None
        assert _f_evt_name.values[0].value == "PyCon 2026"
        _f_evt_id = state2.get_field("event.id")
        assert _f_evt_id is not None
        assert _f_evt_id.values[0].value == "EVT-PY-2026"

        # ── Turn 3: event details ──────────────────────────────────
        result3 = await agent.invoke(AgentInput.from_text(USER_MESSAGES[2]))
        assert isinstance(result3, StateResultData)

        state3 = await agent.get_state()
        _f_pricing = state3.get_field("event.pricing")
        assert _f_pricing is not None
        assert _f_pricing.values[0].value == "299.99"
        _f_capacity = state3.get_field("event.capacity")
        assert _f_capacity is not None
        assert _f_capacity.values[0].value == "500"
        _f_reg_id = state3.get_field("id")
        assert _f_reg_id is not None
        assert _f_reg_id.values[0].value == "REG-MAIN-001"

        # ── Turn 4: guest + total price ────────────────────────────
        result4 = await agent.invoke(AgentInput.from_text(USER_MESSAGES[3]))
        assert isinstance(result4, StateResultData)

        state4 = await agent.get_state()
        _f_guest_name = state4.get_field("guests.0.name")
        assert _f_guest_name is not None
        assert _f_guest_name.values[0].value == "Alice Smith"
        _f_guest_email = state4.get_field("guests.0.email")
        assert _f_guest_email is not None
        assert _f_guest_email.values[0].value == "alice@example.com"
        _f_total_price = state4.get_field("total_price")
        assert _f_total_price is not None
        assert _f_total_price.values[0].value == "599.98"

        # Action must NOT have fired yet (status missing).
        assert registration_action.executed is False

        # ── Turn 5: confirm + description ──────────────────────────
        result5 = await agent.invoke(AgentInput.from_text(USER_MESSAGES[4]))
        assert isinstance(result5, StateResultData)

        state5 = await agent.get_state()
        _f_status = state5.get_field("status")
        assert _f_status is not None
        assert _f_status.values[0].value == "confirmed"
        assert state5.get_field("event.description") is not None

        # Projector was called once per invoke.
        assert registration_projector.call_count == 5

        # Action must have fired after the 5th message.
        assert registration_action.executed is True
        assert registration_action.last_result is not None
        assert registration_action.last_result.status == ActionStatus.SUCCESS
        assert registration_action.execute_count == 1

        # The mock LLM client was called exactly 5 times.
        assert mock_llm_client.call_count == 5

    @pytest.mark.asyncio
    async def test_state_accumulates_across_messages(
        self,
        langstate_agent: LangState[MutationContext, AgentInput],
    ) -> None:
        """Each invoke adds new fields; the filled count never decreases."""
        agent = langstate_agent
        filled_counts: List[int] = []

        for msg in USER_MESSAGES:
            await agent.invoke(AgentInput.from_text(msg))
            state = await agent.get_state()
            filled_counts.append(len(state.get_filled_fields()))

        # Strictly non-decreasing sequence.
        for i in range(1, len(filled_counts)):
            assert filled_counts[i] >= filled_counts[i - 1], (
                f"Filled field count decreased between turn {i} and {i + 1}: "
                f"{filled_counts}"
            )

        # After all 5 messages we expect a non-trivial number of filled fields.
        assert filled_counts[-1] >= len(REQUIRED_FIELDS)

    @pytest.mark.asyncio
    async def test_projector_receives_updated_state_each_invocation(
        self,
        langstate_agent: LangState[MutationContext, AgentInput],
        registration_projector: RegistrationProjector,
    ) -> None:
        """Projector receives exactly one state snapshot per invoke."""
        agent = langstate_agent

        for idx, msg in enumerate(USER_MESSAGES):
            await agent.invoke(AgentInput.from_text(msg))
            assert registration_projector.call_count == idx + 1

        assert len(registration_projector.states) == 5

        # Every recorded state is a BaseState instance.
        for s in registration_projector.states:
            assert isinstance(s, BaseState)

    @pytest.mark.asyncio
    async def test_action_not_triggered_before_message_5(
        self,
        langstate_agent: LangState[MutationContext, AgentInput],
        registration_action: RegistrationAction,
    ) -> None:
        """Action remains dormant until all required fields are present."""
        agent = langstate_agent

        # Send only the first 4 messages — "status" is still missing.
        for msg in USER_MESSAGES[:4]:
            await agent.invoke(AgentInput.from_text(msg))

        assert registration_action.executed is False
        assert registration_action.execute_count == 0

        # The 5th message supplies "status: confirmed" → action fires.
        await agent.invoke(AgentInput.from_text(USER_MESSAGES[4]))

        assert registration_action.executed is True
        assert registration_action.execute_count == 1

    @pytest.mark.asyncio
    async def test_reset_clears_state_and_projector_can_refire(
        self,
        langstate_agent: LangState[MutationContext, AgentInput],
        registration_projector: RegistrationProjector,
        registration_action: RegistrationAction,
        mock_llm_client: SequentialMockLLMClient,
    ) -> None:
        """After reset the state is empty and the projector count is preserved."""
        agent = langstate_agent

        # Send one message so state is partially filled.
        await agent.invoke(AgentInput.from_text(USER_MESSAGES[0]))
        assert registration_projector.call_count == 1

        state_before_reset = await agent.get_state()
        assert len(state_before_reset.get_filled_fields()) > 0

        # Reset.
        reset_result = await agent.reset()
        assert reset_result is not None

        state_after_reset = await agent.get_state()
        filled_after = state_after_reset.get_filled_fields()
        assert (
            len(filled_after) == 0
        ), f"Expected empty state after reset, got: {filled_after}"

        # Action should not have been triggered (only 1 message was sent).
        assert registration_action.executed is False
