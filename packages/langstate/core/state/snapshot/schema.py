from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar

from core.state.base.base import BaseBasicState

TState = TypeVar("TState", bound=BaseBasicState[Any])


@dataclass(frozen=True)
class Snapshot(Generic[TState]):
    """Immutable snapshot of a state at a point in time.

    Attributes:
        mutator_id: Identifier of the mutator that produced this state
        timestamp: When the snapshot was recorded
        state: Deep copy of the state at snapshot time
        index: Sequential index of this snapshot (0-based)
    """

    mutator_id: str
    timestamp: datetime
    state: TState
    index: int
