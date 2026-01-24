from packages.langstate.core.schema_reader.base.schema import Schema
from packages.langstate.core.state.canonical.base import BaseCanonicalState
from packages.langstate.core.state.canonical.state import CanonicalState
from packages.langstate.core.state.factory.base import BaseStateFactory
from packages.langstate.core.state.interpretive.base import BaseInterpretiveState
from packages.langstate.core.state.interpretive.schema import ValueConfidence
from packages.langstate.core.state.interpretive.state import InterpretiveState


class StateFactory(BaseStateFactory):
    """Default implementation of state factory.

    Creates standard CanonicalState and InterpretiveState instances.
    Can be extended for custom state implementations.
    """

    def create_canonical_state(
        self,
        schema: Schema,
    ) -> BaseCanonicalState:
        """Create a new canonical state instance.

        Args:
            schema: Schema to initialize from

        Returns:
            New CanonicalState instance with fields initialized from schema
        """
        # Create canonical state using new implementation
        canonical_state = CanonicalState()
        
        # Initialize fields with default values from schema
        for field_id, field in schema.root.items():
            # Use default value if provided, otherwise None
            default_value = field.default_value
            canonical_state.set_field(field_id, default_value)  # type: ignore
        
        return canonical_state

    def create_interpretive_state(
        self,
        canonical_state: BaseCanonicalState,
    ) -> BaseInterpretiveState:
        """Create a new interpretive state instance.

        Args:
            canonical_state: Canonical state to derive values from

        Returns:
            New InterpretiveState instance with values derived from canonical state
        """
        # Create interpretive state using new implementation
        interpretive_state = InterpretiveState()
        
        # Get all fields from canonical state
        canonical_dict = canonical_state.to_dict()
        
        # Add values from canonical state as high-confidence values
        for field_id, value in canonical_dict.items():
            if value is not None:
                # Add value with confidence 1.0 since it comes from resolved state
                interpretive_state.add_value(
                    field_id,
                    ValueConfidence(value=value, confidence=1.0)
                )
        
        return interpretive_state

