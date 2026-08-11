from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class VariantConfig:
    name: str
    command: list[str]
    remove: list[Path] = field(default_factory=list)
    overlay: list[tuple[Path, Path]] = field(default_factory=list)


@dataclass
class BenchmarkConfig:
    name: str
    repository: Path
    config_dir: Path
    base_ref: str
    prompt: str
    trials: int
    timeout_seconds: float
    checks: list[list[str]]
    allowed_paths: list[str]
    variants: list[VariantConfig]


@dataclass(frozen=True)
class CheckResult:
    command: list[str]
    exit_code: int | None
    passed: bool
    duration_seconds: float
    stdout_bytes: int = 0
    stderr_bytes: int = 0


@dataclass(frozen=True)
class TrialResult:
    variant: str
    trial: int
    passed: bool
    runner_exit_code: int | None
    timed_out: bool
    duration_seconds: float
    changed_files: list[str]
    additions: int
    deletions: int
    unexpected_files: list[str]
    stdout_bytes: int
    stderr_bytes: int
    token_usage: TokenUsage | None
    checks: list[CheckResult]
    error: str | None


@dataclass(frozen=True)
class BenchmarkRun:
    name: str
    results: list[TrialResult]
    output_dir: Path
