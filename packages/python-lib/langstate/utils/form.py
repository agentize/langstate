"""
Form-related utility functions for the assistant service.
"""

from typing import List, Dict, Any, cast
import json
from ..models.formation import Form
from ..models.property import Property, PropertySnapshot, PropertyStatusType, PropertyDependency


def is_form_untouched(form: Form) -> bool:
    """
    Check if the form is new, all properties' status are `untouched`.

    Args:
        form: The current form containing properties

    Returns:
        True if the form is new, False otherwise
    """
    for property_snapshot in form.properties:
        if get_status(property_snapshot) != PropertyStatusType.UNTOUCHED:
            return False
    return True


def find_property_by_id(form: Form, property_id: str) -> PropertySnapshot | None:
    """
    Find a property by its id in the form.

    Args:
        form: The current form containing properties
        property_id: ID of the property to find
    Returns:
        PropertySnapshot object if found, None otherwise
    """
    for property_snapshot in form.properties:
        if property_snapshot.id == property_id:
            return property_snapshot
    return None


def get_property_dependencies(
    form: Form, property_id: str, statuses: list[PropertyStatusType]
) -> list[PropertySnapshot]:
    """
    Find all dependencies of a given property that match any of the specified statuses.

    Args:
        form: The current form containing properties
        property_id: ID of the property to find dependencies for
        statuses: List of PropertyStatusType values to match against

    Returns:
        List of PropertySnapshot objects that are dependencies and match the statuses
    """
    # Find the target property
    target_property = find_property_by_id(form, property_id)

    if target_property is None:
        return []

    # Find all properties that this property depends on and match the specified statuses
    dependencies = []
    for property_snapshot in form.properties:
        for dep in target_property.property.depends_on:
            if property_snapshot.id == dep.property_id and property_snapshot.status.type in statuses:
                dependencies.append(property_snapshot)

    return dependencies


def get_ready_for_generation_properties(form: Form) -> list[PropertySnapshot]:
    """
    Find all properties that are untouched but whose dependencies have been satisfied.

    A property is ready for generation if:
    1. Its status is "untouched"
    2. All of its dependencies have status "generated", "edited", or "validated"

    Args:
        form: The current form containing properties

    Returns:
        List of PropertySnapshot objects that are ready for generation
    """
    ready_for_generation_properties = []
    status_order = [PropertyStatusType.UNTOUCHED, PropertyStatusType.GENERATED, PropertyStatusType.EDITED, PropertyStatusType.VALIDATED]

    def get_status_level(status: PropertyStatusType) -> int:
        return status_order.index(status)

    for property_snapshot in form.properties:
        # Check if property is untouched
        if property_snapshot.status.type != PropertyStatusType.UNTOUCHED:
            continue

        # Check if property has dependencies
        if not property_snapshot.property.depends_on:
            ready_for_generation_properties.append(property_snapshot)
            continue

        # Check if all dependencies are satisfied
        all_dependencies_satisfied = True
        for dependency in property_snapshot.property.depends_on:
            dependency_property = find_property_by_id(form, dependency.property_id)
            if dependency_property is None:
                all_dependencies_satisfied = False
                break

            required_level = get_status_level(dependency_type_to_status(dependency))
            actual_level = get_status_level(dependency_property.status.type)

            if actual_level < required_level:
                all_dependencies_satisfied = False
                break

        if all_dependencies_satisfied:
            ready_for_generation_properties.append(property_snapshot)

    return ready_for_generation_properties


def get_display_name(property_snapshot: PropertySnapshot | None) -> str:
    if property_snapshot is None:
        return ""
    if property_snapshot.info.display_names:
        return property_snapshot.info.display_names[0].value
    return property_snapshot.info.name or property_snapshot.id


def get_status(property_snapshot: PropertySnapshot | None) -> PropertyStatusType:
    if property_snapshot is None:
        return PropertyStatusType.UNKNOWN
    return property_snapshot.status.type


def get_description(property_snapshot: PropertySnapshot | None) -> str:
    if property_snapshot is None:
        return ""
    return property_snapshot.info.description or ""


def get_property_value(property_snapshot: PropertySnapshot | None) -> str:
    if property_snapshot is None or property_snapshot.status.value is None:
        return ""
    return str(property_snapshot.status.value)


