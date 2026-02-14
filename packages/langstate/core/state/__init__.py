"""State module exports."""

from .base import BaseState
from .schema import (
    Inference,
    ValueConfidence,
    StateField,
    StateSchema,
)
from .state import State
from .canonical import (
    BaseCanonicalState,
    CanonicalStateSchema,
)
from .interpretive import (
    BaseInterpretiveState,
    InterpretiveFieldState,
    InterpretiveStateSchema,
    BaseSnapshotStore,
)
from .repository import (
    BaseStateRepository,
    InMemoryStateRepository,
)

__all__ = [
    # Base
    "BaseState",
    "Inference",
    "State",
    "StateSchema",
    "StateField",
    "ValueConfidence",
    # Canonical
    "BaseCanonicalState",
    "CanonicalStateSchema",
    # Interpretive
    "BaseInterpretiveState",
    "InterpretiveFieldState",
    "InterpretiveStateSchema",
    "BaseSnapshotStore",
    # Repository (SOLID: SRP, DIP)
    "BaseStateRepository",
    "InMemoryStateRepository",
]
