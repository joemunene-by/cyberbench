"""Ollama backend (local or remote). Uses the HTTP API directly via httpx."""

from __future__ import annotations

import os

import httpx

from .base import Backend


class OllamaBackend(Backend):
    name = "ollama"

    def __init__(self, model: str = "llama3", host: str | None = None, timeout: float = 120.0):
        self.model = model
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = timeout

    def generate(self, prompt: str, system: str | None = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        resp = httpx.post(
            f"{self.host}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return (data.get("response") or "").strip()
