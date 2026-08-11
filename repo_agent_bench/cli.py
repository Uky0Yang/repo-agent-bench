from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, load_config
from .runner import RunnerError, run_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-agent-bench",
        description="A/B test coding-agent workflows in isolated git worktrees.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Validate a benchmark YAML file.")
    validate.add_argument("config")
    run = commands.add_parser("run", help="Run variants and write comparison reports.")
    run.add_argument("config")
    run.add_argument("--variant", action="append", dest="variants")
    run.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "validate":
            print(
                f"Valid benchmark {config.name!r}: "
                f"{len(config.variants)} variant(s), {config.trials} trial(s) each."
            )
            return 0
        output = args.output or config.repository / ".repo-agent-bench" / "runs" / config.name
        run = run_benchmark(
            config,
            output_dir=output,
            selected_variants=set(args.variants) if args.variants else None,
        )
        passed = sum(result.passed for result in run.results)
        print(f"{passed}/{len(run.results)} trials passed. Reports: {run.output_dir}")
        return 0 if passed == len(run.results) else 1
    except (ConfigError, RunnerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
