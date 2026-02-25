from __future__ import annotations

from .subject import Subject

"""
Generic observer pattern interfaces and implementations.
"""

from .base import BaseObserver, BaseSubject

__all__ = [
    "BaseObserver",
    "BaseSubject",
    "Subject",
]
