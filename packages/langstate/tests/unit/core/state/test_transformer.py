"""Unit tests for BaseStateTransformer ABC."""

from typing import Any

import pytest

from core.state.transformer.base import BaseStateTransformer
from core.state.base.base import BaseDAHState
from core.state.state.state import State


class ConcreteTransformer(BaseStateTransformer):
    """Minimal concrete transformer for testing."""

    def transform(self, state: State) -> BaseDAHState[Any]:
        return state


class TestBaseStateTransformer:
    """Tests for BaseStateTransformer abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseStateTransformer()  # type: ignore[abstract]

    def test_concrete_subclass_instantiates(self) -> None:
        t = ConcreteTransformer()
        assert isinstance(t, BaseStateTransformer)

    def test_transform_returns_state(self) -> None:
        t = ConcreteTransformer()
        state = State()
        result = t.transform(state)
        assert result is state
