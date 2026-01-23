"""Pydantic schemas for Canonical State module.

This module contains all data models used by the Canonical State.
Canonical State uses simple key-value format for business logic.
"""

from typing import Dict

from pydantic import RootModel


class CanonicalStateSchema(RootModel[Dict[str, object]]):
    """Canonical state representation: simple key-value mapping.

    Format: {key: value}

    Example:
        {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
    """

    pass
