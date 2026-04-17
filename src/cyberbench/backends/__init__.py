"""Model backends. Each backend exposes a `generate(prompt, system=None) -> str` method."""

from __future__ import annotations

from .base import Backend
from .echo import EchoBackend
from .ollama import OllamaBackend


def get_backend(name: str, **kwargs) -> Backend:
    """Resolve a backend by `provider:model` string or shorthand."""
    if ":" in name:
        provider, model = name.split(":", 1)
    else:
        provider, model = name, ""
    provider = provider.lower()

    if provider == "echo":
        return EchoBackend(model=model or "echo")
    if provider == "ollama":
        return OllamaBackend(model=model or "llama3", **kwargs)
    if provider == "openai":
        from .openai_backend import OpenAIBackend  # lazy import
        return OpenAIBackend(model=model or "gpt-4o-mini", **kwargs)
    if provider == "anthropic":
        from .anthropic_backend import AnthropicBackend  # lazy import
        return AnthropicBackend(model=model or "claude-sonnet-4-6", **kwargs)
    raise ValueError(f"unknown backend provider: {provider}")


__all__ = ["Backend", "EchoBackend", "OllamaBackend", "get_backend"]
