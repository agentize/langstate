import json
import os
import yaml
from typing import Any, Dict, List, Optional

from ..models.formation import Form
from ..models.basic import Info, DisplayName, Language, Path
from ..models.property import (
    PropertySnapshot, PropertyStatus, PropertyStatusType, Property, PropertyType,
    PromptTemplate, PropertyDependency, EnumerationCondition, ValueRangeCondition,
    ValueSimilarityCondition, StatusTypeCondition, PromptCondition
)
from ..models.agent import Agent


def load_form_from_id(id: str) -> Form:
    """
    Load a JSON or YAML configuration file and convert it to a complete Form.

    Args:
        id: Name of the JSON/YAML file (without extension) in the same directory

    Returns:
        Form: The complete loaded form configuration

    Raises:
        FileNotFoundError: If the specified file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        yaml.YAMLError: If the file contains invalid YAML
        KeyError: If required fields are missing from the configuration
    """
    # Get the directory of this file
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the configuration files
    json_file_path = os.path.join(current_dir, f"{id}.json")
    yaml_file_path = os.path.join(current_dir, f"{id}.yaml")

    # Check if file exists and load configuration
    if os.path.exists(json_file_path):
        # Load and parse the JSON file
        with open(json_file_path, "r", encoding="utf-8") as file:
            config_data = json.load(file)
    elif os.path.exists(yaml_file_path):
        # Load and parse the YAML file
        with open(yaml_file_path, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)
    else:
        raise FileNotFoundError(f"Configuration file not found: {json_file_path} or {yaml_file_path}")

    # Handle legacy format (with "fields" key) or new format (with "properties" key)
    if "fields" in config_data:
        # Legacy format conversion
        form = _load_form_from_legacy_format(id, config_data)
    else:
        # New format
        form = _load_form_from_new_format(id, config_data)

    return form


def _load_form_from_legacy_format(id: str, config_data: Dict[str, Any]) -> Form:
    """Load form from legacy format (with 'fields' key)."""
    # Extract and process info section
    info_data = config_data.get("info", {})
    if not info_data and "name" in config_data:
        # If no info section, create from top-level fields
        info_data = {
            "name": config_data.get("name"),
            "description": config_data.get("description"),
            "display_names": [{"language": "en", "value": config_data.get("name", id)}]
        }
    
    info = _build_info(info_data)

    # Convert legacy fields to properties
    fields_data = config_data.get("fields", [])
    properties = _convert_legacy_fields_to_properties(fields_data)

    # Extract metadata
    metadata = {
        "field_alias": config_data.get("field_alias", "field"),
        "tones": config_data.get("tones", []),
        "welcome_message": config_data.get("welcome_message"),
    }
    metadata.update(config_data.get("metadata", {}))

    return Form(
        id=id,
        info=info,
        properties=properties,
        metadata=metadata
    )


def _load_form_from_new_format(id: str, config_data: Dict[str, Any]) -> Form:
    """Load form from new format (with 'properties' key)."""
    # Extract and process info section
    info_data = config_data.get("info", {})
    info = _build_info(info_data)

    # Extract and process properties section
    properties_data = config_data.get("properties", [])
    properties = _build_property_snapshots(properties_data)

    # Extract metadata
    metadata = config_data.get("metadata", {})

    return Form(
        id=config_data.get("id", id),
        info=info,
        properties=properties,
        metadata=metadata
    )


def _convert_legacy_fields_to_properties(fields_data: List[Dict[str, Any]]) -> List[PropertySnapshot]:
    """Convert legacy 'fields' format to PropertySnapshot objects."""
    properties = []
    
    for field_data in fields_data:
        # Build property info from field data
        field_info = Info(
            name=field_data.get("name"),
            description=field_data.get("description"),
            display_names=[
                DisplayName(
                    language=Language.EN,
                    value=field_data.get("display_name", field_data.get("name", ""))
                )
            ]
        )
        
        # Build prompt template from instruction_prompt_template
        prompt_template = None
        if "instruction_prompt_template" in field_data:
            prompt_template = PromptTemplate(
                generate=field_data["instruction_prompt_template"]
            )
        
        # Build property type
        prop_type = PropertyType.STRING
        if "type" in field_data:
            prop_type = PropertyType(field_data["type"])
        
        # Create Property object
        property_obj = Property(
            id=field_data.get("name", ""),
            info=field_info,
            prompt_template=prompt_template,
            type=prop_type,
            depends_on=[],
            tags=field_data.get("tags", []),
            paths=[]
        )
        
        # Create PropertyStatus
        status = PropertyStatus(
            type=PropertyStatusType.UNTOUCHED,
            value=field_data.get("value")
        )
        
        # Create PropertySnapshot
        snapshot = PropertySnapshot(
            id=field_data.get("name", ""),
            info=field_info,
            property=property_obj,
            status=status,
            updated_by=[],
            requested_by=[]
        )
        
        properties.append(snapshot)
    
    return properties


def _build_info(info_data: Dict[str, Any]) -> Info:
    """Build Info object from configuration data."""
    display_names_data = info_data.get("display_names", [])
    display_names = []
    
    for dn_data in display_names_data:
        language_value = dn_data.get("language", "en")
        # Handle string language values by converting to enum
        language = Language(language_value) if isinstance(language_value, str) else language_value
        display_names.append(DisplayName(
            language=language,
            value=dn_data.get("value", "")
        ))

    return Info(
        name=info_data.get("name"),
        description=info_data.get("description"),
        display_names=display_names,
        uri=info_data.get("uri"),
        metadata=info_data.get("metadata", {})
    )


