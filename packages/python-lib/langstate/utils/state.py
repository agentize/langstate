"""
State-related utility functions for assistant services.

This module contains functions for managing and manipulating assistant states.
"""

from copy import deepcopy
from studio.services.assistant.models import DynamicAssistantState, AssistantInfo
from loguru import logger


def sanitize_state_fields(state: DynamicAssistantState, field_names: list[str]) -> DynamicAssistantState:
    """
    Sanitize the flow state by removing sensitive fields before sending back to user.
    Removes specified field names from all fields.

    Args:
        state: The current assistant state containing fields
        field_names: List of field attribute names to remove from each field

    Returns:
        Sanitized state with specified fields removed
    """
    try:
        # Create a deep copy to avoid modifying the original state
        sanitized_state = deepcopy(state)

        # Remove sensitive fields from each field in the state
        for field in sanitized_state["fields"]:
            # Remove each specified field name if it exists
            for field_name in field_names:
                if hasattr(field, field_name):
                    setattr(field, field_name, None)

        logger.info(
            f"Sanitized flow state, removed sensitive fields {field_names} from {len(sanitized_state['fields'])} fields"
        )

        return sanitized_state

    except Exception as e:
        logger.error(f"Failed to sanitize flow state: {e}")
        # Return original state if sanitization fails to avoid breaking the flow
        return state


def get_intent_type_description(intent_type: str) -> str:
    """
    Return a human-readable description for the given intent_type.
    """
    intent_type = (intent_type or "").upper()
    if intent_type == "UPDATE":
        return "The user wants to provide, edit, or confirm a value for one or more fields."
    elif intent_type == "SUGGEST":
        return "The user is asking for suggestions, options, or possible values for a field."
    elif intent_type == "UNRELATED":
        return "The user's message is unrelated to the form or its fields."
    else:
        return "Unknown intent type."


def get_info(state: DynamicAssistantState) -> AssistantInfo:
    """
    Return AssistantInfo about the state. Tries state.info, attempts to cast to AssistantInfo, defaults to a basic AssistantInfo if not present or None.
    Never returns None.
    """
    info = getattr(state, "info", None)
    if info is None:
        return AssistantInfo(name="Assistant", description="AI Assistant", avatar_url=None)
    try:
        if isinstance(info, dict):
            return AssistantInfo(**info)
        if isinstance(info, AssistantInfo):
            return info
    except Exception:
        pass
    # Fallback to default if casting fails
    return AssistantInfo(name="Assistant", description="AI Assistant", avatar_url=None)
