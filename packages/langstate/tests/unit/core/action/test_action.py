"""Unit tests for Action module.

Covers ActionStatus enum, ActionContext / ActionResult Pydantic models,
and BaseAction abstract base class.
"""

from typing import Optional, Tuple

import pytest
from pydantic import ValidationError

from core.action.base.action import BaseAction
from core.action.base.schema import ActionContext, ActionResult, ActionStatus
from core.state.state.state import State


# ── Concrete action implementation for testing ─────────────────────


class ConcreteAction(BaseAction):
    """Minimal concrete action for testing the ABC."""

    async def execute(self, context: ActionContext) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def validate(self, context: ActionContext) -> Tuple[bool, Optional[str]]:
        return (True, None)

    async def rollback(self, context: ActionContext) -> bool:
        return True


# ════════════════════════════════════════════════════════════════════
# ActionStatus enum
# ════════════════════════════════════════════════════════════════════


class TestActionStatus:
    """Tests for ActionStatus enum."""

    def test_has_five_members(self) -> None:
        assert len(ActionStatus) == 5

    def test_pending_value(self) -> None:
        assert ActionStatus.PENDING == "pending"

    def test_running_value(self) -> None:
        assert ActionStatus.RUNNING == "running"

    def test_success_value(self) -> None:
        assert ActionStatus.SUCCESS == "success"

    def test_failed_value(self) -> None:
        assert ActionStatus.FAILED == "failed"

    def test_cancelled_value(self) -> None:
        assert ActionStatus.CANCELLED == "cancelled"

    def test_members_are_strings(self) -> None:
        for member in ActionStatus:
            assert isinstance(member.value, str)


# ════════════════════════════════════════════════════════════════════
# ActionContext model
# ════════════════════════════════════════════════════════════════════


class TestActionContext:
    """Tests for ActionContext Pydantic model."""

    def test_construction_with_required_fields(self) -> None:
        state = State()
        ctx = ActionContext(canonical_state=state)
        assert ctx.canonical_state is state

    def test_action_type_default(self) -> None:
        ctx = ActionContext(canonical_state=State())
        assert ctx.action_type == "default"

    def test_parameters_default_empty(self) -> None:
        ctx = ActionContext(canonical_state=State())
        assert ctx.parameters == {}

    def test_metadata_default_empty(self) -> None:
        ctx = ActionContext(canonical_state=State())
        assert ctx.metadata == {}

    def test_custom_action_type(self) -> None:
        ctx = ActionContext(
            canonical_state=State(),
            action_type="submit",
        )
        assert ctx.action_type == "submit"

    def test_custom_parameters(self) -> None:
        params: dict[str, object] = {"retry": True, "timeout": 30}
        ctx = ActionContext(
            canonical_state=State(),
            parameters=params,
        )
        assert ctx.parameters == params

    def test_custom_metadata(self) -> None:
        meta: dict[str, object] = {"session_id": "abc123"}
        ctx = ActionContext(
            canonical_state=State(),
            metadata=meta,
        )
        assert ctx.metadata == meta


# ════════════════════════════════════════════════════════════════════
# ActionResult model
# ════════════════════════════════════════════════════════════════════


class TestActionResult:
    """Tests for ActionResult Pydantic model."""

    def test_construction_with_status(self) -> None:
        result = ActionResult(status=ActionStatus.SUCCESS)
        assert result.status == ActionStatus.SUCCESS

    def test_result_data_default_empty(self) -> None:
        result = ActionResult(status=ActionStatus.PENDING)
        assert result.result_data == {}

    def test_error_message_default_none(self) -> None:
        result = ActionResult(status=ActionStatus.FAILED)
        assert result.error_message is None

    def test_metadata_default_empty(self) -> None:
        result = ActionResult(status=ActionStatus.SUCCESS)
        assert result.metadata == {}

    def test_custom_result_data(self) -> None:
        result = ActionResult(
            status=ActionStatus.SUCCESS,
            result_data={"user_id": "u123"},
        )
        assert result.result_data == {"user_id": "u123"}

    def test_custom_error_message(self) -> None:
        result = ActionResult(
            status=ActionStatus.FAILED,
            error_message="Connection timed out",
        )
        assert result.error_message == "Connection timed out"

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            ActionResult(status="invalid_status")  # type: ignore[arg-type]

    def test_all_status_values_accepted(self) -> None:
        for status in ActionStatus:
            result = ActionResult(status=status)
            assert result.status == status


# ════════════════════════════════════════════════════════════════════
# BaseAction ABC
# ════════════════════════════════════════════════════════════════════


class TestBaseAction:
    """Tests for BaseAction abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseAction()  # type: ignore[abstract]

    def test_concrete_subclass_instantiates(self) -> None:
        action = ConcreteAction()
        assert isinstance(action, BaseAction)

    def test_get_action_type_returns_default(self) -> None:
        action = ConcreteAction()
        assert action.get_action_type() == "default"

    @pytest.mark.asyncio
    async def test_execute_returns_result(self) -> None:
        action = ConcreteAction()
        ctx = ActionContext(canonical_state=State())
        result = await action.execute(ctx)
        assert isinstance(result, ActionResult)
        assert result.status == ActionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_validate_returns_tuple(self) -> None:
        action = ConcreteAction()
        ctx = ActionContext(canonical_state=State())
        is_valid, error = await action.validate(ctx)
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_rollback_returns_bool(self) -> None:
        action = ConcreteAction()
        ctx = ActionContext(canonical_state=State())
        result = await action.rollback(ctx)
        assert result is True

    def test_get_action_type_can_be_overridden(self) -> None:
        class CustomAction(ConcreteAction):
            def get_action_type(self) -> str:
                return "custom_submit"

        action = CustomAction()
        assert action.get_action_type() == "custom_submit"
