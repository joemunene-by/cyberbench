"""CyberBench CLI: run benchmarks and produce reports."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .backends import get_backend
from .report import build_leaderboard
from .runner import run_suite, write_run
from .tasks import load_tasks


console = Console()


def _slugify(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", s).strip("_").lower()


def _cmd_run(args: argparse.Namespace) -> int:
    tasks = load_tasks(args.tasks_dir, categories=args.category or None)
    if not tasks:
        console.print("[red]no tasks found[/red]")
        return 1

    backend = get_backend(args.model)
    console.print(
        f"[bold]cyberbench[/bold] running {len(tasks)} tasks against [cyan]{backend.identifier()}[/cyan]"
    )

    results = run_suite(backend, tasks)

    table = Table(title="Results", show_lines=False)
    table.add_column("Task")
    table.add_column("Category")
    table.add_column("Score", justify="right")
    table.add_column("Pass", justify="center")
    table.add_column("Latency", justify="right")
    for r in results:
        table.add_row(
            r.task_id,
            r.category,
            f"{r.score:.2f}",
            "✓" if r.passed else "·",
            f"{r.latency_ms} ms",
        )
    console.print(table)

    mean = sum(r.score for r in results) / len(results) if results else 0.0
    console.print(f"[bold]mean score:[/bold] {mean:.3f}")

    out_dir = Path(args.output_dir)
    out_path = out_dir / f"{_slugify(backend.identifier())}.json"
    write_run(out_path, backend, results)
    console.print(f"[green]run written:[/green] {out_path}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    md = build_leaderboard(args.runs_dir)
    out_path = Path(args.out)
    out_path.write_text(md)
    console.print(f"[green]leaderboard written:[/green] {out_path}")
    if args.print:
        console.print(md)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cyberbench")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run tasks against a model backend")
    p_run.add_argument("--model", required=True, help="e.g. echo, ollama:llama3, openai:gpt-4o-mini")
    p_run.add_argument("--tasks-dir", default="tasks", help="root directory of task YAML files")
    p_run.add_argument(
        "--category",
        nargs="*",
        default=None,
        help="restrict to categories (subdirectory names)",
    )
    p_run.add_argument("--output-dir", default="leaderboard", help="where to write the run JSON")
    p_run.set_defaults(func=_cmd_run)

    p_report = sub.add_parser("report", help="build the markdown leaderboard")
    p_report.add_argument("--runs-dir", default="leaderboard")
    p_report.add_argument("--out", default="LEADERBOARD.md")
    p_report.add_argument("--print", action="store_true")
    p_report.set_defaults(func=_cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
