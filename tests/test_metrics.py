from __future__ import annotations

from repo_agent_bench.metrics import extract_token_usage


def test_should_extract_last_jsonl_usage_event() -> None:
    """RAB-005: Provider JSONL can report token usage without an API call."""
    transcript = (
        '{"type":"turn","usage":{"input_tokens":10,"output_tokens":3}}\n'
        '{"type":"result","usage":{"input_tokens":24,"output_tokens":8,'
        '"cached_input_tokens":4}}'
    )

    usage = extract_token_usage(transcript)

    assert usage.total_tokens == 32


def test_should_return_none_for_plain_text_transcript() -> None:
    """RAB-005: Missing usage stays unknown instead of being invented."""
    assert extract_token_usage("all tests passed") is None
