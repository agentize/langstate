from typing import Any, Dict, List, Optional, Union, Literal, Protocol
from typing_extensions import TypedDict
from enum import Enum

from pydantic import BaseModel
from .basic import Language, ExtensionProtocol, DisplayName, Path, Info
from .agent import Agent

class PropertyStatusType(str, Enum):
    UNTOUCHED = "untouched"
    GENERATED = "generated"
    EDITED = "edited"
    VALIDATED = "validated"
    UNKNOWN = "unknown"


class EnumerationCondition(BaseModel):
    values: List[Any]

class ValueRangeCondition(BaseModel):
    min: float
    max: float

class ValueSimilarityCondition(BaseModel):
    reference: str
    threshold: float  # Similarity threshold (0-1.0)

class StatusTypeCondition(BaseModel):
    allowed_condtions: List[Union[PropertyStatusType, ExtensionProtocol]]
    disallowed_conditions: List[Union[PropertyStatusType, ExtensionProtocol]]

class PromptCondition(BaseModel):
    prompt: str  # The prompt to be used for this condition

class PropertyDependency(BaseModel):
    property_id: str  
    enumerateCondtion: Optional[EnumerationCondition] = None
    valueRangeCondition: Optional[ValueRangeCondition] = None
    valueSimilarityCondition: Optional[ValueSimilarityCondition] = None
    statusTypeCondition: Optional[StatusTypeCondition] = None
    promptCondition: Optional[PromptCondition] = None
    
    class Config:
        extra = "allow"

class PropertyType(str, Enum):
    STRING = "string"
    NUMBER = "number"

class PromptTemplate(BaseModel):
    # Template for generating the property value without considering an existing value
    generate: Optional[str] = None
    # Template for updating the property value considering an existing value
    update: Optional[str] = None


class Property(BaseModel):
    id: str
    info: Info
    prompt_template: Optional[PromptTemplate]
    type: Union[PropertyType, ExtensionProtocol] = PropertyType.STRING
    # List of property names this property depends on with relationship of "OR". if any of these dependencies are met, this property is considered valid
    depends_on: List[PropertyDependency] = []
    tags: List[str] = []
    paths: List[Path] = []

    class Config:
        extra = "allow"

class PropertyStatus(BaseModel):
    type: Union[PropertyStatusType, ExtensionProtocol] = PropertyStatusType.UNKNOWN
    value: Optional[str] = None

class PropertySnapshot(BaseModel):
    id: str
    info: Info
    property: Property
    status: PropertyStatus
    # Indicates if this property is perceived as having updated during recent execution
    updated_by: List[Agent] = []
    # Indicates if the property is currently selected by AI for further processing
    requested_by: List[Agent] = []

