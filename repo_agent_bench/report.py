from __future__ import annotations

import html
import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import TrialResult


@dataclass(frozen=True)
class VariantSummary:
    variant: str
    trials: int
    passes: int
    pass_rate: float
    median_duration_seconds: float
    median_churn: float
    median_tokens: float | None


def aggregate_results(results: list[TrialResult]) -> list[VariantSummary]:
    grouped: dict[str, list[TrialResult]] = {}
    for result in results:
        grouped.setdefault(result.variant, []).append(result)
    summaries: list[VariantSummary] = []
    for variant, trials in grouped.items():
        tokens = [
            trial.token_usage.total_tokens for trial in trials if trial.token_usage is not None
        ]
        passes = sum(trial.passed for trial in trials)
        summaries.append(
            VariantSummary(
                variant=variant,
                trials=len(trials),
                passes=passes,
                pass_rate=passes / len(trials),
                median_duration_seconds=statistics.median(
                    trial.duration_seconds for trial in trials
                ),
                median_churn=statistics.median(
                    trial.additions + trial.deletions for trial in trials
                ),
                median_tokens=statistics.median(tokens) if tokens else None,
            )
        )
    return summaries


def render_markdown(name: str, results: list[TrialResult]) -> str:
    lines = [
        f"# Benchmark: {name}",
        "",
        "| Variant | Pass rate | Trials | Median time | Median churn | Median tokens |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in aggregate_results(results):
        tokens = "unknown" if summary.median_tokens is None else f"{summary.median_tokens:.0f}"
        lines.append(
            f"| {summary.variant} | {summary.pass_rate:.0%} | {summary.trials} | "
            f"{summary.median_duration_seconds:.2f}s | {summary.median_churn:.0f} | {tokens} |"
        )
    lines.extend(
        [
            "",
            "## Trial evidence",
            "",
            "| Variant | Trial | Result | Exit | Changed files | Unexpected files |",
            "| --- | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for result in results:
        exit_code = "timeout" if result.timed_out else str(result.runner_exit_code)
        lines.append(
            f"| {result.variant} | {result.trial} | {'PASS' if result.passed else 'FAIL'} | "
            f"{exit_code} | {len(result.changed_files)} | {len(result.unexpected_files)} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_html(name: str, results: list[TrialResult]) -> str:
    rows = []
    for summary in aggregate_results(results):
        width = int(summary.pass_rate * 100)
        tokens = "unknown" if summary.median_tokens is None else f"{summary.median_tokens:.0f}"
        rows.append(
            "<tr>"
            f"<td>{html.escape(summary.variant)}</td>"
            f'<td><div class=bar><span style="width:{width}%"></span></div>{width}%</td>'
            f"<td>{summary.trials}</td><td>{summary.median_duration_seconds:.2f}s</td>"
            f"<td>{summary.median_churn:.0f}</td><td>{tokens}</td>"
            "</tr>"
        )
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{title}</title><style>
body{{font:15px system-ui;max-width:960px;margin:48px auto;padding:0 20px;color:#172033;background:#f7f8fb}}
h1{{font-size:28px}}table{{width:100%;border-collapse:collapse;background:white;box-shadow:0 8px 30px #17203312}}
th,td{{padding:12px;text-align:left;border-bottom:1px solid #e7e9ef}}.bar{{display:inline-block;width:120px;height:10px;background:#e8ecf3;margin-right:8px;border-radius:8px;overflow:hidden}}
.bar span{{display:block;height:100%;background:#2b7fff}}
</style></head><body><h1>{title}</h1><p>Repository-local coding-agent workflow comparison.</p>
<table><thead><tr><th>Variant</th><th>Pass rate</th><th>Trials</th><th>Median time</th><th>Median churn</th><th>Median tokens</th></tr></thead>
<tbody>{rows}</tbody></table></body></html>""".format(
        title=html.escape(f"Benchmark: {name}"), rows="".join(rows)
    )


def write_reports(output_dir: Path, name: str, results: list[TrialResult]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "name": name,
        "summaries": [asdict(summary) for summary in aggregate_results(results)],
        "results": [asdict(result) for result in results],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "summary.md").write_text(render_markdown(name, results), encoding="utf-8")
    (output_dir / "summary.html").write_text(render_html(name, results), encoding="utf-8")
