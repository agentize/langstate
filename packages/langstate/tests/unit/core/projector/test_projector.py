"""Unit tests for Projector module.

Covers BaseProjector, ProjectionContext, ProjectionResult,
BaseProjectorUI, UIComponentType, UIComponent, UIProjectionContext,
UIProjectionResult, and the _default_conversation_history factory.
"""

# pyright: reportPrivateUsage=false

from typing import Optional

import pytest

from core.projector.base.projector import BaseProjector
from core.projector.base.schema import (
    ProjectionContext,
    ProjectionResult,
    _default_conversation_history,
)
from core.projector.ui.projector import BaseProjectorUI
from core.projector.ui.schema import (
    UIComponent,
    UIComponentType,
    UIProjectionContext,
    UIProjectionResult,
)
from core.spec_extractor.base.schema import Schema
from core.state.state.state import State


# ── Concrete implementations for testing ───────────────────────────


class ConcreteProjector(BaseProjector[ProjectionContext, ProjectionResult]):
    """Minimal concrete projector for testing."""

    def __init__(self) -> None:
        self.project_calls: list[ProjectionContext] = []

    async def project(self, context: ProjectionContext) -> ProjectionResult:
        self.project_calls.append(context)
        return ProjectionResult(success=True)

    async def initialize(self, schema: Optional[Schema] = None) -> None:
        pass


class ConcreteProjectorUI(BaseProjectorUI):
    """Minimal concrete UI projector for testing."""

    async def project(self, context: UIProjectionContext) -> UIProjectionResult:
        return UIProjectionResult(prompt="Hello", is_complete=False)

    async def initialize(self, schema: Optional[Schema] = None) -> None:
        pass

    async def generate_prompt(self, context: UIProjectionContext) -> str:
        return "Generated prompt"

    def map_field_to_component(self, field_key: str) -> UIComponent:
        return UIComponent(
            component_type=UIComponentType.TEXT_INPUT,
            field_id=field_key,
        )


# ════════════════════════════════════════════════════════════════════
# _default_conversation_history factory
# ════════════════════════════════════════════════════════════════════


class TestDefaultConversationHistory:
    """Tests for the _default_conversation_history factory function."""

    def test_returns_empty_list(self) -> None:
        result = _default_conversation_history()
        assert result == []

    def test_returns_new_list_each_call(self) -> None:
        a = _default_conversation_history()
        b = _default_conversation_history()
        a.append({"role": "user", "content": "hi"})
        assert b == []


# ════════════════════════════════════════════════════════════════════
# ProjectionContext model
# ════════════════════════════════════════════════════════════════════


class TestProjectionContext:
    """Tests for ProjectionContext Pydantic model."""

    def test_construction_with_state(self) -> None:
        state = State()
        ctx = ProjectionContext(state=state)
        assert ctx.state is state

    def test_conversation_history_default(self) -> None:
        ctx = ProjectionContext(state=State())
        assert ctx.conversation_history == []

    def test_user_preferences_default(self) -> None:
        ctx = ProjectionContext(state=State())
        assert ctx.user_preferences == {}

    def test_strategy_default(self) -> None:
        ctx = ProjectionContext(state=State())
        assert ctx.strategy == "highest_confidence"

    def test_confidence_threshold_default(self) -> None:
        ctx = ProjectionContext(state=State())
        assert ctx.confidence_threshold == 0.7

    def test_metadata_default(self) -> None:
        ctx = ProjectionContext(state=State())
        assert ctx.metadata == {}

    def test_custom_conversation_history(self) -> None:
        ctx = ProjectionContext(
            state=State(),
            conversation_history=[{"role": "user", "content": "hello"}],
        )
        assert len(ctx.conversation_history) == 1

    def test_custom_strategy(self) -> None:
        ctx = ProjectionContext(state=State(), strategy="latest")
        assert ctx.strategy == "latest"

    def test_custom_confidence_threshold(self) -> None:
        ctx = ProjectionContext(state=State(), confidence_threshold=0.9)
        assert ctx.confidence_threshold == 0.9


