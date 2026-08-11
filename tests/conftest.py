from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal real git repository for worktree integration tests."""
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Repo Agent Bench Tests"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "tests@example.invalid"],
        cwd=repository,
        check=True,
    )
    (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed.txt"], cwd=repository, check=True)
    subprocess.run(
        ["git", "commit", "-m", "seed"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return repository
