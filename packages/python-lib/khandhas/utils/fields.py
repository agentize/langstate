"""
Field-related utility functions for the assistant service.
"""

from typing import List, Dict, Any, cast
import json


def is_state_untouched(state: DynamicAssistantState) -> bool:
    """
    Check if the assistant state is new, all fields' status are `untouched`.

    Args:
        state: The current assistant state containing fields

    Returns:
        True if the state is new, False otherwise
    """
    for field in state["fields"]:
        if get_status(field) != "untouched":
            return False
    return True


def find_field_by_name(state: DynamicAssistantState, field_name: str) -> DynamicField | None:
    """
    Find a field by its name in the assistant state.

    Args:
        state: The current assistant state containing fields
        field_name: Name of the field to find
    Returns:
        DynamicField object if found, None otherwise
    """
    for field in state["fields"]:
        if field.name == field_name:
            return field
    return None


def get_field_dependencies(
    state: DynamicAssistantState, field_name: str, statuses: list[FieldStatus]
) -> list[DynamicField]:
    """
    Find all dependencies of a given field that match any of the specified statuses.

    Args:
        state: The current assistant state containing fields
        field_name: Name of the field to find dependencies for
        statuses: List of FieldStatus values to match against

    Returns:
        List of DynamicField objects that are dependencies and match the statuses
    """
    # Find the target field
    target_field = find_field_by_name(state, field_name)

    if target_field is None:
        return []

    # Find all fields that this field depends on and match the specified statuses
    dependencies = []
    for field in state["fields"]:
        if field.name in target_field.depends_on and field.status in statuses:
            dependencies.append(field)

    return dependencies


def get_ready_for_generation_fields(state: DynamicAssistantState) -> list[DynamicField]:
    """
    Find all fields that are untouched but whose dependencies have been satisfied.

    A field is ready for generation if:
    1. Its status is "untouched"
    2. All of its dependencies have status "generated", "edited", or "validated"

    Args:
        state: The current assistant state containing fields

    Returns:
        List of DynamicField objects that are ready for generation
    """
    ready_for_generation_fields = []
    status_order = ["untouched", "generated", "edited", "validated"]

    def get_status_level(status: FieldStatus) -> int:
        return status_order.index(status)

    for field in state["fields"]:
        # Check if field is untouched
        if field.status != "untouched":
            continue

        # Check if field has dependencies
        if not field.depends_on:
            ready_for_generation_fields.append(field)
            continue

        # Check if all dependencies are touched
        all_dependencies_satisfied = True
        for dependency in field.depends_on:
            dependency_field = find_field_by_name(state, dependency.field_name)
            if dependency_field is None:
                all_dependencies_satisfied = False
                break

            required_level = get_status_level(dependency_type_to_status(dependency.type))
            actual_level = get_status_level(dependency_field.status)

            if actual_level < required_level:
                all_dependencies_satisfied = False
                break

        if all_dependencies_satisfied:
            ready_for_generation_fields.append(field)

    return ready_for_generation_fields


def get_display_name(field: DynamicField | None) -> str:
    return getattr(field, "display_name", None) or getattr(field, "name", None) or ""


def get_status(field: DynamicField | None) -> FieldStatus:
    return getattr(field, "status", None) or FieldStatus.UNKNOWN


def get_description(field: DynamicField | None) -> str:
    return getattr(field, "description", None) or ""


def get_field_value(field: DynamicField | None) -> str:
    if field is None or field.value is None:
        return ""
    return str(field.value)


def get_field_desc_string(field: DynamicField | None, with_value: bool = False, raw_json: bool = False) -> str:
    """
    Return a string in the format display_name(status): description for a field.
    Optionally include the field's value if with_value is True.
    If raw_json is True, return a JSON string with {name, display_name, description, status, value}.

    Args:
        field: The DynamicField object
        with_value: Whether to include the field's value in the string
        raw_json: Whether to return a JSON string with field details
    Returns:
        Formatted string: display_name(status): description [| Value: value] or JSON string
    """
    display_name = get_display_name(field)
    status = get_status(field)
    description = get_description(field)
    value = getattr(field, "value", None)
    name = getattr(field, "name", None)
    if raw_json:
        return json.dumps(
            {"name": name, "display_name": display_name, "description": description, "status": status, "value": value}
        )
    if display_name or description:
        desc = f"{display_name}({status}): {description}"
        if with_value:
            desc += f" | Value: '{value}'" if value is not None and value != "" else " | Value: (empty)"
        return desc
    return ""


