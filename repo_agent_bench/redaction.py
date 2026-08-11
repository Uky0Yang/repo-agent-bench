from __future__ import annotations

import re
from collections.abc import Mapping

SENSITIVE_NAME = re.compile(r"(?:TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL|COOKIE|AUTH)", re.IGNORECASE)


def redact_sensitive_values(text: str, environment: Mapping[str, str]) -> str:
    """Best-effort redaction for secret-like environment values in captured logs."""
    candidates = [
        (name, value)
        for name, value in environment.items()
        if SENSITIVE_NAME.search(name) and len(value) >= 8
    ]
    for name, value in sorted(candidates, key=lambda item: len(item[1]), reverse=True):
        text = text.replace(value, f"[REDACTED:{name}]")
    return text
