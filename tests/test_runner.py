from __future__ import annotations

import sys
from pathlib import Path

from repo_agent_bench.models import BenchmarkConfig, VariantConfig
from repo_agent_bench.runner import RunnerError, run_benchmark


def _config(
    repository: Path,
    command: list[str],
    *,
    checks: list[list[str]] | None = None,
    allowed_paths: list[str] | None = None,
    timeout_seconds: float = 10,
) -> BenchmarkConfig:
    return BenchmarkConfig(
        name="integration",
        repository=repository,
        config_dir=repository,
        base_ref="HEAD",
        prompt="Create result.txt",
        trials=1,
        timeout_seconds=timeout_seconds,
        checks=checks or [],
        allowed_paths=allowed_paths or [],
        variants=[VariantConfig(name="candidate", command=command)],
    )


def test_should_run_agent_in_detached_worktree(git_repo: Path, tmp_path: Path) -> None:
    """RAB-002: The runner receives a disposable worktree."""
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('result.txt').write_text('ok')",
    ]

    run = run_benchmark(_config(git_repo, command), output_dir=tmp_path / "artifacts")

    assert run.results[0].changed_files == ["result.txt"]


def test_should_not_mutate_source_repository(git_repo: Path, tmp_path: Path) -> None:
    """RAB-002: Agent changes never touch the source checkout."""
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('result.txt').write_text('ok')",
    ]

    run_benchmark(_config(git_repo, command), output_dir=tmp_path / "artifacts")

    assert not (git_repo / "result.txt").exists()


def test_should_fail_when_deterministic_check_fails(git_repo: Path, tmp_path: Path) -> None:
    """RAB-004: Claims do not override verifier failures."""
    command = [sys.executable, "-c", "print('done')"]
    checks = [[sys.executable, "-c", "raise SystemExit(7)"]]

    run = run_benchmark(
        _config(git_repo, command, checks=checks), output_dir=tmp_path / "artifacts"
    )

    assert run.results[0].passed is False


def test_should_fail_when_agent_times_out(git_repo: Path, tmp_path: Path) -> None:
    """RAB-004: Hung agents stop at the configured deadline."""
    command = [sys.executable, "-c", "import time; time.sleep(2)"]

    run = run_benchmark(
        _config(git_repo, command, timeout_seconds=0.05), output_dir=tmp_path / "artifacts"
    )

    assert run.results[0].timed_out is True


def test_should_fail_for_changes_outside_allowed_paths(git_repo: Path, tmp_path: Path) -> None:
    """RAB-004: Scope drift is a deterministic failure."""
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('outside.txt').write_text('drift')",
    ]

    run = run_benchmark(
        _config(git_repo, command, allowed_paths=["src/**"]),
        output_dir=tmp_path / "artifacts",
    )

    assert run.results[0].unexpected_files == ["outside.txt"]


def test_should_apply_overlay_before_agent_run(git_repo: Path, tmp_path: Path) -> None:
    """RAB-003: Candidate instructions can be injected as a variant baseline."""
    overlay_source = tmp_path / "candidate.md"
    overlay_source.write_text("candidate guidance\n", encoding="utf-8")
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('result.txt').write_text(Path('AGENTS.md').read_text())",
    ]
    config = _config(git_repo, command)
    config.variants[0] = VariantConfig(
        name="candidate",
        command=command,
        overlay=[(overlay_source, Path("AGENTS.md"))],
    )

    run = run_benchmark(config, output_dir=tmp_path / "artifacts")

    assert run.results[0].changed_files == ["result.txt"]


def test_should_remove_instruction_for_vanilla_variant(git_repo: Path, tmp_path: Path) -> None:
    """RAB-003: A variant can hide repository instructions before measurement."""
    (git_repo / "AGENTS.md").write_text("guidance\n", encoding="utf-8")
    import subprocess

    subprocess.run(["git", "add", "AGENTS.md"], cwd=git_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "add instructions"],
        cwd=git_repo,
        check=True,
        capture_output=True,
        text=True,
    )
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; raise SystemExit(Path('AGENTS.md').exists())",
    ]
    config = _config(git_repo, command)
    config.variants[0] = VariantConfig(name="vanilla", command=command, remove=[Path("AGENTS.md")])

    run = run_benchmark(config, output_dir=tmp_path / "artifacts")

    assert run.results[0].runner_exit_code == 0


def test_should_write_all_report_formats(git_repo: Path, tmp_path: Path) -> None:
    """RAB-006: One run writes machine and human review artifacts."""
    output_dir = tmp_path / "artifacts"

    run_benchmark(
        _config(git_repo, [sys.executable, "-c", "print('ok')"]),
        output_dir=output_dir,
    )

    assert sorted(path.name for path in output_dir.iterdir()) == [
        "summary.html",
        "summary.json",
        "summary.md",
        "trial-candidate-1.stderr.txt",
        "trial-candidate-1.stdout.txt",
    ]


def test_should_reject_unknown_selected_variant(git_repo: Path, tmp_path: Path) -> None:
    """RAB-007: A misspelled filter cannot silently change the experiment."""
    config = _config(git_repo, [sys.executable, "-c", "print('ok')"])

    try:
        run_benchmark(
            config,
            output_dir=tmp_path / "artifacts",
            selected_variants={"candidate", "typo"},
        )
    except RunnerError as exc:
        message = str(exc)
    else:
        message = ""

    assert "typo" in message


def test_should_report_new_path_after_git_rename(git_repo: Path, tmp_path: Path) -> None:
    """RAB-005: Rename evidence uses the destination path."""
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('seed.txt').rename('renamed.txt')",
    ]

    run = run_benchmark(_config(git_repo, command), output_dir=tmp_path / "artifacts")

    assert run.results[0].changed_files == ["renamed.txt", "seed.txt"]


def test_should_capture_verifier_transcripts(git_repo: Path, tmp_path: Path) -> None:
    """RAB-005: Failed checks retain reviewable evidence."""
    output_dir = tmp_path / "artifacts"
    checks = [[sys.executable, "-c", "print('verification-details'); raise SystemExit(1)"]]

    run_benchmark(
        _config(git_repo, [sys.executable, "-c", "print('done')"], checks=checks),
        output_dir=output_dir,
    )

    assert (
        output_dir / "trial-candidate-1.check-1.stdout.txt"
    ).read_text().strip() == "verification-details"


def test_should_redact_agent_transcript_secrets(
    git_repo: Path, tmp_path: Path, monkeypatch
) -> None:
    """RAB-005: Local artifacts do not copy obvious environment secrets verbatim."""
    output_dir = tmp_path / "artifacts"
    secret = "test-secret-value-12345"
    monkeypatch.setenv("RAB_TEST_TOKEN", secret)
    command = [
        sys.executable,
        "-c",
        "import os; print(os.environ['RAB_TEST_TOKEN'])",
    ]

    run_benchmark(_config(git_repo, command), output_dir=output_dir)

    assert secret not in (output_dir / "trial-candidate-1.stdout.txt").read_text()
