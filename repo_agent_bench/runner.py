from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .metrics import extract_token_usage
from .models import (
    BenchmarkConfig,
    BenchmarkRun,
    CheckResult,
    TrialResult,
    VariantConfig,
)
from .redaction import redact_sensitive_values
from .report import write_reports


class RunnerError(RuntimeError):
    """Raised when the benchmark harness itself cannot run."""


def _git(repository: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", "-C", str(repository), *args],
            check=check,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "git command failed").strip()
        raise RunnerError(detail) from exc


def _render_command(command: list[str], prompt: str, workspace: Path) -> list[str]:
    return [
        item.replace("{prompt}", prompt).replace("{workspace}", str(workspace)) for item in command
    ]


def _workspace_target(workspace: Path, relative: Path) -> Path:
    root = workspace.resolve()
    target = workspace / relative
    try:
        target.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise RunnerError(f"variant target escapes the worktree: {relative}") from exc
    return target


def _apply_variant(workspace: Path, variant: VariantConfig) -> None:
    for relative in variant.remove:
        target = _workspace_target(workspace, relative)
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        elif target.exists() or target.is_symlink():
            target.unlink()
    for source, relative_target in variant.overlay:
        if not source.exists():
            raise RunnerError(f"overlay source does not exist: {source}")
        target = _workspace_target(workspace, relative_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
    _git(workspace, "add", "-A")
    _git(
        workspace,
        "-c",
        "user.name=repo-agent-bench",
        "-c",
        "user.email=repo-agent-bench@example.invalid",
        "commit",
        "--allow-empty",
        "-m",
        f"repo-agent-bench setup: {variant.name}",
    )


def _run_process(
    command: list[str], workspace: Path, timeout: float
) -> tuple[int | None, str, str, bool, float, str | None]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return (
            completed.returncode,
            completed.stdout,
            completed.stderr,
            False,
            time.monotonic() - started,
            None,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout.decode("utf-8", "replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")
        )
        stderr = (
            exc.stderr.decode("utf-8", "replace")
            if isinstance(exc.stderr, bytes)
            else (exc.stderr or "")
        )
        return None, stdout, stderr, True, time.monotonic() - started, "runner timed out"
    except OSError as exc:
        return None, "", "", False, time.monotonic() - started, str(exc)


def _changed_files(workspace: Path) -> list[str]:
    status = _git(workspace, "status", "--porcelain=v1", "-z").stdout
    paths: list[str] = []
    for entry in status.split("\0"):
        if not entry:
            continue
        path = entry[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.replace("\\", "/"))
    return sorted(set(paths))


def _churn(workspace: Path, changed_files: list[str]) -> tuple[int, int]:
    additions = 0
    deletions = 0
    tracked_paths: set[str] = set()
    for line in _git(workspace, "diff", "--numstat", "HEAD", "--").stdout.splitlines():
        added, deleted, path = line.split("\t", 2)
        tracked_paths.add(path.replace("\\", "/"))
        if added.isdigit():
            additions += int(added)
        if deleted.isdigit():
            deletions += int(deleted)
    for path in changed_files:
        if path in tracked_paths:
            continue
        candidate = workspace / path
        if candidate.is_file():
            try:
                additions += len(candidate.read_text(encoding="utf-8").splitlines())
            except (OSError, UnicodeDecodeError):
                additions += 1
    return additions, deletions


def _unexpected_files(changed_files: list[str], patterns: list[str]) -> list[str]:
    if not patterns:
        return []
    return [
        path
        for path in changed_files
        if not any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)
    ]


