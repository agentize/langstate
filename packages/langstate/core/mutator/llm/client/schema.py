from typing import Annotated

from pydantic import BaseModel, Field


class FieldExtraction(BaseModel):
    """Schema for a single field extraction from LLM response.
    """

    path: Annotated[
        str, Field(..., description="Field path (e.g. 'name', 'address.city')")
    ]
    value: Annotated[str, Field(..., description="The extracted value")]
    confidence: Annotated[
        float,
        Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0"),
    ]
