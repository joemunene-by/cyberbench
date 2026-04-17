from __future__ import annotations

from cyberbench.scorers import score_task
from cyberbench.scorers.mc_exact import score as mc_score
from cyberbench.scorers.rubric_keyword import score as rubric_score
from cyberbench.scorers.sigma_structural import score as sigma_score
from cyberbench.tasks import Task


def _mc(answer: str = "C") -> Task:
    return Task.from_dict(
        {
            "id": "mc",
            "category": "x",
            "type": "multiple_choice",
            "prompt": "?",
            "choices": ["A: a", "B: b", "C: c", "D: d"],
            "answer": answer,
        }
    )


def test_mc_letter_only():
    task = _mc("C")
    s, d = mc_score(task, "C")
    assert s == 1.0
    assert d["extracted"] == "C"


def test_mc_the_answer_is():
    task = _mc("B")
    s, _ = mc_score(task, "The answer is B because the exploit targets SMBv1.")
    assert s == 1.0


def test_mc_paren_letter():
    task = _mc("D")
    s, _ = mc_score(task, "(D) is correct")
    assert s == 1.0


def test_mc_wrong():
    task = _mc("A")
    s, _ = mc_score(task, "B")
    assert s == 0.0


def test_rubric_full_hit():
    task = Task.from_dict(
        {
            "id": "r",
            "category": "x",
            "type": "free_form",
            "prompt": "?",
            "rubric": [
                {"must_mention": "sql injection", "weight": 0.5},
                {"any_of": ["parameterized", "prepared statement"], "weight": 0.5},
            ],
        }
    )
    s, d = rubric_score(task, "This is a SQL injection — use a parameterized query to fix it.")
    assert s == 1.0
    assert all(h["matched"] for h in d["rubric_hits"])


def test_rubric_partial():
    task = Task.from_dict(
        {
            "id": "r",
            "category": "x",
            "type": "free_form",
            "prompt": "?",
            "rubric": [
                {"must_mention": "xss", "weight": 0.5},
                {"must_mention": "escape", "weight": 0.5},
            ],
        }
    )
    s, _ = rubric_score(task, "There's an XSS here. No fix suggested.")
    assert s == 0.5


def test_sigma_valid():
    task = Task.from_dict(
        {
            "id": "s",
            "category": "x",
            "type": "sigma_rule",
            "prompt": "?",
            "requirements": {
                "must_have_fields": ["title", "detection", "condition", "logsource"],
                "detection_keys_should_include": ["Image"],
                "expected_logsource_product": "windows",
            },
        }
    )
    response = """```yaml
title: Detect foo
id: abcd-1234
status: experimental
description: detects foo
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image: '*\\\\foo.exe'
  condition: selection
```"""
    s, d = sigma_score(task, response)
    assert s == 1.0
    assert d["parse_ok"] is True
    assert d["missing_fields"] == []


def test_sigma_missing_fields():
    task = Task.from_dict(
        {
            "id": "s",
            "category": "x",
            "type": "sigma_rule",
            "prompt": "?",
            "requirements": {
                "must_have_fields": ["title", "detection", "condition", "logsource"],
            },
        }
    )
    response = "title: x\n"  # missing most fields
    s, d = sigma_score(task, response)
    assert s < 1.0
    assert set(d["missing_fields"]) == {"detection", "condition", "logsource"}


def test_sigma_bad_yaml():
    task = Task.from_dict(
        {"id": "s", "category": "x", "type": "sigma_rule", "prompt": "?"}
    )
    s, d = sigma_score(task, "::: not yaml :::\n  - [")
    assert s == 0.0
    assert "error" in d


def test_score_task_dispatch():
    task = _mc("A")
    result = score_task(task, "A")
    assert result.score == 1.0
    assert result.passed is True
