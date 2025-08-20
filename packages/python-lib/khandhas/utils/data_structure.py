from __future__ import annotations

from typing import List, Optional, TypeVar, Generic, Union
from pydantic import BaseModel, Field

N = TypeVar("N")
V = TypeVar("V")

class Tree(BaseModel, Generic[N, V]):
    value: Optional[V] = None
    children: List[N] = Field(default_factory=list)