def get_all_fields_desc_string(fields: list[DynamicField], with_value: bool = False, raw_json: bool = False) -> str:
    """
    Return a string combining the descriptions of all fields using get_field_desc_string.
    Args:
        fields: List of DynamicField objects
        with_value: Whether to include the field's value in the string
        raw_json: Whether to return a JSON string with field details
    Returns:
        Combined string of all field descriptions (or JSON array if raw_json)
    """
    if raw_json:
        return "[" + ", ".join(get_field_desc_string(field, with_value, raw_json=True) for field in fields) + "]"
    return "\n".join(get_field_desc_string(field, with_value, raw_json=False) for field in fields)


def get_selected_field(
    fields: list[DynamicField], desc_value: bool = False, raw_json: bool = False
) -> tuple[DynamicField | None, str]:
    """
    Get the currently selected field from the fields list, and its display_name(status):description (and value if desc_value=True) if available.

    Args:
        fields: List of fields to search through
        desc_value: Whether to include the value in the description string

    Returns:
        Tuple of (DynamicField object that is selected or None, display_name(status): description [| Value: value] string)
    """
    for field in fields:
        if get_is_selected(field):
            desc = get_field_desc_string(field, with_value=desc_value, raw_json=raw_json)
            return field, desc
    return None, "No field is currently selected."


def clear_field_selections(state: DynamicAssistantState) -> None:
    """
    Clear all field selections in the state.

    Args:
        state: The current assistant state containing fields
    """
    for field in state["fields"]:
        field.selected = False


def get_updated_fields(state: DynamicAssistantState) -> list[DynamicField]:
    """
    Get all fields that have been updated.

    Args:
        state: The current assistant state containing fields

    Returns:
        List of DynamicField objects that have been updated
    """
    return [field for field in state["fields"] if get_is_updated(field)]


def get_fields_by_status(state: DynamicAssistantState, status: FieldStatus) -> list[DynamicField]:
    """
    Get all fields with a specific status.

    Args:
        state: The current assistant state containing fields
        status: The status to filter by

    Returns:
        List of DynamicField objects with the specified status
    """
    return [field for field in state["fields"] if get_status(field) == status]


def validate_field_dependencies(state: DynamicAssistantState, field: DynamicField) -> bool:
    """
    Check if a field's dependencies are satisfied.

    Args:
        state: The current assistant state containing fields
        field: The field to validate dependencies for

    Returns:
        True if all dependencies are satisfied, False otherwise
    """
    if not field.depends_on:
        return True

    status_order = ["untouched", "generated", "edited", "validated"]

    def get_status_level(status: FieldStatus) -> int:
        return status_order.index(status)

    for dependency in field.depends_on:
        dependency_field = find_field_by_name(state, dependency.field_name)
        if dependency_field is None:
            return False

        required_level = get_status_level(dependency_type_to_status(dependency.type))
        actual_level = get_status_level(dependency_field.status)

        if actual_level < required_level:
            return False

    return True


def batch_update_field_status(state: DynamicAssistantState, field_names: List[str], new_status: FieldStatus) -> None:
    """
    Update the status of multiple fields at once.

    Args:
        state: The current assistant state containing fields
        field_names: List of field names to update
        new_status: The new status to set
    """
    for field_name in field_names:
        field = find_field_by_name(state, field_name)
        if field:
            field.status = new_status
            logger.debug(f"Updated field '{field_name}' status to '{new_status}'")
        else:
            logger.warning(f"Field '{field_name}' not found for status update")


def reset_field_states(state: DynamicAssistantState, reset_values: bool = False) -> None:
    """
    Reset all fields to their initial state.

    Args:
        state: The current assistant state containing fields
        reset_values: Whether to also reset field values to None
    """
    for field in state["fields"]:
        field.status = FieldStatus.UNTOUCHED
        field.updated = False
        field.selected = False
        if reset_values:
            field.value = None

    logger.info(f"Reset {len(state['fields'])} fields to initial state")


