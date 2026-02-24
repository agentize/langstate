"""Snapshot data model for LangState.

A Snapshot is an immutable wrapper around a state at a point in time,
tagged with metadata about when and how it was created.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from core.state.base.base import BaseDAHState

TState = TypeVar("TState", bound=BaseDAHState[Any])


@dataclass(frozen=True)
class Snapshot(Generic[TState]):
    """Immutable snapshot of a state at a point in time.

    Attributes:
        mutator_id: Identifier of the mutator that produced this state
        timestamp: When the snapshot was recorded (UTC)
        state: The state at snapshot time
        index: Sequential version index of this snapshot (0-based)
        snapshot_type: Whether this is a full keyframe or a delta reference
    """

    mutator_id: str
    timestamp: datetime
    state: TState
    index: int
    snapshot_type: Literal["keyframe", "delta"] = "keyframe"
