"""Base interface for state transformers."""

from abc import ABC, abstractmethod
from typing import Any

from core.state.base.base import BaseDAHState
from core.state.state.state import State


class BaseStateTransformer(ABC):
    """Abstract base for transformers that convert a State into a BaseDahState."""

    @abstractmethod
    def transform(self, state: State) -> BaseDAHState[Any]:
        """Transform the given State into a BaseDahState.

        Args:
            state: The interpretive state to transform.

        Returns:
            A BaseDahState representation of the given state.
        """
