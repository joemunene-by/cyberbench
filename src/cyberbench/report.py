"""Markdown leaderboard generator. Reads per-run JSON files, builds a ranked table."""

from __future__ import annotations

import json
from pathlib import Path


def build_leaderboard(runs_dir: str | Path) -> str:
    runs_dir = Path(runs_dir)
    rows = []
    for path in sorted(runs_dir.glob("*.json")):
        with open(path) as f:
            data = json.load(f)
        by_category: dict[str, list[float]] = {}
        for r in data.get("results", []):
            by_category.setdefault(r["category"], []).append(r["score"])
        per_cat = {c: (sum(v) / len(v)) if v else 0.0 for c, v in by_category.items()}
        rows.append(
            {
                "model": data.get("model", path.stem),
                "tasks": data.get("task_count", 0),
                "mean": data.get("mean_score", 0.0),
                "pass_rate": data.get("pass_rate", 0.0),
                "per_cat": per_cat,
            }
        )

    rows.sort(key=lambda r: r["mean"], reverse=True)
    categories = sorted({c for r in rows for c in r["per_cat"]})

    lines = ["# CyberBench Leaderboard", ""]
    header = ["Rank", "Model", "Mean", "Pass rate", "Tasks", *categories]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for i, r in enumerate(rows, start=1):
        cells = [
            str(i),
            f"`{r['model']}`",
            f"{r['mean']:.3f}",
            f"{r['pass_rate']:.3f}",
            str(r["tasks"]),
        ]
        for c in categories:
            v = r["per_cat"].get(c)
            cells.append(f"{v:.3f}" if v is not None else "—")
        lines.append("| " + " | ".join(cells) + " |")

    if not rows:
        lines.append("")
        lines.append("_No runs yet. Run `cyberbench run --model <backend>` to add a row._")
    return "\n".join(lines) + "\n"
