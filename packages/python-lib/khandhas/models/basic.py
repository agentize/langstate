from typing import Any, Dict, List, Optional, Union, Literal, Protocol
from typing_extensions import TypedDict
from enum import Enum

from pydantic import BaseModel

# Define protocols for extensible enum-like objects
class ExtensionProtocol(Protocol):
    @property
    def value(self) -> str: ...


class Language(str, Enum):
    EN = "en"
    ZH = "zh"

class DisplayName(BaseModel):
    language: Union[Language, ExtensionProtocol]
    value: str

class Path(BaseModel):
    type: Literal["key", "index"]
    value: str


class Info(BaseModel):
    """
    Base class for metadata information.
    
    This class can be extended to include additional metadata fields as needed.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    display_names: List[DisplayName] = []
    uri: Optional[str] = None

    # Additional metadata can be added here
    metadata: Dict[str, Any] = {}