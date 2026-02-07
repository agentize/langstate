from __future__ import annotations

"""
Generic observer pattern interfaces and implementations.
"""

from .base import BaseObserver, BaseSubject
from .observer import Subject

__all__ = [
    "BaseObserver",
    "BaseSubject",
    "Subject",
]
