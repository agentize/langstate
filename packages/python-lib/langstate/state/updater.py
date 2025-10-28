from typing import Optional
from pydantic import BaseModel, Field
from .basic import Info, ModelInfo



class Updater(BaseModel):
    """Updater information."""
    id: str
    info: Info
    function_name: Optional[str] = None
    prompt_template: Optional[str] = None
    model_info: Optional[ModelInfo] = None
    
