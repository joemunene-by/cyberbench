"""Base backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Backend(ABC):
    name: str = "base"
    model: str = ""

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """Return the model's response as a single string."""

    def identifier(self) -> str:
        return f"{self.name}:{self.model}" if self.model else self.name
