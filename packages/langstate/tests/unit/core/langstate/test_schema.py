"""Unit tests for LangState schema models.

Covers InputType, AgentInput (factory classmethods and is_empty),
InteractionType, InteractionRequest, StateResultData, LangStateConfig,
and LangStateDeps.
"""

from collections.abc import Callable

from core.langstate.base.schema import (
    AgentInput,
    InputType,
    InteractionRequest,
    InteractionType,
    LangStateConfig,
    LangStateDeps,
    StateResultData,
)
from core.state.state.state import State

from core.state.state.base import BaseState


# ════════════════════════════════════════════════════════════════════
# InputType enum
# ════════════════════════════════════════════════════════════════════


class TestInputType:
    """Tests for InputType enum."""

    def test_has_six_members(self) -> None:
        assert len(InputType) == 6

    def test_text_value(self) -> None:
        assert InputType.TEXT == "text"

    def test_action_value(self) -> None:
        assert InputType.ACTION == "action"

    def test_selection_value(self) -> None:
        assert InputType.SELECTION == "selection"

    def test_confirmation_value(self) -> None:
        assert InputType.CONFIRMATION == "confirmation"

    def test_file_value(self) -> None:
        assert InputType.FILE == "file"

    def test_system_value(self) -> None:
        assert InputType.SYSTEM == "system"


# ════════════════════════════════════════════════════════════════════
# AgentInput – factory classmethods
# ════════════════════════════════════════════════════════════════════


class TestAgentInputFromText:
    """Tests for AgentInput.from_text factory."""

    def test_sets_text_type(self) -> None:
        inp = AgentInput.from_text("hello")
        assert inp.input_type == InputType.TEXT

    def test_sets_text_field(self) -> None:
        inp = AgentInput.from_text("hello")
        assert inp.text == "hello"

    def test_other_fields_are_none(self) -> None:
        inp = AgentInput.from_text("x")
        assert inp.action is None
        assert inp.action_data is None
        assert inp.selection is None
        assert inp.field_id is None
        assert inp.confirmed is None
        assert inp.files is None
        assert inp.metadata is None


class TestAgentInputFromAction:
    """Tests for AgentInput.from_action factory."""

    def test_sets_action_type(self) -> None:
        inp = AgentInput.from_action("submit")
        assert inp.input_type == InputType.ACTION

    def test_sets_action_field(self) -> None:
        inp = AgentInput.from_action("submit")
        assert inp.action == "submit"

    def test_data_defaults_to_none(self) -> None:
        inp = AgentInput.from_action("submit")
        assert inp.action_data is None

    def test_data_can_be_provided(self) -> None:
        inp = AgentInput.from_action("submit", data={"form_id": "reg"})
        assert inp.action_data == {"form_id": "reg"}

    def test_text_is_none(self) -> None:
        inp = AgentInput.from_action("submit")
        assert inp.text is None


class TestAgentInputFromSelection:
    """Tests for AgentInput.from_selection factory."""

    def test_sets_selection_type(self) -> None:
        inp = AgentInput.from_selection(["opt1", "opt2"])
        assert inp.input_type == InputType.SELECTION

    def test_sets_selection_field(self) -> None:
        inp = AgentInput.from_selection(["opt1"])
        assert inp.selection == ["opt1"]

    def test_field_id_defaults_to_none(self) -> None:
        inp = AgentInput.from_selection(["opt1"])
        assert inp.field_id is None

    def test_field_id_can_be_provided(self) -> None:
        inp = AgentInput.from_selection(["opt1"], field_id="color")
        assert inp.field_id == "color"

    def test_text_is_none(self) -> None:
        inp = AgentInput.from_selection(["opt1"])
        assert inp.text is None


