"""
LLM client abstractions and minimal OpenAI-compatible implementation.
Configured for OpenRouter via env vars.

Env:
- OPENAI_API_KEY: your OpenRouter key (sk-or-...)
- OPENAI_MODEL: model id, e.g. "openai/gpt-4o-mini" or "openrouter/auto"
- OPENAI_BASE_URL: defaults to OpenRouter chat completions endpoint
- OPENROUTER_HTTP_REFERER (optional): for attribution
- OPENROUTER_X_TITLE (optional): for attribution
"""

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
    model: str
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    timeout_s: int = 30
    http_referer: str | None = None
    x_title: str | None = None

    def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise JSON-producing assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # Optional OpenRouter attribution headers
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.x_title:
            headers["X-Title"] = self.x_title

        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8")
            except Exception:
                detail = ""
            raise RuntimeError(f"LLM request failed: HTTP {exc.code} {exc.reason} {detail}".strip()) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        return body["choices"][0]["message"]["content"]


def build_default_llm_client() -> LLMClient | None:
    api_key = os.getenv("OPENAI_API_KEY")  # OpenRouter key works here
    model = os.getenv("OPENAI_MODEL", "openrouter/auto")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

    if not api_key:
        return None

    return OpenAIChatClient(
        api_key=api_key,
        model=model,
        base_url=base_url,
        http_referer=os.getenv("OPENROUTER_HTTP_REFERER"),
        x_title=os.getenv("OPENROUTER_X_TITLE"),
    )