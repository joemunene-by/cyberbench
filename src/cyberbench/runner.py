"""Run a suite of tasks against a backend and produce per-task results."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .backends import Backend
from .scorers import score_task
from .tasks import Task


SYSTEM_PROMPTS = {
    "multiple_choice": (
        "You are a cybersecurity expert. Answer the multiple-choice question below. "
        "Reply with only the letter of the correct answer (e.g., 'A')."
    ),
    "free_form": (
        "You are a senior security engineer reviewing code and systems. "
        "Give a concise, technically precise answer."
    ),
    "sigma_rule": (
        "You are a detection engineer. Write a valid SIGMA rule in YAML. "
        "Respond with a single YAML document enclosed in a ```yaml code block."
    ),
}


@dataclass
class TaskRun:
    task_id: str
    category: str
    type: str
    score: float
    passed: bool
    response: str
    detail: dict
    latency_ms: int


def run_suite(backend: Backend, tasks: list[Task]) -> list[TaskRun]:
    results: list[TaskRun] = []
    for task in tasks:
        system = SYSTEM_PROMPTS.get(task.type)
        t0 = time.perf_counter()
        try:
            response = backend.generate(task.prompt, system=system)
        except Exception as e:
            response = f"[backend error: {e}]"
        latency_ms = int((time.perf_counter() - t0) * 1000)
        scored = score_task(task, response)
        results.append(
            TaskRun(
                task_id=task.id,
                category=task.category,
                type=task.type,
                score=scored.score,
                passed=scored.passed,
                response=response,
                detail=scored.detail,
                latency_ms=latency_ms,
            )
        )
    return results


def write_run(path: str | Path, backend: Backend, results: list[TaskRun]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": backend.identifier(),
        "task_count": len(results),
        "total_score": sum(r.score for r in results),
        "mean_score": (sum(r.score for r in results) / len(results)) if results else 0.0,
        "pass_rate": (sum(1 for r in results if r.passed) / len(results)) if results else 0.0,
        "results": [asdict(r) for r in results],
    }
    out.write_text(json.dumps(payload, indent=2))
    return out