def get_property_desc_string(property_snapshot: PropertySnapshot | None, with_value: bool = False, raw_json: bool = False) -> str:
    """
    Return a string in the format display_name(status): description for a property.
    Optionally include the property's value if with_value is True.
    If raw_json is True, return a JSON string with {id, display_name, description, status, value}.

    Args:
        property_snapshot: The PropertySnapshot object
        with_value: Whether to include the property's value in the string
        raw_json: Whether to return a JSON string with property details
    Returns:
        Formatted string: display_name(status): description [| Value: value] or JSON string
    """
    if property_snapshot is None:
        return ""
        
    display_name = get_display_name(property_snapshot)
    status = get_status(property_snapshot)
    description = get_description(property_snapshot)
    value = property_snapshot.status.value
    property_id = property_snapshot.id
    
    if raw_json:
        return json.dumps(
            {"id": property_id, "display_name": display_name, "description": description, "status": status.value, "value": value}
        )
    
    if display_name or description:
        desc = f"{display_name}({status.value}): {description}"
        if with_value:
            desc += f" | Value: '{value}'" if value is not None and value != "" else " | Value: (empty)"
        return desc
    return ""


def get_all_properties_desc_string(property_snapshots: list[PropertySnapshot], with_value: bool = False, raw_json: bool = False) -> str:
    """
    Return a string combining the descriptions of all properties using get_property_desc_string.
    Args:
        property_snapshots: List of PropertySnapshot objects
        with_value: Whether to include the property's value in the string
        raw_json: Whether to return a JSON string with property details
    Returns:
        Combined string of all property descriptions (or JSON array if raw_json)
    """
    if raw_json:
        return "[" + ", ".join(get_property_desc_string(prop, with_value, raw_json=True) for prop in property_snapshots) + "]"
    return "\n".join(get_property_desc_string(prop, with_value, raw_json=False) for prop in property_snapshots)


def get_selected_property(
    property_snapshots: list[PropertySnapshot], desc_value: bool = False, raw_json: bool = False
) -> tuple[PropertySnapshot | None, str]:
    """
    Get the currently selected property from the properties list, and its display_name(status):description (and value if desc_value=True) if available.

    Args:
        property_snapshots: List of properties to search through
        desc_value: Whether to include the value in the description string

    Returns:
        Tuple of (PropertySnapshot object that is selected or None, display_name(status): description [| Value: value] string)
    """
    for property_snapshot in property_snapshots:
        if get_is_requested(property_snapshot):
            desc = get_property_desc_string(property_snapshot, with_value=desc_value, raw_json=raw_json)
            return property_snapshot, desc
    return None, "No property is currently selected."


def clear_property_selections(form: Form) -> None:
    """
    Clear all property selections in the form.

    Args:
        form: The current form containing properties
    """
    for property_snapshot in form.properties:
        property_snapshot.requested_by.clear()


def get_updated_properties(form: Form) -> list[PropertySnapshot]:
    """
    Get all properties that have been updated.

    Args:
        form: The current form containing properties

    Returns:
        List of PropertySnapshot objects that have been updated
    """
    return [prop for prop in form.properties if get_is_updated(prop)]


def get_properties_by_status(form: Form, status: PropertyStatusType) -> list[PropertySnapshot]:
    """
    Get all properties with a specific status.

    Args:
        form: The current form containing properties
        status: The status to filter by

    Returns:
        List of PropertySnapshot objects with the specified status
    """
    return [prop for prop in form.properties if get_status(prop) == status]


def validate_property_dependencies(form: Form, property_snapshot: PropertySnapshot) -> bool:
    """
    Check if a property's dependencies are satisfied.

    Args:
        form: The current form containing properties
        property_snapshot: The property to validate dependencies for

    Returns:
        True if all dependencies are satisfied, False otherwise
    """
    if not property_snapshot.property.depends_on:
        return True

    status_order = [PropertyStatusType.UNTOUCHED, PropertyStatusType.GENERATED, PropertyStatusType.EDITED, PropertyStatusType.VALIDATED]

    def get_status_level(status: PropertyStatusType) -> int:
        return status_order.index(status)

    for dependency in property_snapshot.property.depends_on:
        dependency_property = find_property_by_id(form, dependency.property_id)
        if dependency_property is None:
            return False

        required_level = get_status_level(dependency_type_to_status(dependency))
        actual_level = get_status_level(dependency_property.status.type)

        if actual_level < required_level:
            return False

    return True


def batch_update_property_status(form: Form, property_ids: List[str], new_status: PropertyStatusType) -> None:
    """
    Update the status of multiple properties at once.

    Args:
        form: The current form containing properties
        property_ids: List of property IDs to update
        new_status: The new status to set
    """
    for property_id in property_ids:
        property_snapshot = find_property_by_id(form, property_id)
        if property_snapshot:
            property_snapshot.status.type = new_status
            # Note: logging would need to be imported if needed
            # logger.debug(f"Updated property '{property_id}' status to '{new_status}'")
        else:
            # logger.warning(f"Property '{property_id}' not found for status update")
            pass


