"""Deterministic echo backend for tests and smoke runs."""

from __future__ import annotations

from .base import Backend


class EchoBackend(Backend):
    """Returns a canned answer derived from the prompt. Useful for end-to-end tests.

    If the prompt looks like a multiple-choice question, it picks the first choice letter.
    Otherwise it echoes a short summary of the prompt.
    """

    name = "echo"

    def __init__(self, model: str = "echo", canned: str | None = None):
        self.model = model
        self._canned = canned

    def generate(self, prompt: str, system: str | None = None) -> str:
        if self._canned is not None:
            return self._canned
        # crude heuristic: if prompt contains "A)" / "A." treat as MC and answer A
        if any(tag in prompt for tag in ("A)", "A.", "A:")):
            return "A"
        return prompt[:120]
