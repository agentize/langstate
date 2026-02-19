import json
from uuid import uuid4

from core.mutator.base.base import BaseMutator
from core.mutator.base.schema import MutationResult
from core.mutator.llm.schema import MutationContext
from core.mutator.llm.client.base import BaseLLMClient
from core.mutator.llm.client.schema import FieldExtraction
from core.state import ValueConfidence
from core.state.state.schema import Inference, ValueConfidence

_EXTRACTION_PROMPT = """You are a structured data extraction assistant.

Here is the current state (JSON):
{state_json}

Prompt:
{prompt}

Analyze the prompt and extract field updates. Return a JSON array where each element has:
- "path": field path (e.g. "name", "address.city")
- "value": the extracted value
- "confidence": confidence score from 0.0 to 1.0
- "inference": brief reasoning for this extraction

Return ONLY a JSON array, no other text. Example:
[{{"path": "name", "value": "John", "confidence": 0.95, "inference": "Extracted from user's introduction"}}]
"""


class LLMMutator(BaseMutator[MutationContext]):
    """Mutator that uses an LLM to extract field values from user input."""

    def __init__(self, llm_client: BaseLLMClient) -> None:
        self._llm_client = llm_client
        self._mutator_id: str = str(uuid4())

    async def mutate(self, context: MutationContext) -> MutationResult:
        """Process user input and update state via LLM extraction.

        Args:
            context: MutationContext containing agent input and current state

        Returns:
            MutationResult with the updated state graph
        """
        state = context.state.copy()

        state_json = state.to_json()

        # Build prompt for the LLM
        prompt_str: str = str(context.input.prompt)
        prompt = _EXTRACTION_PROMPT.format(
            state_json=state_json,
            prompt=prompt_str,
        )

        raw_response = await self._llm_client.generate(prompt)

        # Parse the LLM response as a list
        raw_data = json.loads(raw_response)
        if not isinstance(raw_data, list):
            raise ValueError(
                f"Expected a JSON array from LLM, got {type(raw_data).__name__}"
            )

        # Validate and parse extractions using Pydantic schemas
        extractions: list[FieldExtraction] = []
        for entry in raw_data:  # type: ignore[misc]
            extractions.append(FieldExtraction.model_validate(entry))

        # Apply extractions to the state copy
        for extraction in extractions:
            vc = ValueConfidence(
                value=extraction.value, confidence=extraction.confidence
            )
            state.add_value(extraction.path, vc)

            # Add inference tracking with LLM-generated reasoning
            inference = Inference(
                content=extraction.inference,
                mutator_id=self._mutator_id,
                message_id=context.input.message_id,
            )
            state.add_inference(extraction.path, inference)

        return MutationResult(updated_state=state)
