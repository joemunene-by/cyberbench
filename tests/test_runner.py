from __future__ import annotations

import json

from cyberbench.backends import get_backend
from cyberbench.backends.echo import EchoBackend
from cyberbench.runner import run_suite, write_run
from cyberbench.tasks import Task


def test_run_suite_with_echo_backend(tmp_path):
    tasks = [
        Task.from_dict(
            {
                "id": "t1",
                "category": "cve_triage",
                "type": "multiple_choice",
                "prompt": "Which is it?\nA) foo\nB) bar\nC) baz\nD) qux",
                "choices": ["A: foo", "B: bar", "C: baz", "D: qux"],
                "answer": "A",
            }
        ),
        Task.from_dict(
            {
                "id": "t2",
                "category": "cve_triage",
                "type": "multiple_choice",
                "prompt": "Which is it?\nA) foo\nB) bar",
                "choices": ["A: foo", "B: bar"],
                "answer": "B",
            }
        ),
    ]
    backend = EchoBackend()
    results = run_suite(backend, tasks)
    assert len(results) == 2
    # echo picks A, so t1=correct, t2=wrong
    scores = {r.task_id: r.score for r in results}
    assert scores["t1"] == 1.0
    assert scores["t2"] == 0.0

    run_path = write_run(tmp_path / "run.json", backend, results)
    data = json.loads(run_path.read_text())
    assert data["model"].startswith("echo")
    assert data["task_count"] == 2
    assert abs(data["mean_score"] - 0.5) < 1e-9


def test_get_backend_echo():
    backend = get_backend("echo")
    assert backend.name == "echo"


def test_get_backend_unknown_raises():
    import pytest

    with pytest.raises(ValueError, match="unknown backend"):
        get_backend("nonexistent-provider:model")
