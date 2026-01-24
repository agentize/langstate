


from packages.langstate.core.state.base.state import State
from packages.langstate.core.state.canonical.base import BaseCanonicalState
from packages.langstate.core.state.canonical.schema import CanonicalStateSchema


class CanonicalState(State[CanonicalStateSchema], BaseCanonicalState):
    """Canonical State implementation with simple key-value storage.
    
    Inherits common functionality from State and specialized interface from BaseCanonicalState.
    """
    pass