class TestAgentInputFromConfirmation:
    """Tests for AgentInput.from_confirmation factory."""

    def test_sets_confirmation_type(self) -> None:
        inp = AgentInput.from_confirmation("email", True)
        assert inp.input_type == InputType.CONFIRMATION

    def test_sets_confirmed_true(self) -> None:
        inp = AgentInput.from_confirmation("email", True)
        assert inp.confirmed is True

    def test_sets_confirmed_false(self) -> None:
        inp = AgentInput.from_confirmation("email", False)
        assert inp.confirmed is False

    def test_sets_field_id(self) -> None:
        inp = AgentInput.from_confirmation("email", True)
        assert inp.field_id == "email"

    def test_text_is_none(self) -> None:
        inp = AgentInput.from_confirmation("email", True)
        assert inp.text is None


# ════════════════════════════════════════════════════════════════════
# AgentInput.is_empty
# ════════════════════════════════════════════════════════════════════


class TestAgentInputIsEmpty:
    """Tests for AgentInput.is_empty – all branch combinations."""

    def test_default_input_is_empty(self) -> None:
        """Default AgentInput (all None) should be empty."""
        inp = AgentInput()
        assert inp.is_empty() is True

    def test_text_set_not_empty(self) -> None:
        inp = AgentInput(text="hello")
        assert inp.is_empty() is False

    def test_action_set_not_empty(self) -> None:
        inp = AgentInput(action="submit")
        assert inp.is_empty() is False

    def test_selection_none_is_empty(self) -> None:
        inp = AgentInput(selection=None)
        assert inp.is_empty() is True

    def test_selection_empty_list_is_empty(self) -> None:
        """Empty selection list should still count as empty."""
        inp = AgentInput(selection=[])
        assert inp.is_empty() is True

    def test_selection_non_empty_not_empty(self) -> None:
        inp = AgentInput(selection=["opt1"])
        assert inp.is_empty() is False

    def test_confirmed_set_not_empty(self) -> None:
        inp = AgentInput(confirmed=True)
        assert inp.is_empty() is False

    def test_confirmed_false_not_empty(self) -> None:
        inp = AgentInput(confirmed=False)
        assert inp.is_empty() is False

    def test_files_none_is_empty(self) -> None:
        inp = AgentInput(files=None)
        assert inp.is_empty() is True

    def test_files_empty_list_is_empty(self) -> None:
        inp = AgentInput(files=[])
        assert inp.is_empty() is True

    def test_files_non_empty_not_empty(self) -> None:
        inp = AgentInput(files=[{"name": "doc.pdf"}])
        assert inp.is_empty() is False

    def test_only_metadata_still_empty(self) -> None:
        """Metadata alone doesn't count as non-empty."""
        inp = AgentInput(metadata={"session": "abc"})
        assert inp.is_empty() is True

    def test_combined_all_set(self) -> None:
        inp = AgentInput(
            text="hi",
            action="go",
            selection=["a"],
            confirmed=True,
            files=[{"name": "f"}],
        )
        assert inp.is_empty() is False


# ════════════════════════════════════════════════════════════════════
# InteractionType enum
# ════════════════════════════════════════════════════════════════════


class TestInteractionType:
    """Tests for InteractionType enum."""

    def test_has_five_members(self) -> None:
        assert len(InteractionType) == 5

    def test_prompt_value(self) -> None:
        assert InteractionType.PROMPT == "prompt"

    def test_selection_value(self) -> None:
        assert InteractionType.SELECTION == "selection"

    def test_confirmation_value(self) -> None:
        assert InteractionType.CONFIRMATION == "confirmation"

    def test_action_value(self) -> None:
        assert InteractionType.ACTION == "action"

    def test_complete_value(self) -> None:
        assert InteractionType.COMPLETE == "complete"


# ════════════════════════════════════════════════════════════════════
# InteractionRequest model
# ════════════════════════════════════════════════════════════════════


