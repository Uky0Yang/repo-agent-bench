from __future__ import annotations

import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import yaml

from .models import BenchmarkConfig, VariantConfig


class ConfigError(ValueError):
    """Raised when a benchmark definition is unsafe or incomplete."""


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be a mapping")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label} must be a non-empty string")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ConfigError(f"{label} must be a list of non-empty strings")
    return list(value)


def _command(value: Any, label: str) -> list[str]:
    command = _string_list(value, label)
    if not command:
        raise ConfigError(f"{label} must not be empty")
    return command


def _identifier(value: Any, label: str) -> str:
    text = _string(value, label)
    if not IDENTIFIER.fullmatch(text):
        raise ConfigError(f"{label} must use lowercase letters, numbers, and hyphens")
    return text


def _commands(value: Any, label: str) -> list[list[str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError(f"{label} must be a list of command arrays")
    return [_command(item, f"{label}[{index}]") for index, item in enumerate(value)]


def _safe_relative(value: Any, label: str) -> Path:
    text = _string(value, label)
    posix = PurePosixPath(text)
    windows = PureWindowsPath(text)
    if posix.is_absolute() or windows.is_absolute() or ".." in posix.parts or ".." in windows.parts:
        raise ConfigError(f"{label} must stay inside the worktree")
    return Path(text)


def _positive_number(value: Any, label: str, default: float) -> float:
    if value is None:
        return float(default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigError(f"{label} must be greater than zero")
    return float(value)


def _load_variant(raw: Any, config_dir: Path, index: int) -> VariantConfig:
    data = _mapping(raw, f"variants[{index}]")
    name = _identifier(data.get("name"), f"variants[{index}].name")
    command = _command(data.get("command"), f"variants[{index}].command")
    remove = [
        _safe_relative(item, f"variants[{index}].remove")
        for item in _string_list(data.get("remove"), f"variants[{index}].remove")
    ]
    overlay: list[tuple[Path, Path]] = []
    raw_overlay = data.get("overlay", [])
    if not isinstance(raw_overlay, list):
        raise ConfigError(f"variants[{index}].overlay must be a list")
    for overlay_index, item in enumerate(raw_overlay):
        entry = _mapping(item, f"variants[{index}].overlay[{overlay_index}]")
        source_text = _string(entry.get("source"), "overlay source")
        source = Path(source_text)
        if not source.is_absolute():
            source = (config_dir / source).resolve()
        target = _safe_relative(entry.get("target"), "overlay target")
        overlay.append((source, target))
    return VariantConfig(name=name, command=command, remove=remove, overlay=overlay)


def load_config(path: str | Path) -> BenchmarkConfig:
    config_path = Path(path).resolve()
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"could not read config: {exc}") from exc
    data = _mapping(raw, "config")
    if data.get("version") != 1:
        raise ConfigError("version must be 1")
    config_dir = config_path.parent
    repository_text = _string(data.get("repository"), "repository")
    repository = Path(repository_text)
    if not repository.is_absolute():
        repository = config_dir / repository
    repository = repository.resolve()
    if not repository.is_dir() or not (repository / ".git").exists():
        raise ConfigError("repository must be the root of an existing git worktree")
    raw_variants = data.get("variants")
    if not isinstance(raw_variants, list) or not raw_variants:
        raise ConfigError("variants must contain at least one entry")
    variants = [_load_variant(item, config_dir, index) for index, item in enumerate(raw_variants)]
    names = [variant.name for variant in variants]
    if len(names) != len(set(names)):
        raise ConfigError("variant names must be unique")
    trials_value = _positive_number(data.get("trials"), "trials", 1)
    if not trials_value.is_integer():
        raise ConfigError("trials must be an integer")
    return BenchmarkConfig(
        name=_identifier(data.get("name"), "name"),
        repository=repository,
        config_dir=config_dir,
        base_ref=_string(data.get("base_ref", "HEAD"), "base_ref"),
        prompt=_string(data.get("prompt"), "prompt"),
        trials=int(trials_value),
        timeout_seconds=_positive_number(data.get("timeout_seconds"), "timeout_seconds", 900),
        checks=_commands(data.get("checks"), "checks"),
        allowed_paths=_string_list(data.get("allowed_paths"), "allowed_paths"),
        variants=variants,
    )
