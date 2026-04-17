"""Multiple-choice exact-match scorer. Extracts an A/B/C/D style letter from output."""

from __future__ import annotations

import re

from ..tasks import Task


_LETTER_PATTERNS = [
    re.compile(r"\banswer\s*(?:is|:)?\s*\(?\s*([A-Z])\)?\b", re.IGNORECASE),
    re.compile(r"\b(?:option|choice)\s+\(?\s*([A-Z])\)?\b", re.IGNORECASE),
    re.compile(r"^\s*\(?([A-Z])[\)\.\:\-\s]", re.MULTILINE),
    re.compile(r"\b([A-Z])\b"),
]


def _extract_letter(text: str, valid: set[str]) -> str | None:
    for pat in _LETTER_PATTERNS:
        for m in pat.finditer(text):
            letter = m.group(1).upper()
            if letter in valid:
                return letter
    return None


def score(task: Task, response: str) -> tuple[float, dict]:
    if not task.answer:
        return 0.0, {"error": "task has no answer set"}
    valid_letters = set()
    for choice in task.choices:
        # choices may be "A: Foo" or just "Foo"; extract leading letter if present
        m = re.match(r"\s*\(?([A-Z])\)?[\)\.\:\-]", choice)
        if m:
            valid_letters.add(m.group(1).upper())
    if not valid_letters and task.choices:
        # choices present but no parseable letters: default A..Z by count
        valid_letters = {chr(ord("A") + i) for i in range(len(task.choices))}
    if not valid_letters:
        # no choices field: extract letters listed inline in the prompt (e.g. "A) ..." lines)
        for m in re.finditer(r"^\s*\(?([A-Z])[\)\.\:\-]", task.prompt, re.MULTILINE):
            valid_letters.add(m.group(1).upper())
    if not valid_letters:
        # last-resort fallback
        valid_letters = {"A", "B", "C", "D"}

    extracted = _extract_letter(response, valid_letters)
    expected = task.answer.strip().upper()[:1]
    correct = extracted == expected
    return (1.0 if correct else 0.0), {
        "extracted": extracted,
        "expected": expected,
        "valid_letters": sorted(valid_letters),
    }
