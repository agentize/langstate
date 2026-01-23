"""Canonical State interface for LangState.

The Canonical State represents the resolved business state with simple key-value pairs.
Format: {key: value}

This is the state used for executing actions and represents the final resolved values.
"""

from packages.langstate.core.state.canonical.schema import CanonicalStateSchema
from ..base.state import BaseState


class CanonicalState(BaseState[CanonicalStateSchema]):
    """Canonical State interface.

    The Canonical State stores resolved field values in a simple key-value format.
    This is the business state used for executing actions.

    Format:
        {field_id: value}

    Example:
        state = CanonicalStateImpl()
        state.set_field("name", "John Doe")
        state.set_field("email", "john@example.com")

        # Get value
        name = state.get_field("name")  # "John Doe"

        # Convert to dict
        data = state.to_dict()  # {"name": "John Doe", "email": "john@example.com"}
    """

    pass
