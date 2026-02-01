"""State Factory module.

This module provides factories for creating state instances,
following the Factory pattern (SRP - separates creation from use).
"""

from .state_factory import StateFactory
from .base import BaseStateFactory

__all__ = [
    "BaseStateFactory",
    "StateFactory",
]
