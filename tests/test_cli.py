from __future__ import annotations

from pathlib import Path

from repo_agent_bench.cli import main


def _config_text(repository: Path) -> str:
    return f"""version: 1
name: cli-demo
repository: {repository.as_posix()}
prompt: Say hello.
variants:
  - name: fake
    command: [python, -c, \"print('ok')\"]
"""


def test_should_validate_config_from_cli(git_repo: Path, tmp_path: Path, capsys) -> None:
    """RAB-007: Validate exits successfully for a usable definition."""
    config_path = tmp_path / "bench.yml"
    config_path.write_text(_config_text(git_repo), encoding="utf-8")

    code = main(["validate", str(config_path)])

    assert code == 0


def test_should_return_two_for_invalid_config(tmp_path: Path, capsys) -> None:
    """RAB-007: Invalid input has a stable CLI exit code."""
    config_path = tmp_path / "broken.yml"
    config_path.write_text("version: 1\n", encoding="utf-8")

    code = main(["validate", str(config_path)])

    assert code == 2
