from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cyberbench.tasks import Task, load_tasks


def _write_task(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data))


def test_task_from_dict_minimal():
    task = Task.from_dict(
        {
            "id": "t1",
            "category": "x",
            "type": "multiple_choice",
            "prompt": "?",
            "choices": ["A: one", "B: two"],
            "answer": "A",
        }
    )
    assert task.id == "t1"
    assert task.scorer_name() == "mc_exact"


def test_task_missing_fields_raises():
    with pytest.raises(ValueError, match="missing"):
        Task.from_dict({"id": "x"})


def test_task_unknown_type_raises():
    with pytest.raises(ValueError, match="unknown task type"):
        Task.from_dict(
            {"id": "x", "category": "c", "type": "nope", "prompt": "p"}
        )


def test_load_tasks_from_dir(tmp_path):
    _write_task(
        tmp_path / "mc" / "a.yaml",
        {
            "id": "a",
            "category": "mc",
            "type": "multiple_choice",
            "prompt": "?",
            "choices": ["A: one"],
            "answer": "A",
        },
    )
    _write_task(
        tmp_path / "ff" / "b.yaml",
        {
            "id": "b",
            "category": "ff",
            "type": "free_form",
            "prompt": "?",
            "rubric": [{"must_mention": "x", "weight": 1.0}],
        },
    )
    tasks = load_tasks(tmp_path)
    assert len(tasks) == 2
    assert {t.id for t in tasks} == {"a", "b"}


def test_load_tasks_category_filter(tmp_path):
    _write_task(
        tmp_path / "mc" / "a.yaml",
        {"id": "a", "category": "mc", "type": "multiple_choice",
         "prompt": "?", "choices": ["A: x"], "answer": "A"},
    )
    _write_task(
        tmp_path / "other" / "b.yaml",
        {"id": "b", "category": "other", "type": "multiple_choice",
         "prompt": "?", "choices": ["A: x"], "answer": "A"},
    )
    tasks = load_tasks(tmp_path, categories=["mc"])
    assert [t.id for t in tasks] == ["a"]


def test_load_tasks_duplicate_id_raises(tmp_path):
    for name in ("a.yaml", "b.yaml"):
        _write_task(
            tmp_path / "c" / name,
            {"id": "dup", "category": "c", "type": "multiple_choice",
             "prompt": "?", "choices": ["A: x"], "answer": "A"},
        )
    with pytest.raises(ValueError, match="duplicate"):
        load_tasks(tmp_path)


def test_seed_tasks_all_load():
    # ensure the shipped seed tasks parse cleanly
    tasks = load_tasks(Path(__file__).parent.parent / "tasks")
    assert len(tasks) >= 15
    categories = {t.category for t in tasks}
    assert categories == {"cve_triage", "code_review", "detection_rule"}
