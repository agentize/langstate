from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for LLM client implementations."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            The generated text response
        """
        pass
