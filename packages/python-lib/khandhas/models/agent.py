from typing import Any, Dict, List, Optional, Union, Literal, Protocol
from pydantic import BaseModel
from .basic import Info


class Agent(BaseModel):
    id: str
    info: Info