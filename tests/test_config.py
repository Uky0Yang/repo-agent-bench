from __future__ import annotations

from pathlib import Path

import pytest

from repo_agent_bench.config import ConfigError, load_config


def _write_config(path: Path, repository: Path, extra: str = "") -> None:
    path.write_text(
        f"""version: 1
name: instruction-ab
repository: {repository.as_posix()}
prompt: Fix the failing behavior.
trials: 2
timeout_seconds: 30
checks:
  - [python, -c, \"raise SystemExit(0)\"]
allowed_paths:
  - src/**
variants:
  - name: vanilla
    command: [python, -c, \"print('{{prompt}}')\"]
  - name: guided
    command: [python, -c, \"print('{{workspace}}')\"]
{extra}""",
        encoding="utf-8",
    )


class TestLoadConfig:
    def test_should_load_valid_benchmark(self, tmp_path: Path, git_repo: Path) -> None:
        """RAB-001: A valid versioned config loads."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, git_repo)

        config = load_config(config_path)

        assert config.name == "instruction-ab"

    def test_should_resolve_repository_path(self, tmp_path: Path, git_repo: Path) -> None:
        """RAB-001: Repository paths become absolute."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, git_repo)

        config = load_config(config_path)

        assert config.repository == git_repo.resolve()

    def test_should_reject_unknown_schema_version(self, tmp_path: Path, git_repo: Path) -> None:
        """RAB-001: Unknown schema versions fail closed."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, git_repo)
        config_path.write_text(config_path.read_text().replace("version: 1", "version: 99"))

        with pytest.raises(ConfigError, match="version"):
            load_config(config_path)

    def test_should_reject_missing_variants(self, tmp_path: Path, git_repo: Path) -> None:
        """RAB-001: A comparison requires variants."""
        config_path = tmp_path / "bench.yml"
        config_path.write_text(
            f"version: 1\nname: empty\nrepository: {git_repo.as_posix()}\nprompt: test\n",
            encoding="utf-8",
        )

        with pytest.raises(ConfigError, match="variants"):
            load_config(config_path)

    def test_should_reject_duplicate_variant_names(self, tmp_path: Path, git_repo: Path) -> None:
        """RAB-001: Variant names are stable identifiers."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, git_repo)
        config_path.write_text(config_path.read_text().replace("name: guided", "name: vanilla"))

        with pytest.raises(ConfigError, match="unique"):
            load_config(config_path)

    def test_should_reject_parent_traversal_in_remove_path(
        self, tmp_path: Path, git_repo: Path
    ) -> None:
        """RAB-003: Variant removals stay inside the worktree."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, git_repo)
        config_path.write_text(
            config_path.read_text().replace(
                "command: [python, -c, \"print('{workspace}')\"]",
                "command: [python, -c, \"print('{workspace}')\"]\n    remove: [../outside]",
            ),
            encoding="utf-8",
        )

        with pytest.raises(ConfigError, match="remove"):
            load_config(config_path)

    def test_should_reject_absolute_overlay_target(self, tmp_path: Path, git_repo: Path) -> None:
        """RAB-003: Overlay targets stay inside the worktree."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, git_repo)
        config_path.write_text(
            config_path.read_text().replace(
                "command: [python, -c, \"print('{workspace}')\"]",
                "command: [python, -c, \"print('{workspace}')\"]\n    overlay:\n      - source: candidate.md\n        target: C:/outside.md",
            ),
            encoding="utf-8",
        )

        with pytest.raises(ConfigError, match="target"):
            load_config(config_path)

    def test_should_reject_unsafe_benchmark_name(self, tmp_path: Path, git_repo: Path) -> None:
        """RAB-001: Benchmark names cannot escape artifact directories."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, git_repo)
        config_path.write_text(
            config_path.read_text().replace("name: instruction-ab", "name: ../escape")
        )

        with pytest.raises(ConfigError, match="name"):
            load_config(config_path)

    def test_should_reject_unsafe_variant_name(self, tmp_path: Path, git_repo: Path) -> None:
        """RAB-001: Variant names are safe artifact identifiers."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, git_repo)
        config_path.write_text(config_path.read_text().replace("name: vanilla", "name: ../escape"))

        with pytest.raises(ConfigError, match="name"):
            load_config(config_path)

    def test_should_reject_empty_agent_command(self, tmp_path: Path, git_repo: Path) -> None:
        """RAB-001: Every variant must have something to execute."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, git_repo)
        config_path.write_text(
            config_path.read_text().replace(
                "command: [python, -c, \"print('{prompt}')\"]", "command: []"
            )
        )

        with pytest.raises(ConfigError, match="command"):
            load_config(config_path)

    def test_should_reject_missing_repository(self, tmp_path: Path) -> None:
        """RAB-001: Validation catches a repository typo before a paid run."""
        config_path = tmp_path / "bench.yml"
        _write_config(config_path, tmp_path / "missing")

        with pytest.raises(ConfigError, match="repository"):
            load_config(config_path)
