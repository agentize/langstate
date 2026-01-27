from typing import Any, cast

from packages.langstate.core.schema_reader.base.schema import Schema, SchemaField
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
            default_value = self._process_field_value(field)
            canonical_state.set_field(field_id, default_value)  # type: ignore
        
        return canonical_state

    def _process_field_value(self, field: SchemaField) -> dict[str, Any] | None:
        """Process field value, handling nested fields if present.

        Args:
            field: SchemaField to process

        Returns:
            Processed value (dict for nested fields, or default_value)
        """
        default_value = field.default_value
        
        # If default_value contains nested SchemaField objects, process them recursively
        if isinstance(default_value, dict) and default_value:
            # Check if this is a dict of SchemaField objects (nested fields)
            dict_value = cast(dict[str, Any], default_value)
            first_value = next(iter(dict_value.values()), None)
            if isinstance(first_value, SchemaField):
                result: dict[str, Any] = {}
                for nested_field_id, nested_field in dict_value.items():
                    if isinstance(nested_field, SchemaField):
                        result[nested_field_id] = self._process_field_value(nested_field)
                return result
        
        # Return as-is if not a nested SchemaField dict
        return cast(dict[str, Any] | None, default_value)

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
        
        # Add values from canonical state as high-confidence values (including nested fields)
        self._add_values_to_interpretive_state(interpretive_state, canonical_dict)
        
        return interpretive_state

    def _add_values_to_interpretive_state(
        self, 
        interpretive_state: InterpretiveState, 
        values_dict: dict[str, Any],
        prefix: str = ""
    ) -> None:
        """Recursively add values to interpretive state, handling nested dicts.

        Args:
            interpretive_state: InterpretiveState to add values to
            values_dict: Dictionary of values to add
            prefix: Field ID prefix for nested fields
        """
        for field_id, value in values_dict.items():
            full_field_id = f"{prefix}{field_id}" if prefix else field_id
            
            # If value is a dict, recursively add nested values
            if isinstance(value, dict):
                # Cast to dict for type checker after isinstance check
                nested_dict = cast(dict[str, Any], value)
                # Add nested fields with dot notation
                self._add_values_to_interpretive_state(
                    interpretive_state, 
                    nested_dict, 
                    f"{full_field_id}."
                )
            else:
                # Add value with confidence 1.0 since it comes from resolved state
                # Always add values, even if None, to match canonical state structure
                interpretive_state.add_value(
                    full_field_id,
                    ValueConfidence(value=value, confidence=1.0)
                )

