"""Task schema and loader."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Supported task types (type -> default scorer name)
TASK_TYPES = {
    "multiple_choice": "mc_exact",
    "free_form": "rubric_keyword",
    "sigma_rule": "sigma_structural",
}


@dataclass
class Task:
    id: str
    category: str
    type: str
    prompt: str
    # multiple_choice
    choices: list[str] = field(default_factory=list)
    answer: str | None = None
    # free_form (rubric_keyword)
    rubric: list[dict[str, Any]] = field(default_factory=list)
    # sigma_rule
    requirements: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        missing = [k for k in ("id", "category", "type", "prompt") if k not in data]
        if missing:
            raise ValueError(f"task missing required fields: {missing}")
        t = data["type"]
        if t not in TASK_TYPES:
            raise ValueError(f"unknown task type '{t}'. known: {list(TASK_TYPES)}")
        return cls(
            id=data["id"],
            category=data["category"],
            type=t,
            prompt=data["prompt"],
            choices=data.get("choices", []) or [],
            answer=data.get("answer"),
            rubric=data.get("rubric", []) or [],
            requirements=data.get("requirements", {}) or {},
            metadata=data.get("metadata", {}) or {},
        )

    def scorer_name(self) -> str:
        return TASK_TYPES[self.type]


def load_tasks(root: str | Path, categories: list[str] | None = None) -> list[Task]:
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"tasks directory not found: {root}")

    tasks: list[Task] = []
    seen_ids: set[str] = set()
    for path in sorted(root.rglob("*.yaml")):
        if categories and path.parent.name not in categories:
            continue
        with open(path) as f:
            data = yaml.safe_load(f)
        if not data:
            continue
        task = Task.from_dict(data)
        if task.id in seen_ids:
            raise ValueError(f"duplicate task id: {task.id}")
        seen_ids.add(task.id)
        tasks.append(task)
    return tasks
