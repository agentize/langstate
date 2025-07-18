from typing import Any, Dict, List, Optional, Union, Literal, Protocol
from typing_extensions import TypedDict
from enum import Enum

from pydantic import BaseModel

class DisplayName(BaseModel):
    language: str
    value: str

    class Config:
        arbitrary_types_allowed = True

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