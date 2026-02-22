"""LLM client abstractions and minimal OpenAI-compatible implementation."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Return a model completion as plain text."""


@dataclass
class OpenAIChatClient:
    api_key: str
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1/chat/completions"
    timeout_s: int = 30

    def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise JSON-producing assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        return body["choices"][0]["message"]["content"]


class NoopLLMClient:
    """Placeholder client for tests and explicit no-LLM mode."""

    def complete(self, prompt: str) -> str:
        raise RuntimeError("No LLM client configured")


def build_default_llm_client() -> LLMClient | None:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        return None
    return OpenAIChatClient(api_key=api_key, model=model)
