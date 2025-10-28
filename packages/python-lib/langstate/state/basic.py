"""Basic model definitions for the khandhas package.

This module contains fundamental data structures and protocols used throughout
the khandhas library, including language definitions, display names, paths,
and base information models.
"""

from typing import Any, Dict, List, Optional, Union, Literal
from enum import Enum

from pydantic import BaseModel, Field


class DisplayName(BaseModel):
    """Display name with language information."""
    locale: str
    value: str


class Path(BaseModel):
    """Path specification for navigation."""
    type: Literal["key", "index"]
    value: str


class Info(BaseModel):
    """Base class for metadata information.
    
    This class can be extended to include additional metadata fields as needed.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    display_names: List[DisplayName] = Field(default_factory=list)
    uri: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ModelInfo(Info):
    """Model-specific information extending the base Info class."""
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    provider: Optional[str] = None