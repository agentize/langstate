"""State Factory implementation using DAH-based states."""

from typing import Any, cast

from core.schema_reader.base.schema import Schema, SchemaField
from core.state.canonical.base import BaseCanonicalState
from core.state.canonical.schema import CanonicalFieldValue
from core.state.canonical.state import CanonicalState
from core.state.factory.base import BaseStateFactory
from core.state.interpretive.base import BaseInterpretiveState
from core.state.interpretive.schema import ValueConfidence
from core.state.interpretive.state import InterpretiveState


class StateFactory(BaseStateFactory):
    """Default implementation of state factory.

    Creates standard CanonicalState and InterpretiveState instances
    using DAH-based storage with path-based field addressing.
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
        canonical_state = CanonicalState()
        
        # Initialize only leaf fields with primitive values from schema
        # Uses dot notation for paths: "field", "parent.child", "array.0.field"
        self._initialize_leaf_fields(canonical_state, schema.root, prefix="")
        
        return canonical_state

    def _initialize_leaf_fields(
        self,
        state: CanonicalState,
        fields: dict[str, SchemaField],
        prefix: str
    ) -> None:
        """Recursively initialize only leaf fields with primitive values.

        Args:
            state: CanonicalState to populate
            fields: Dictionary of field_id to SchemaField
            prefix: Path prefix for nested fields (e.g., "parent." or "array.0.")
        """
        for field_id, field in fields.items():
            full_path = f"{prefix}{field_id}" if prefix else field_id
            default_value = field.default_value
            
            # Check if default_value is a dict that contains SchemaFields (nested object)
            is_nested_schema = False
            if isinstance(default_value, dict) and default_value:
                dict_value = cast(dict[str, Any], default_value)
                first_value = next(iter(dict_value.values()), None)
                
                if isinstance(first_value, SchemaField):
                    # This is a nested object - recurse into it
                    # Don't create a node for the parent, only for leaf fields
                    nested_fields = cast(dict[str, SchemaField], dict_value)
                    self._initialize_leaf_fields(state, nested_fields, prefix=f"{full_path}.")
                    is_nested_schema = True
            
            # This is a leaf field - set the primitive value
            # value can be: None, str, int, float, bool, list (but NOT dict with SchemaFields)
            if not is_nested_schema:
                # For leaf fields, use the value from the SchemaField's default_value
                # If default_value is None, that's a valid primitive value
                state.set_field(full_path, cast(CanonicalFieldValue, default_value))

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
        interpretive_state = InterpretiveState()
        
        # Get all fields from canonical state
        # Each canonical leaf field gets corresponding interpretive node
        for path, value in canonical_state.iter_fields():
            # Add value with confidence 1.0 since it comes from schema default
            # The primitive value goes into values: [{value: <primitive>, confidence: 1.0}]
            interpretive_state.add_value(
                path,
                ValueConfidence(value=value, confidence=1.0)
            )
        
        return interpretive_state