def get_field_statistics(state: DynamicAssistantState) -> Dict[str, int]:
    """
    Get statistics about field statuses in the current state.

    Args:
        state: The current assistant state containing fields

    Returns:
        Dictionary with status counts
    """
    stats = {
        "total": len(state["fields"]),
        "untouched": 0,
        "generated": 0,
        "edited": 0,
        "validated": 0,
        "updated": 0,
        "selected": 0,
    }

    for field in state["fields"]:
        stats[get_status(field)] += 1
        if get_is_updated(field):
            stats["updated"] += 1
        if get_is_selected(field):
            stats["selected"] += 1

    return stats


def find_fields_by_dependency(state: DynamicAssistantState, dependency_field_name: str) -> List[DynamicField]:
    """
    Find all fields that depend on a specific field.

    Args:
        state: The current assistant state containing fields
        dependency_field_name: Name of the field that others depend on

    Returns:
        List of fields that depend on the specified field
    """
    dependent_fields = []

    for field in state["fields"]:
        for dependency in field.depends_on:
            if dependency.field_name == dependency_field_name:
                dependent_fields.append(field)
                break

    return dependent_fields


def validate_field_values(state: DynamicAssistantState) -> Dict[str, List[str]]:
    """
    Validate all field values against their types and constraints.

    Args:
        state: The current assistant state containing fields

    Returns:
        Dictionary mapping field names to validation error messages
    """
    validation_errors = {}

    for field in state["fields"]:
        errors = []

        if field.value is not None:
            # Type validation
            if field.type == "number":
                try:
                    float(field.value)
                except (ValueError, TypeError):
                    errors.append(f"Value '{field.value}' is not a valid number")
            elif field.type == "string":
                if not isinstance(field.value, str):
                    errors.append("Value must be a string")

        # Add dependency validation
        if not validate_field_dependencies(state, field):
            errors.append("Field dependencies are not satisfied")

        if errors:
            validation_errors[field.name] = errors

    return validation_errors


def create_field_update_summary(state: DynamicAssistantState, field_name: str, old_value: Any, new_value: Any) -> str:
    """
    Create a human-readable summary of a field update.

    Args:
        state: The current assistant state containing fields
        field_name: Name of the field that was updated
        old_value: Previous value
        new_value: New value

    Returns:
        Human-readable update summary
    """
    field = find_field_by_name(state, field_name)
    display_name = get_display_name(field) if field else field_name

    if old_value is None:
        return f"Set {display_name} to '{new_value}'"
    elif new_value is None:
        return f"Cleared {display_name}"
    else:
        return f"Updated {display_name} from '{old_value}' to '{new_value}'"


def get_field_name_description_pairs(state: DynamicAssistantState) -> str:
    """
    Get field information including name, description, and current value.

    Args:
        state: The current assistant state containing fields
    Returns:
        Formatted string with field name, description, and value information
    """
    field_descriptions = []
    for field in state["fields"]:
        display_name = get_display_name(field)
        description = get_description(field) or "No description"

        # Format the current value
        value = getattr(field, "value", None)
        if value is not None and value != "":
            current_value = f"Current value: '{value}'"
        else:
            current_value = "Current value: (empty)"

        field_descriptions.append(f"- {display_name}: {description} | {current_value}")

    return "\n".join(field_descriptions)


def get_missing_dependencies(state: DynamicAssistantState, field: DynamicField) -> list[DynamicField]:
    """
    Get a list of missing dependencies for a field.

    Args:
        state: The current assistant state containing fields
        field: The field to check dependencies for

    Returns:
        List of missing dependency DynamicField objects (dependencies not met)
    """
    if not field.depends_on:
        return []

    # Define status level hierarchy
    status_levels = {
        "untouched": 0,
        "touched": 1,
        "generated": 2,
        "edited": 3,
        "validated": 4,
    }

    missing_dependencies = []
    for dependency in field.depends_on:
        dependency_field = find_field_by_name(state, dependency.field_name)
        if dependency_field is None:
            # If the dependency field is missing, skip adding None, but could log or handle as needed
            continue
        required_level = status_levels.get(dependency.type, 0)
        actual_level = status_levels.get(dependency_field.status, 0)
        if actual_level < required_level:
            missing_dependencies.append(dependency_field)

    return missing_dependencies


