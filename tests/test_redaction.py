from __future__ import annotations

from repo_agent_bench.redaction import redact_sensitive_values


def test_should_redact_sensitive_environment_values() -> None:
    """RAB-005: Captured transcripts hide configured process secrets."""
    text = "token=example-secret-value-12345 path=C:/tools"
    environment = {
        "OPENAI_API_KEY": "example-secret-value-12345",
        "PATH": "C:/tools",
    }

    redacted = redact_sensitive_values(text, environment)

    assert redacted == "token=[REDACTED:OPENAI_API_KEY] path=C:/tools"


def test_should_ignore_short_values_to_avoid_noisy_replacement() -> None:
    """RAB-005: Short common strings are not treated as credentials."""
    assert redact_sensitive_values("mode=dev", {"APP_SECRET": "dev"}) == "mode=dev"