# ════════════════════════════════════════════════════════════════════
# ProjectionResult model
# ════════════════════════════════════════════════════════════════════


class TestProjectionResult:
    """Tests for ProjectionResult Pydantic model."""

    def test_default_success(self) -> None:
        result = ProjectionResult()
        assert result.success is True

    def test_default_metadata(self) -> None:
        result = ProjectionResult()
        assert result.metadata == {}

    def test_custom_fields(self) -> None:
        result = ProjectionResult(success=False, metadata={"error": "timeout"})
        assert result.success is False
        assert result.metadata == {"error": "timeout"}


# ════════════════════════════════════════════════════════════════════
# BaseProjector ABC
# ════════════════════════════════════════════════════════════════════


class TestBaseProjector:
    """Tests for BaseProjector abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseProjector()  # type: ignore[abstract]

    def test_concrete_subclass_instantiates(self) -> None:
        proj = ConcreteProjector()
        assert isinstance(proj, BaseProjector)

    @pytest.mark.asyncio
    async def test_project_returns_result(self) -> None:
        proj = ConcreteProjector()
        ctx = ProjectionContext(state=State())
        result = await proj.project(ctx)
        assert isinstance(result, ProjectionResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_notified_delegates_to_project(self) -> None:
        """notified() should call project() and return its result."""
        proj = ConcreteProjector()
        ctx = ProjectionContext(state=State())
        # Use a dummy subject (not actually needed by the method)
        from core.data_structure.observer.subject import Subject

        subject: Subject[ProjectionContext] = Subject()
        result = await proj.notified(subject, ctx)
        assert isinstance(result, ProjectionResult)
        assert len(proj.project_calls) == 1
        assert proj.project_calls[0] is ctx


# ════════════════════════════════════════════════════════════════════
# UIComponentType enum
# ════════════════════════════════════════════════════════════════════


class TestUIComponentType:
    """Tests for UIComponentType enum."""

    def test_has_fourteen_members(self) -> None:
        assert len(UIComponentType) == 14

    def test_all_values_are_strings(self) -> None:
        for member in UIComponentType:
            assert isinstance(member.value, str)

    def test_text_input_value(self) -> None:
        assert UIComponentType.TEXT_INPUT == "text_input"

    def test_select_value(self) -> None:
        assert UIComponentType.SELECT == "select"

    def test_custom_value(self) -> None:
        assert UIComponentType.CUSTOM == "custom"

    def test_all_expected_members_exist(self) -> None:
        expected = {
            "TEXT_INPUT",
            "SELECT",
            "RADIO",
            "CHECKBOX",
            "DATE_PICKER",
            "TIME_PICKER",
            "FILE_UPLOAD",
            "BUTTON",
            "TEXTAREA",
            "NUMBER_INPUT",
            "SLIDER",
            "TOGGLE",
            "AUTOCOMPLETE",
            "CUSTOM",
        }
        actual = {m.name for m in UIComponentType}
        assert actual == expected


# ════════════════════════════════════════════════════════════════════
# UIComponent model
# ════════════════════════════════════════════════════════════════════


class TestUIComponent:
    """Tests for UIComponent Pydantic model."""

    def test_required_fields(self) -> None:
        comp = UIComponent(
            component_type=UIComponentType.TEXT_INPUT,
            field_id="name",
        )
        assert comp.component_type == UIComponentType.TEXT_INPUT
        assert comp.field_id == "name"

    def test_defaults(self) -> None:
        comp = UIComponent(
            component_type=UIComponentType.SELECT,
            field_id="country",
        )
        assert comp.label == ""
        assert comp.placeholder == ""
        assert comp.options == []
        assert comp.validation_rules == {}
        assert comp.disabled is False
        assert comp.required is False
        assert comp.metadata == {}

    def test_custom_fields(self) -> None:
        comp = UIComponent(
            component_type=UIComponentType.SELECT,
            field_id="color",
            label="Favorite Color",
            placeholder="Choose...",
            options=[{"label": "Red", "value": "red"}],
            validation_rules={"required": True},
            disabled=True,
            required=True,
            metadata={"hint": "Pick one"},
        )
        assert comp.label == "Favorite Color"
        assert comp.placeholder == "Choose..."
        assert len(comp.options) == 1
        assert comp.disabled is True
        assert comp.required is True


# ════════════════════════════════════════════════════════════════════
# UIProjectionContext model
# ════════════════════════════════════════════════════════════════════


class TestUIProjectionContext:
    """Tests for UIProjectionContext Pydantic model."""

    def test_inherits_projection_context(self) -> None:
        ctx = UIProjectionContext(state=State())
        assert isinstance(ctx, ProjectionContext)
        assert ctx.strategy == "highest_confidence"

    def test_all_base_defaults_inherited(self) -> None:
        ctx = UIProjectionContext(state=State())
        assert ctx.conversation_history == []
        assert ctx.user_preferences == {}
        assert ctx.metadata == {}


# ════════════════════════════════════════════════════════════════════
# UIProjectionResult model
# ════════════════════════════════════════════════════════════════════


class TestUIProjectionResult:
    """Tests for UIProjectionResult Pydantic model."""

    def test_inherits_projection_result(self) -> None:
        result = UIProjectionResult()
        assert isinstance(result, ProjectionResult)

    def test_defaults(self) -> None:
        result = UIProjectionResult()
        assert result.prompt == ""
        assert result.components == []
        assert result.suggestions == {}
        assert result.is_complete is False
        assert result.next_fields == []
        assert result.success is True

    def test_custom_fields(self) -> None:
        comp = UIComponent(
            component_type=UIComponentType.TEXT_INPUT,
            field_id="name",
        )
        result = UIProjectionResult(
            prompt="What is your name?",
            components=[comp],
            suggestions={"name": ["Alice", "Bob"]},
            is_complete=True,
            next_fields=["email"],
        )
        assert result.prompt == "What is your name?"
        assert len(result.components) == 1
        assert result.is_complete is True
        assert result.next_fields == ["email"]


# ════════════════════════════════════════════════════════════════════
# BaseProjectorUI ABC
# ════════════════════════════════════════════════════════════════════


class TestBaseProjectorUI:
    """Tests for BaseProjectorUI abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseProjectorUI()  # type: ignore[abstract]

    def test_concrete_subclass_instantiates(self) -> None:
        proj = ConcreteProjectorUI()
        assert isinstance(proj, BaseProjectorUI)
        assert isinstance(proj, BaseProjector)

    def test_get_supported_components_returns_all_types(self) -> None:
        proj = ConcreteProjectorUI()
        supported = proj.get_supported_components()
        assert isinstance(supported, list)
        assert len(supported) == 14
        assert set(supported) == set(UIComponentType)

    @pytest.mark.asyncio
    async def test_project_returns_ui_result(self) -> None:
        proj = ConcreteProjectorUI()
        ctx = UIProjectionContext(state=State())
        result = await proj.project(ctx)
        assert isinstance(result, UIProjectionResult)
        assert result.prompt == "Hello"

    @pytest.mark.asyncio
    async def test_generate_prompt(self) -> None:
        proj = ConcreteProjectorUI()
        ctx = UIProjectionContext(state=State())
        prompt = await proj.generate_prompt(ctx)
        assert prompt == "Generated prompt"

    def test_map_field_to_component(self) -> None:
        proj = ConcreteProjectorUI()
        comp = proj.map_field_to_component("email")
        assert isinstance(comp, UIComponent)
        assert comp.field_id == "email"
        assert comp.component_type == UIComponentType.TEXT_INPUT

    @pytest.mark.asyncio
    async def test_notified_delegates_to_project(self) -> None:
        """BaseProjectorUI inherits notified() from BaseProjector."""
        proj = ConcreteProjectorUI()
        from core.data_structure.observer.subject import Subject

        subject: Subject[UIProjectionContext] = Subject()
        ctx = UIProjectionContext(state=State())
        result = await proj.notified(subject, ctx)
        assert isinstance(result, UIProjectionResult)