def reset_property_states(form: Form, reset_values: bool = False) -> None:
    """
    Reset all properties to their initial state.

    Args:
        form: The current form containing properties
        reset_values: Whether to also reset property values to None
    """
    for property_snapshot in form.properties:
        property_snapshot.status.type = PropertyStatusType.UNTOUCHED
        property_snapshot.updated_by.clear()
        property_snapshot.requested_by.clear()
        if reset_values:
            property_snapshot.status.value = None

    # logger.info(f"Reset {len(form.properties)} properties to initial state")


def get_property_statistics(form: Form) -> Dict[str, int]:
    """
    Get statistics about property statuses in the current form.

    Args:
        form: The current form containing properties

    Returns:
        Dictionary with status counts
    """
    stats = {
        "total": len(form.properties),
        "untouched": 0,
        "generated": 0,
        "edited": 0,
        "validated": 0,
        "updated": 0,
        "requested": 0,
    }

    for property_snapshot in form.properties:
        status_key = get_status(property_snapshot).value
        if status_key in stats:
            stats[status_key] += 1
        if get_is_updated(property_snapshot):
            stats["updated"] += 1
        if get_is_requested(property_snapshot):
            stats["requested"] += 1

    return stats


def find_properties_by_dependency(form: Form, dependency_property_id: str) -> List[PropertySnapshot]:
    """
    Find all properties that depend on a specific property.

    Args:
        form: The current form containing properties
        dependency_property_id: ID of the property that others depend on

    Returns:
        List of properties that depend on the specified property
    """
    dependent_properties = []

    for property_snapshot in form.properties:
        for dependency in property_snapshot.property.depends_on:
            if dependency.property_id == dependency_property_id:
                dependent_properties.append(property_snapshot)
                break

    return dependent_properties


def validate_property_values(form: Form) -> Dict[str, List[str]]:
    """
    Validate all property values against their types and constraints.

    Args:
        form: The current form containing properties

    Returns:
        Dictionary mapping property IDs to validation error messages
    """
    validation_errors = {}

    for property_snapshot in form.properties:
        errors = []

        if property_snapshot.status.value is not None:
            # Type validation
            from ..models.property import PropertyType
            if property_snapshot.property.type == PropertyType.NUMBER:
                try:
                    float(property_snapshot.status.value)
                except (ValueError, TypeError):
                    errors.append(f"Value '{property_snapshot.status.value}' is not a valid number")
            elif property_snapshot.property.type == PropertyType.STRING:
                if not isinstance(property_snapshot.status.value, str):
                    errors.append("Value must be a string")

        # Add dependency validation
        if not validate_property_dependencies(form, property_snapshot):
            errors.append("Property dependencies are not satisfied")

        if errors:
            validation_errors[property_snapshot.id] = errors

    return validation_errors


def create_property_update_summary(form: Form, property_id: str, old_value: Any, new_value: Any) -> str:
    """
    Create a human-readable summary of a property update.

    Args:
        form: The current form containing properties
        property_id: ID of the property that was updated
        old_value: Previous value
        new_value: New value

    Returns:
        Human-readable update summary
    """
    property_snapshot = find_property_by_id(form, property_id)
    display_name = get_display_name(property_snapshot) if property_snapshot else property_id

    if old_value is None:
        return f"Set {display_name} to '{new_value}'"
    elif new_value is None:
        return f"Cleared {display_name}"
    else:
        return f"Updated {display_name} from '{old_value}' to '{new_value}'"


def get_property_name_description_pairs(form: Form) -> str:
    """
    Get property information including ID, description, and current value.

    Args:
        form: The current form containing properties
    Returns:
        Formatted string with property ID, description, and value information
    """
    property_descriptions = []
    for property_snapshot in form.properties:
        display_name = get_display_name(property_snapshot)
        description = get_description(property_snapshot) or "No description"

        # Format the current value
        value = property_snapshot.status.value
        if value is not None and value != "":
            current_value = f"Current value: '{value}'"
        else:
            current_value = "Current value: (empty)"

        property_descriptions.append(f"- {display_name}: {description} | {current_value}")

    return "\n".join(property_descriptions)


def get_missing_dependencies(form: Form, property_snapshot: PropertySnapshot) -> list[PropertySnapshot]:
    """
    Get a list of missing dependencies for a property.

    Args:
        form: The current form containing properties
        property_snapshot: The property to check dependencies for

    Returns:
        List of missing dependency PropertySnapshot objects (dependencies not met)
    """
    if not property_snapshot.property.depends_on:
        return []

    # Define status level hierarchy
    status_levels = {
        PropertyStatusType.UNTOUCHED: 0,
        PropertyStatusType.GENERATED: 1,
        PropertyStatusType.EDITED: 2,
        PropertyStatusType.VALIDATED: 3,
    }

    missing_dependencies = []
    for dependency in property_snapshot.property.depends_on:
        dependency_property = find_property_by_id(form, dependency.property_id)
        if dependency_property is None:
            # If the dependency property is missing, skip adding None, but could log or handle as needed
            continue
        required_level = status_levels.get(dependency_type_to_status(dependency), 0)
        actual_level = status_levels.get(dependency_property.status.type, 0)
        if actual_level < required_level:
            missing_dependencies.append(dependency_property)

    return missing_dependencies