def check_intent_fields_dependencies(state: DynamicAssistantState) -> tuple[bool, list[DynamicField]]:
    """
    Check if all intent fields have their dependencies satisfied.

    Args:
        state: The current assistant state containing fields

    Returns:
        Tuple of (all_satisfied: bool, missing_deps: List[DynamicField])
        - all_satisfied: True if all intent fields have dependencies satisfied
        - missing_deps: List of missing dependency DynamicField objects for intent fields
    """
    intent_fields = [field for field in state["fields"] if get_is_intent(field)]

    if not intent_fields:
        return True, []

    all_missing_deps = []

    for field in intent_fields:
        missing_deps = get_missing_dependencies(state, field)
        if missing_deps:
            all_missing_deps.extend(missing_deps)

    return len(all_missing_deps) == 0, all_missing_deps


def build_field_context(state: DynamicAssistantState) -> dict[str, str | float | int]:
    """
    Build a dictionary of field names to values for use in instruction template formatting.

    Only includes fields that have non-empty values.

    Args:
        state: The current assistant state containing fields

    Returns:
        Dictionary mapping field names to their values
    """
    field_context = {}
    for field in state["fields"]:
        if field.value:
            field_context[field.name] = field.value
    return field_context


def available_fields(state: DynamicAssistantState, status: FieldStatus) -> list[DynamicField]:
    """
    Get a list of available fields that match the given status and have all dependencies satisfied.

    Args:
        state: The current assistant state containing fields
        status: The status to filter by

    Returns:
        List of DynamicField objects that are available (status matches and dependencies satisfied)
    """
    available = []
    for field in state["fields"]:
        if field.status == status and validate_field_dependencies(state, field):
            available.append(field)
    return available


def suggest_edit_field(state: DynamicAssistantState) -> DynamicField | None:
    """
    Suggest a field to work on by priority: validated > edited > generated.
    Returns a random available field with the highest priority status, or None if none found.
    """
    for status in [cast(FieldStatus, "edited"), cast(FieldStatus, "generated"), cast(FieldStatus, "untouched")]:
        candidates = available_fields(state, status)
        if candidates and len(candidates) > 0:
            return candidates[0]
    return None


def get_formatted_instruction(field, state):
    """
    Given a field and the current state, return the formatted instruction string.
    This uses the field's instruction_prompt_template and fills it with values from other fields in the state.
    If a variable is missing, returns the unformatted template and logs a warning.
    """
    field_alias = state.get("field_alias", "field")
    instruction_template = (
        getattr(field, "instruction_prompt_template", None)
        or f"Generate a realistic value appropriate for this {field_alias} type."
    )
    # Build context from other fields
    field_context = {
        other_field.name: other_field.value
        for other_field in state["fields"]
        if other_field.value and other_field.name != field.name
    }
    try:
        formatted_instructions = instruction_template.format(**field_context)
    except KeyError as e:
        logger.warning(
            f"Could not format instruction template for field '{getattr(field, 'display_name', field.name)}': missing variable {e}"
        )
        formatted_instructions = instruction_template
    return formatted_instructions


def get_is_updated(field: DynamicField) -> bool:
    return getattr(field, "updated", False)


def get_is_selected(field: DynamicField) -> bool:
    return getattr(field, "selected", False)


def get_is_intent(field: DynamicField) -> bool:
    return getattr(field, "intent", False)


def get_intent_result(field: DynamicField):
    return getattr(field, "intent_result", None)


def dependency_type_to_status(dep_type: FieldDependencyType) -> FieldStatus:
    mapping = {
        FieldDependencyType.GENERATED: FieldStatus.GENERATED,
        FieldDependencyType.EDITED: FieldStatus.EDITED,
        FieldDependencyType.VALIDATED: FieldStatus.VALIDATED,
    }
    return mapping.get(dep_type, FieldStatus.UNKNOWN)
