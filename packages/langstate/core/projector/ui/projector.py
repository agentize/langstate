"""UI Projector interface for LangState.

The UI Projector is responsible for:
- Generating UI components based on current state
- Creating natural language prompts/responses
- Suggesting values based on context
- Determining which fields to focus on next
"""

from abc import abstractmethod
from typing import List

from ..base.projector import BaseProjector
from .schema import (
    UIComponent,
    UIComponentType,
    UIProjectionContext,
    UIProjectionResult,
)


class BaseProjectorUI(BaseProjector[UIProjectionContext, UIProjectionResult]):
    """Abstract base class for UI Projector implementations.

    The UI Projector generates UI components and LLM completions based on
    the current state graph. It bridges the gap between the internal state
    representation and what the user sees.

    Responsibilities:
    - Map field schemas to appropriate UI component types
    - Generate natural language prompts/responses
    - Suggest values based on context
    - Determine which fields to focus on next

    Example usage:
        class ChatProjectorUI(BaseProjectorUI):
            async def project(
                self,
                context: UIProjectionContext
            ) -> UIProjectionResult:
                # Generate components for unfilled fields
                components = []
                for field_id, field_data in context.state.items():
                    values = field_data.get("values", [])
                    if not self._has_resolved_value(values):
                        component = self.map_field_to_component(field_id)
                        components.append(component)

                # Generate prompt
                prompt = await self.generate_prompt(context)

                return UIProjectionResult(
                    prompt=prompt,
                    components=components,
                    is_complete=self._is_complete(context)
                )
    """

    @abstractmethod
    async def project(self, context: UIProjectionContext) -> UIProjectionResult:
        """Generate UI components and prompt based on current state.

        This method takes the current state and generates the appropriate
        UI representation and natural language prompt for the user.

        Args:
            context: UIProjectionContext containing current state

        Returns:
            UIProjectionResult with UI components and prompt
        """
        pass

    @abstractmethod
    async def generate_prompt(self, context: UIProjectionContext) -> str:
        """Generate a natural language prompt for the user.

        Args:
            context: UIProjectionContext containing current state

        Returns:
            Generated prompt string
        """
        pass

    @abstractmethod
    def map_field_to_component(self, field_key: str) -> UIComponent:
        """Map a field to an appropriate UI component.

        Args:
            field_key: The field key to map

        Returns:
            UIComponent appropriate for the field
        """
        pass

    def get_supported_components(self) -> List[UIComponentType]:
        """Get list of supported UI component types.

        Override this method to specify which component types
        this projector supports.

        Returns:
            List of supported UIComponentType values
        """
        return list(UIComponentType)
