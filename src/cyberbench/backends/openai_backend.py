"""OpenAI-compatible backend (also works with any OpenAI-compatible endpoint)."""

from __future__ import annotations

import os

from .base import Backend


class OpenAIBackend(Backend):
    name = "openai"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.0,
    ):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError("install with `pip install cyberbench[openai]`") from e
        self.model = model
        self.temperature = temperature
        self._client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
        )

    def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return (resp.choices[0].message.content or "").strip()
