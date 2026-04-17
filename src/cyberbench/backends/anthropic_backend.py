"""Anthropic backend via the official SDK."""

from __future__ import annotations

import os

from .base import Backend


class AnthropicBackend(Backend):
    name = "anthropic"

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_key: str | None = None,
        max_tokens: int = 2048,
    ):
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise RuntimeError("install with `pip install cyberbench[anthropic]`") from e
        self.model = model
        self.max_tokens = max_tokens
        self._client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def generate(self, prompt: str, system: str | None = None) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        resp = self._client.messages.create(**kwargs)
        parts = []
        for block in resp.content:
            if getattr(block, "type", "") == "text":
                parts.append(block.text)
        return "".join(parts).strip()
