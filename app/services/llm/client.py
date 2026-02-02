"""LiteLLM client wrapper for LLM operations."""

from typing import Any

from litellm import acompletion

from app.core.exceptions import LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_llm_settings():
    """Get current LLM settings from settings service."""
    try:
        from app.services.settings import settings_service
        return settings_service.load().llm
    except Exception:
        from app.config import settings
        return settings


class LLMClient:
    """Client for LLM operations using LiteLLM.

    Provides a unified interface for calling various LLM providers
    (OpenAI, Anthropic, Ollama, etc.) through LiteLLM.
    Settings are read dynamically to support hot-reload.
    """

    def __init__(self) -> None:
        pass  # Settings read dynamically

    @property
    def api_url(self) -> str:
        """Get API URL from current settings."""
        return _get_llm_settings().api_url

    @property
    def api_key(self) -> str:
        """Get API key from current settings."""
        s = _get_llm_settings()
        if hasattr(s, 'api_key'):
            key = s.api_key
            return key.get_secret_value() if hasattr(key, 'get_secret_value') else key
        return ""

    @property
    def model(self) -> str:
        """Get model from current settings."""
        return _get_llm_settings().model

    @property
    def timeout(self) -> int:
        """Get timeout from current settings."""
        from app.config import settings
        return settings.llm_timeout_seconds

    @property
    def max_retries(self) -> int:
        """Get max retries from current settings."""
        from app.config import settings
        return settings.llm_max_retries

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        """Get a completion from the LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            str: LLM response text

        Raises:
            LLMError: If the LLM call fails
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            # Configure based on provider preset
            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": self.timeout,
            }

            # Add API base and key if configured
            if self.api_url:
                kwargs["api_base"] = self.api_url
            if self.api_key:
                kwargs["api_key"] = self.api_key

            response = await acompletion(**kwargs)

            content = response.choices[0].message.content
            logger.debug(
                "LLM completion successful",
                model=self.model,
                tokens_used=response.usage.total_tokens if response.usage else None,
            )
            return content or ""

        except Exception as e:
            logger.error("LLM completion failed", model=self.model, error=str(e))
            raise LLMError(f"LLM completion failed: {e}")

    async def health_check(self) -> bool:
        """Check if LLM service is available.

        Returns:
            bool: True if LLM is healthy
        """
        try:
            await self.complete("Say 'OK'", max_tokens=10)
            return True
        except Exception:
            return False


# Global client instance
llm_client = LLMClient()
