"""State module exports."""

from .base.base import BaseState
from .interpretive.schema import Inference, ValueConfidence
from .factory.state_factory import StateFactory
from .base import (
    State,
)
from .canonical import (
    BaseCanonicalState,
    CanonicalStateSchema,
)
from .interpretive import (
    BaseInterpretiveState,
    InterpretiveFieldState,
    InterpretiveStateSchema,
    SnapshotStore,
)
from .repository import (
    IStateRepository,
    StateRepositoryBase,
    InMemoryStateRepository,
)
from .factory import (
    BaseStateFactory,
)

__all__ = [
    # Base
    "BaseState",
    "Inference",
    "State",
    "ValueConfidence",
    # Canonical
    "BaseCanonicalState",
    "CanonicalStateSchema",
    # Interpretive
    "BaseInterpretiveState",
    "InterpretiveFieldState",
    "InterpretiveStateSchema",
    "SnapshotStore",
    # Repository (SOLID: SRP, DIP)
    "IStateRepository",
    "StateRepositoryBase",
    "InMemoryStateRepository",
    # Factory (SOLID: SRP)
    "BaseStateFactory",
    "StateFactory",
]
