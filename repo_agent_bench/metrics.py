from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from .models import TokenUsage


def _mappings(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _mappings(child)


def extract_token_usage(transcript: str) -> TokenUsage | None:
    """Return the last explicit token-usage object in a JSON/JSONL transcript."""
    found: TokenUsage | None = None
    for line in transcript.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        for item in _mappings(payload):
            input_tokens = item.get("input_tokens")
            output_tokens = item.get("output_tokens")
            cached_tokens = item.get("cached_input_tokens", 0)
            if (
                isinstance(input_tokens, int)
                and not isinstance(input_tokens, bool)
                and isinstance(output_tokens, int)
                and not isinstance(output_tokens, bool)
                and isinstance(cached_tokens, int)
                and not isinstance(cached_tokens, bool)
            ):
                found = TokenUsage(input_tokens, output_tokens, cached_tokens)
    return found