def check_intent_properties_dependencies(form: Form) -> tuple[bool, list[PropertySnapshot]]:
    """
    Check if all intent properties have their dependencies satisfied.

    Args:
        form: The current form containing properties

    Returns:
        Tuple of (all_satisfied: bool, missing_deps: List[PropertySnapshot])
        - all_satisfied: True if all intent properties have dependencies satisfied
        - missing_deps: List of missing dependency PropertySnapshot objects for intent properties
    """
    # Note: intent logic would need to be defined based on your specific requirements
    # For now, treating all requested properties as intent properties
    intent_properties = [prop for prop in form.properties if get_is_requested(prop)]

    if not intent_properties:
        return True, []

    all_missing_deps = []

    for property_snapshot in intent_properties:
        missing_deps = get_missing_dependencies(form, property_snapshot)
        if missing_deps:
            all_missing_deps.extend(missing_deps)

    return len(all_missing_deps) == 0, all_missing_deps


def build_property_context(form: Form) -> dict[str, str | float | int]:
    """
    Build a dictionary of property IDs to values for use in instruction template formatting.

    Only includes properties that have non-empty values.

    Args:
        form: The current form containing properties

    Returns:
        Dictionary mapping property IDs to their values
    """
    property_context = {}
    for property_snapshot in form.properties:
        if property_snapshot.status.value:
            property_context[property_snapshot.id] = property_snapshot.status.value
    return property_context


def available_properties(form: Form, status: PropertyStatusType) -> list[PropertySnapshot]:
    """
    Get a list of available properties that match the given status and have all dependencies satisfied.

    Args:
        form: The current form containing properties
        status: The status to filter by

    Returns:
        List of PropertySnapshot objects that are available (status matches and dependencies satisfied)
    """
    available = []
    for property_snapshot in form.properties:
        if property_snapshot.status.type == status and validate_property_dependencies(form, property_snapshot):
            available.append(property_snapshot)
    return available


def suggest_edit_property(form: Form) -> PropertySnapshot | None:
    """
    Suggest a property to work on by priority: edited > generated > untouched.
    Returns the first available property with the highest priority status, or None if none found.
    """
    for status in [PropertyStatusType.EDITED, PropertyStatusType.GENERATED, PropertyStatusType.UNTOUCHED]:
        candidates = available_properties(form, status)
        if candidates and len(candidates) > 0:
            return candidates[0]
    return None


def get_formatted_instruction(property_snapshot: PropertySnapshot, form: Form) -> str:
    """
    Given a property and the current form, return the formatted instruction string.
    This uses the property's prompt template and fills it with values from other properties in the form.
    If a variable is missing, returns the unformatted template and logs a warning.
    """
    property_alias = form.metadata.get("property_alias", "property")
    
    # Get instruction template from property
    instruction_template = "Generate a realistic value appropriate for this property type."
    if property_snapshot.property.prompt_template and property_snapshot.property.prompt_template.generate:
        instruction_template = property_snapshot.property.prompt_template.generate
    
    # Build context from other properties
    property_context = {
        other_prop.id: other_prop.status.value
        for other_prop in form.properties
        if other_prop.status.value and other_prop.id != property_snapshot.id
    }
    
    try:
        formatted_instructions = instruction_template.format(**property_context)
    except KeyError as e:
        # logger.warning(f"Could not format instruction template for property '{get_display_name(property_snapshot)}': missing variable {e}")
        formatted_instructions = instruction_template
    return formatted_instructions


def get_is_updated(property_snapshot: PropertySnapshot) -> bool:
    """Check if the property has been updated by any agent."""
    return len(property_snapshot.updated_by) > 0


def get_is_requested(property_snapshot: PropertySnapshot) -> bool:
    """Check if the property is currently requested by any agent."""
    return len(property_snapshot.requested_by) > 0


def dependency_type_to_status(dependency: PropertyDependency) -> PropertyStatusType:
    """
    Convert a property dependency to the required status type.
    This is a simplified mapping - you may need to adjust based on your dependency conditions.
    """
    # This is a placeholder implementation - adjust based on your dependency logic
    if dependency.statusTypeCondition:
        # Use the first allowed condition if available
        if dependency.statusTypeCondition.allowed_condtions:
            for condition in dependency.statusTypeCondition.allowed_condtions:
                if isinstance(condition, PropertyStatusType):
                    return condition
    
    # Default to generated if no specific status condition
    return PropertyStatusType.GENERATED