def _run_checks(
    checks: list[list[str]], prompt: str, workspace: Path, timeout: float
) -> tuple[list[CheckResult], list[tuple[str, str]]]:
    results: list[CheckResult] = []
    transcripts: list[tuple[str, str]] = []
    for check in checks:
        command = _render_command(check, prompt, workspace)
        exit_code, stdout, stderr, timed_out, duration, _ = _run_process(
            command, workspace, timeout
        )
        redacted_stdout = redact_sensitive_values(stdout, os.environ)
        redacted_stderr = redact_sensitive_values(stderr, os.environ)
        transcripts.append((redacted_stdout, redacted_stderr))
        results.append(
            CheckResult(
                command=command,
                exit_code=exit_code,
                passed=exit_code == 0 and not timed_out,
                duration_seconds=duration,
                stdout_bytes=len(redacted_stdout.encode("utf-8")),
                stderr_bytes=len(redacted_stderr.encode("utf-8")),
            )
        )
    return results, transcripts


def _run_trial(
    config: BenchmarkConfig,
    variant: VariantConfig,
    trial: int,
    output_dir: Path,
) -> TrialResult:
    temp_root = Path(tempfile.mkdtemp(prefix="repo-agent-bench-"))
    workspace = temp_root / "worktree"
    added = False
    try:
        _git(config.repository, "worktree", "add", "--detach", str(workspace), config.base_ref)
        added = True
        _apply_variant(workspace, variant)
        command = _render_command(variant.command, config.prompt, workspace)
        exit_code, stdout, stderr, timed_out, duration, error = _run_process(
            command, workspace, config.timeout_seconds
        )
        checks, check_transcripts = _run_checks(
            config.checks, config.prompt, workspace, config.timeout_seconds
        )
        changed_files = _changed_files(workspace)
        additions, deletions = _churn(workspace, changed_files)
        unexpected_files = _unexpected_files(changed_files, config.allowed_paths)
        passed = (
            exit_code == 0
            and not timed_out
            and all(check.passed for check in checks)
            and not unexpected_files
        )
        stem = f"trial-{variant.name}-{trial}"
        redacted_stdout = redact_sensitive_values(stdout, os.environ)
        redacted_stderr = redact_sensitive_values(stderr, os.environ)
        (output_dir / f"{stem}.stdout.txt").write_text(redacted_stdout, encoding="utf-8")
        (output_dir / f"{stem}.stderr.txt").write_text(redacted_stderr, encoding="utf-8")
        for check_index, (check_stdout, check_stderr) in enumerate(check_transcripts, start=1):
            (output_dir / f"{stem}.check-{check_index}.stdout.txt").write_text(
                check_stdout, encoding="utf-8"
            )
            (output_dir / f"{stem}.check-{check_index}.stderr.txt").write_text(
                check_stderr, encoding="utf-8"
            )
        return TrialResult(
            variant=variant.name,
            trial=trial,
            passed=passed,
            runner_exit_code=exit_code,
            timed_out=timed_out,
            duration_seconds=duration,
            changed_files=changed_files,
            additions=additions,
            deletions=deletions,
            unexpected_files=unexpected_files,
            stdout_bytes=len(redacted_stdout.encode("utf-8")),
            stderr_bytes=len(redacted_stderr.encode("utf-8")),
            token_usage=extract_token_usage(stdout),
            checks=checks,
            error=error,
        )
    finally:
        if added:
            _git(config.repository, "worktree", "remove", "--force", str(workspace), check=False)
        shutil.rmtree(temp_root, ignore_errors=True)


def run_benchmark(
    config: BenchmarkConfig,
    *,
    output_dir: str | Path,
    selected_variants: set[str] | None = None,
) -> BenchmarkRun:
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    known_names = {variant.name for variant in config.variants}
    if selected_variants is not None:
        unknown = sorted(selected_variants - known_names)
        if unknown:
            raise RunnerError(f"unknown selected variant(s): {', '.join(unknown)}")
    variants = [
        variant
        for variant in config.variants
        if selected_variants is None or variant.name in selected_variants
    ]
    if not variants:
        raise RunnerError("no selected variants exist in the benchmark")
    results: list[TrialResult] = []
    for variant in variants:
        for trial in range(1, config.trials + 1):
            results.append(_run_trial(config, variant, trial, output_path))
    write_reports(output_path, config.name, results)
    return BenchmarkRun(name=config.name, results=results, output_dir=output_path)