def _build_property_snapshots(properties_data: List[Dict[str, Any]]) -> List[PropertySnapshot]:
    """Build PropertySnapshot objects from configuration data."""
    snapshots = []
    
    for prop_data in properties_data:
        # Build property info
        prop_info_data = prop_data.get("info", {})
        prop_info = _build_info(prop_info_data)
        
        # Build prompt template
        prompt_template_data = prop_data.get("prompt_template", {})
        prompt_template = None
        if prompt_template_data:
            prompt_template = PromptTemplate(
                generate=prompt_template_data.get("generate"),
                update=prompt_template_data.get("update")
            )
        
        # Build property type
        prop_type = prop_data.get("type", "string")
        if isinstance(prop_type, str):
            prop_type = PropertyType(prop_type)
        
        # Build dependencies
        depends_on = _build_property_dependencies(prop_data.get("depends_on", []))
        
        # Build paths
        paths = _build_paths(prop_data.get("paths", []))
        
        # Build property
        property_obj = Property(
            id=prop_data.get("id", ""),
            info=prop_info,
            prompt_template=prompt_template,
            type=prop_type,
            depends_on=depends_on,
            tags=prop_data.get("tags", []),
            paths=paths
        )
        
        # Build property status
        status_data = prop_data.get("status", {})
        status_type = status_data.get("type", "unknown")
        if isinstance(status_type, str):
            status_type = PropertyStatusType(status_type)
        
        status = PropertyStatus(
            type=status_type,
            value=status_data.get("value")
        )
        
        # Build updated_by and requested_by agent lists
        updated_by = _build_agents(prop_data.get("updated_by", []))
        requested_by = _build_agents(prop_data.get("requested_by", []))
        
        # Create PropertySnapshot
        snapshot = PropertySnapshot(
            id=prop_data.get("id", ""),
            info=prop_info,
            property=property_obj,
            status=status,
            updated_by=updated_by,
            requested_by=requested_by
        )
        
        snapshots.append(snapshot)
    
    return snapshots


def _build_property_dependencies(deps_data: List[Dict[str, Any]]) -> List[PropertyDependency]:
    """Build PropertyDependency objects from configuration data."""
    dependencies = []
    
    for dep_data in deps_data:
        # Build enumeration condition
        enum_condition = None
        if "enumerateCondition" in dep_data:
            enum_data = dep_data["enumerateCondition"]
            enum_condition = EnumerationCondition(values=enum_data.get("values", []))
        
        # Build value range condition
        value_range_condition = None
        if "valueRangeCondition" in dep_data:
            range_data = dep_data["valueRangeCondition"]
            value_range_condition = ValueRangeCondition(
                min=range_data.get("min", 0),
                max=range_data.get("max", 100)
            )
        
        # Build value similarity condition
        value_similarity_condition = None
        if "valueSimilarityCondition" in dep_data:
            sim_data = dep_data["valueSimilarityCondition"]
            value_similarity_condition = ValueSimilarityCondition(
                reference=sim_data.get("reference", ""),
                threshold=sim_data.get("threshold", 0.5)
            )
        
        # Build status type condition
        status_type_condition = None
        if "statusTypeCondition" in dep_data:
            status_data = dep_data["statusTypeCondition"]
            allowed_conditions = [
                PropertyStatusType(cond) if isinstance(cond, str) else cond
                for cond in status_data.get("allowed_conditions", [])
            ]
            disallowed_conditions = [
                PropertyStatusType(cond) if isinstance(cond, str) else cond
                for cond in status_data.get("disallowed_conditions", [])
            ]
            status_type_condition = StatusTypeCondition(
                allowed_condtions=allowed_conditions,
                disallowed_conditions=disallowed_conditions
            )
        
        # Build prompt condition
        prompt_condition = None
        if "promptCondition" in dep_data:
            prompt_data = dep_data["promptCondition"]
            prompt_condition = PromptCondition(prompt=prompt_data.get("prompt", ""))
        
        # Create PropertyDependency
        dependency = PropertyDependency(
            property_id=dep_data.get("property_id", ""),
            enumerateCondtion=enum_condition,
            valueRangeCondition=value_range_condition,
            valueSimilarityCondition=value_similarity_condition,
            statusTypeCondition=status_type_condition,
            promptCondition=prompt_condition
        )
        
        dependencies.append(dependency)
    
    return dependencies


def _build_paths(paths_data: List[Dict[str, Any]]) -> List[Path]:
    """Build Path objects from configuration data."""
    paths = []
    
    for path_data in paths_data:
        path = Path(
            type=path_data.get("type", "key"),
            value=path_data.get("value", "")
        )
        paths.append(path)
    
    return paths


def _build_agents(agents_data: List[Dict[str, Any]]) -> List[Agent]:
    """Build Agent objects from configuration data."""
    agents = []
    
    for agent_data in agents_data:
        # Build agent info
        agent_info_data = agent_data.get("info", {})
        agent_info = _build_info(agent_info_data)
        
        # Create Agent object
        agent = Agent(
            id=agent_data.get("id", ""),
            info=agent_info,
            # Add other Agent fields as needed based on your schema
            metadata=agent_data.get("metadata", {})
        )
        
        agents.append(agent)
    
    return agents
