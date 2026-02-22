"""LLM client abstractions with OpenRouter/OpenAI-compatible chat support.

Supported environment variables for default client creation:
- API key: ``OPENAI_API_KEY`` or ``OPENROUTER_API_KEY``
- Model: ``OPENAI_MODEL`` or ``OPENROUTER_MODEL`` (default: ``openrouter/auto``)
- Base URL: ``OPENAI_BASE_URL`` or ``OPENROUTER_BASE_URL``
  - Accepts either the direct chat completions endpoint or a provider root URL.
- Optional OpenRouter attribution headers:
  - ``OPENROUTER_HTTP_REFERER`` (fallback: ``OR_SITE_URL``)
  - ``OPENROUTER_X_TITLE`` (fallback: ``OR_APP_NAME``)
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

    @staticmethod
    def _extract_text_content(content: object) -> str:
        """Normalize chat message content into plain text.

        OpenRouter/OpenAI responses usually return a string, but some providers
        can return a list of content parts. This method keeps the client
        compatible with both formats.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_chunks: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text")
                    if isinstance(text, str):
                        text_chunks.append(text)
            return "\n".join(text_chunks)
        return ""

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

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"LLM response missing message content: {body}") from exc

        text = self._extract_text_content(content)
        if not text:
            raise RuntimeError(f"LLM response returned empty content: {body}")
        return text


def _resolve_chat_completions_url(base_url: str) -> str:
    """Accept provider root URLs and normalize to a chat/completions endpoint."""
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/chat/completions"):
        return trimmed
    if trimmed.endswith("/v1"):
        return f"{trimmed}/chat/completions"
    return f"{trimmed}/v1/chat/completions"


def build_default_llm_client() -> LLMClient | None:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENAI_MODEL") or os.getenv("OPENROUTER_MODEL") or "openrouter/auto"

    base_url = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENROUTER_BASE_URL")
        or "https://openrouter.ai/api/v1/chat/completions"
    )

    if not api_key:
        return None

    return OpenAIChatClient(
        api_key=api_key,
        model=model,
        base_url=_resolve_chat_completions_url(base_url),
        http_referer=os.getenv("OPENROUTER_HTTP_REFERER") or os.getenv("OR_SITE_URL"),
        x_title=os.getenv("OPENROUTER_X_TITLE") or os.getenv("OR_APP_NAME"),
    )
