"""OpenAI-compatible API provider."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from docubot.providers.base import DocProvider

REDACT_PATTERNS = (
    "api_key",
    "password",
    "secret",
    "token",
    "Bearer ",
)


def _redact(text: str) -> str:
    lower = text.lower()
    for p in REDACT_PATTERNS:
        if p.lower() in lower:
            return "[redacted context]"
    return text


class OpenAICompatProvider(DocProvider):
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def summarize(self, context: str, *, max_tokens: int = 512) -> str:
        safe = _redact(context[:8000])
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Summarize the coding session for documentation. "
                        "Be concise (2-4 sentences). No secrets or credentials."
                    ),
                },
                {"role": "user", "content": safe},
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return (data["choices"][0]["message"]["content"] or "").strip()
        except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError):
            return ""
