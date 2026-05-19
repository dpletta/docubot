"""Optional LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class DocProvider(ABC):
    @abstractmethod
    def summarize(self, context: str, *, max_tokens: int = 512) -> str:
        """Generate prose summary from structured context."""


class NoOpProvider(DocProvider):
    def summarize(self, context: str, *, max_tokens: int = 512) -> str:
        return ""


def get_provider(enabled: bool) -> DocProvider:
    if not enabled:
        return NoOpProvider()
    import os

    from docubot.providers.openai_compat import OpenAICompatProvider

    api_key = os.environ.get("DOCUBOT_LLM_API_KEY", "")
    base_url = os.environ.get("DOCUBOT_LLM_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        return NoOpProvider()
    model = os.environ.get("DOCUBOT_LLM_MODEL", "gpt-4o-mini")
    return OpenAICompatProvider(api_key=api_key, base_url=base_url, model=model)
