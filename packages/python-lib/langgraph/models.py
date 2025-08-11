from typing import List, TypedDict
from langchain_core.messages import AnyMessage

class KhandhasState(TypedDict):
    """
    Base class for all Khandhas models for langgraph.
    This class is intended to define the state of a general Khandhas model.
    """
    messages: List[AnyMessage]