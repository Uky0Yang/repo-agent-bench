from __future__ import annotations

from repo_agent_bench.models import CheckResult, TrialResult
from repo_agent_bench.report import aggregate_results, render_html, render_markdown


def _result(variant: str, trial: int, passed: bool, duration: float) -> TrialResult:
    return TrialResult(
        variant=variant,
        trial=trial,
        passed=passed,
        runner_exit_code=0,
        timed_out=False,
        duration_seconds=duration,
        changed_files=["src/app.py"],
        additions=3,
        deletions=1,
        unexpected_files=[],
        stdout_bytes=10,
        stderr_bytes=0,
        token_usage=None,
        checks=[CheckResult(command=["pytest"], exit_code=0, passed=True, duration_seconds=0.1)],
        error=None,
    )


def test_should_aggregate_pass_rate_per_variant() -> None:
    """RAB-006: Comparison aggregates repeated trials."""
    summaries = aggregate_results(
        [_result("vanilla", 1, False, 2.0), _result("vanilla", 2, True, 4.0)]
    )

    assert summaries[0].pass_rate == 0.5


def test_should_render_markdown_comparison_table() -> None:
    """RAB-006: Markdown is ready to paste into a PR."""
    markdown = render_markdown("demo", [_result("guided", 1, True, 1.0)])

    assert "| guided | 100% |" in markdown


def test_should_render_self_contained_html() -> None:
    """RAB-006: HTML report needs no external assets."""
    html = render_html("demo", [_result("guided", 1, True, 1.0)])

    assert "<html" in html and "https://" not in html


def test_should_render_without_a_favicon_request() -> None:
    """RAB-006: Opening a local report should not create a console 404."""
    html = render_html("demo", [_result("guided", 1, True, 1.0)])

    assert '<link rel="icon" href="data:,">' in html


def test_should_render_accessible_pass_rate_text() -> None:
    """RAB-006: Pass rates remain readable without interpreting the visual bar."""
    html = render_html("demo", [_result("guided", 1, True, 1.0)])

    assert '<span class="rate">100%</span>' in html