class TestInteractionRequest:
    """Tests for InteractionRequest Pydantic model."""

    def test_construction_with_type(self) -> None:
        req = InteractionRequest(interaction_type=InteractionType.PROMPT)
        assert req.interaction_type == InteractionType.PROMPT

    def test_prompt_default(self) -> None:
        req = InteractionRequest(interaction_type=InteractionType.PROMPT)
        assert req.prompt == ""

    def test_components_default(self) -> None:
        req = InteractionRequest(interaction_type=InteractionType.PROMPT)
        assert req.components == []

    def test_options_default(self) -> None:
        req = InteractionRequest(interaction_type=InteractionType.SELECTION)
        assert req.options == {}

    def test_state_default_none(self) -> None:
        req = InteractionRequest(interaction_type=InteractionType.PROMPT)
        assert req.state is None

    def test_pending_fields_default(self) -> None:
        req = InteractionRequest(interaction_type=InteractionType.PROMPT)
        assert req.pending_fields == []

    def test_metadata_default(self) -> None:
        req = InteractionRequest(interaction_type=InteractionType.PROMPT)
        assert req.metadata == {}

    def test_custom_fields(self) -> None:
        state = State()
        req = InteractionRequest(
            interaction_type=InteractionType.SELECTION,
            prompt="Choose one",
            options={"color": ["red", "blue"]},
            state=state,
            pending_fields=["name", "email"],
            metadata={"session": "s1"},
        )
        assert req.prompt == "Choose one"
        assert "color" in req.options
        assert req.state is state
        assert req.pending_fields == ["name", "email"]


# ════════════════════════════════════════════════════════════════════
# StateResultData model
# ════════════════════════════════════════════════════════════════════


class TestStateResultData:
    """Tests for StateResultData Pydantic model."""

    def test_construction_with_state(self) -> None:
        state = State()
        result = StateResultData(state=state)
        assert result.state is state

    def test_success_default_true(self) -> None:
        result = StateResultData(state=State())
        assert result.success is True

    def test_data_default_empty(self) -> None:
        result = StateResultData(state=State())
        assert result.data == {}

    def test_metadata_default_empty(self) -> None:
        result = StateResultData(state=State())
        assert result.metadata == {}

    def test_custom_fields(self) -> None:
        result = StateResultData(
            state=State(),
            success=False,
            data={"user_id": "abc"},
            metadata={"elapsed": 1.5},
        )
        assert result.success is False
        assert result.data == {"user_id": "abc"}
        assert result.metadata == {"elapsed": 1.5}


# ════════════════════════════════════════════════════════════════════
# LangStateConfig model
# ════════════════════════════════════════════════════════════════════


class TestLangStateConfig:
    """Tests for LangStateConfig Pydantic model."""

    def test_all_defaults(self) -> None:
        config = LangStateConfig()
        assert config.schema_source is None
        assert config.confidence_threshold == 0.7
        assert config.require_confirmation is False
        assert config.conversation_history_limit == 100
        assert config.metadata == {}

    def test_custom_fields(self) -> None:
        config = LangStateConfig(
            schema_source="/path/to/schema.yaml",
            confidence_threshold=0.9,
            require_confirmation=True,
            conversation_history_limit=50,
            metadata={"env": "test"},
        )
        assert config.schema_source == "/path/to/schema.yaml"
        assert config.confidence_threshold == 0.9
        assert config.require_confirmation is True
        assert config.conversation_history_limit == 50
        assert config.metadata == {"env": "test"}


# ════════════════════════════════════════════════════════════════════
# LangStateDeps model
# ════════════════════════════════════════════════════════════════════


class TestLangStateDeps:
    """Tests for LangStateDeps Pydantic model."""

    def test_minimal_construction(self) -> None:
        deps: LangStateDeps[None, object] = LangStateDeps(
            context_factory=lambda inp, state: None,
        )
        assert deps.mutator is None
        assert deps.spec_extractor is None
        assert deps.projectors is None
        assert deps.repository is None
        assert deps.state_id is None

    def test_context_factory_is_callable(self) -> None:
        factory: Callable[[object, BaseState], dict[str, str]] = lambda inp, state: {
            "text": ""
        }
        deps: LangStateDeps[dict[str, str], object] = LangStateDeps(
            context_factory=factory
        )
        assert deps.context_factory is factory
