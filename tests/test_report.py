from __future__ import annotations

import json

from cyberbench.report import build_leaderboard


def test_leaderboard_empty(tmp_path):
    md = build_leaderboard(tmp_path)
    assert "CyberBench Leaderboard" in md
    assert "No runs yet" in md


def test_leaderboard_ranks_by_mean(tmp_path):
    def write(name, model, results):
        (tmp_path / f"{name}.json").write_text(
            json.dumps(
                {
                    "model": model,
                    "task_count": len(results),
                    "total_score": sum(r["score"] for r in results),
                    "mean_score": sum(r["score"] for r in results) / len(results),
                    "pass_rate": sum(1 for r in results if r["score"] >= 0.5) / len(results),
                    "results": results,
                }
            )
        )

    write(
        "a",
        "modelA",
        [
            {"task_id": "x", "category": "cve_triage", "type": "mc", "score": 1.0, "passed": True},
            {"task_id": "y", "category": "code_review", "type": "ff", "score": 1.0, "passed": True},
        ],
    )
    write(
        "b",
        "modelB",
        [
            {"task_id": "x", "category": "cve_triage", "type": "mc", "score": 0.5, "passed": True},
            {"task_id": "y", "category": "code_review", "type": "ff", "score": 0.0, "passed": False},
        ],
    )
    md = build_leaderboard(tmp_path)
    # modelA (mean 1.0) should appear before modelB (mean 0.25)
    assert md.index("modelA") < md.index("modelB")
    assert "cve_triage" in md
    assert "code_review" in md
