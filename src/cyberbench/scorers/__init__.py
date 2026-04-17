"""Scorers: map (Task, model_response) -> ScoreResult."""

from __future__ import annotations

from dataclasses import dataclass

from ..tasks import Task
from .mc_exact import score as mc_exact
from .rubric_keyword import score as rubric_keyword
from .sigma_structural import score as sigma_structural


@dataclass
class ScoreResult:
    score: float  # in [0.0, 1.0]
    passed: bool  # binary: score >= pass_threshold
    detail: dict


SCORERS = {
    "mc_exact": mc_exact,
    "rubric_keyword": rubric_keyword,
    "sigma_structural": sigma_structural,
}


def score_task(task: Task, response: str, *, pass_threshold: float = 0.5) -> ScoreResult:
    fn = SCORERS[task.scorer_name()]
    score, detail = fn(task, response)
    return ScoreResult(score=score, passed=score >= pass_threshold, detail=detail)


__all__ = ["ScoreResult", "SCORERS", "score_task"]
