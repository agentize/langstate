"""State Repository module.

This module provides the StateRepository interface and implementations
for managing state persistence and retrieval following the Repository pattern.
"""

from .base import BaseStateRepository
from .memory import InMemoryStateRepository

__all__ = [
    "BaseStateRepository",
    "InMemoryStateRepository",
]
