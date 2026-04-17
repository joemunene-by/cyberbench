"""Keyword-rubric scorer: weighted check for presence of required phrases.

Each rubric entry:
  - must_mention: str | list[str]   # string to match (case-insensitive), or any-of list
  - weight: float                   # [0.0, 1.0], contribution to final score
"""

from __future__ import annotations

import re

from ..tasks import Task


def _any_match(text: str, needle) -> bool:
    text_lower = text.lower()
    if isinstance(needle, str):
        needles = [needle]
    else:
        needles = list(needle)
    for n in needles:
        if not n:
            continue
        if re.search(r"\b" + re.escape(n.lower()) + r"\b", text_lower):
            return True
    return False


def score(task: Task, response: str) -> tuple[float, dict]:
    if not task.rubric:
        return 0.0, {"error": "task has no rubric defined"}

    total_weight = sum(float(item.get("weight", 0.0)) for item in task.rubric)
    if total_weight <= 0:
        return 0.0, {"error": "rubric weights sum to zero"}

    earned = 0.0
    hits: list[dict] = []
    for item in task.rubric:
        needle = item.get("must_mention") or item.get("any_of") or ""
        weight = float(item.get("weight", 0.0))
        matched = _any_match(response, needle)
        if matched:
            earned += weight
        hits.append({"needle": needle, "weight": weight, "matched": matched})

    normalized = earned / total_weight
    return normalized, {"rubric_hits": hits, "earned": earned, "total_weight": total_weight}
