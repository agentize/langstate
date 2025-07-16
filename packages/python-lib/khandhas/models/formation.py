from typing import Any, Dict, List, Optional, Union, Literal, Protocol
from pydantic import BaseModel
from .property import Property, PropertySnapshot
from .basic import Info

class Form(BaseModel):
    id: str
    info: Info
    properties: List[PropertySnapshot] = []

    # Additional metadata for the form
    metadata: Dict[str, Any] = {}

class Formation(BaseModel):
    id: str
    perceived: List[PropertySnapshot] = []

    description: Optional[str] = None
    # The properties this operation applies to
    properties: List[Property]
    # Additional metadata for the operation
    metadata: Dict[str, Any] = {}