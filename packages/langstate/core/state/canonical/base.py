"""Canonical State interface for LangState.

The Canonical State represents the resolved business state with simple key-value pairs.
Format: {key: value}

This is the state used for executing actions and represents the final resolved values.
Uses DAH for internal storage with field paths as node identifiers.
"""

from core.state.canonical.schema import CanonicalFieldValue
from ..base.base import BaseState


class BaseCanonicalState(BaseState[CanonicalFieldValue]):
    """Canonical State interface.

    The Canonical State stores resolved field values in a simple key-value format.
    This is the business state used for executing actions.
    Uses DAH internally with path-based field addressing.

    Format:
        {field_path: value}

    Example:
        state = CanonicalStateImpl()
        state.set_field("name", "John Doe")
        state.set_field("email", "john@example.com")
        state.set_field("guests.0.name", "Jane Doe")  # Nested array element

        # Get value
        name = state.get_field("name")  # "John Doe"
        guest_name = state.get_field("guests.0.name")  # "Jane Doe"

        # Get all fields
        data = state.get_all_fields()
    """

    pass
