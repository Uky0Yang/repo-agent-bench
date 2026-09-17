# Real-repository case: context-card freshness checks

This case asks a coding agent to add `--check` to the public
[repo-context-card repository](https://github.com/Uky0Yang/repo-context-card/tree/6cc18043da0256d30d416026f5140e901d8c646d).
It is not the deterministic fake-agent demo. The base is pinned to the version
before this feature; the harness creates disposable worktrees, leaving the source
checkout unchanged.

## Reproduce

Clone `repo-context-card` next to `repo-agent-bench` and fetch the pinned commit.
Install this benchmark project and make a signed-in `codex` CLI available on PATH.
Review `benchmark.yml` before running it: configuration is executable, trials use
your model allowance, and a Git worktree is not an OS security boundary.

```bash
repo-agent-bench validate examples/context-card-check/benchmark.yml
repo-agent-bench run examples/context-card-check/benchmark.yml --output .repo-agent-bench/context-card-check
```

Both variants receive the same task and acceptance tests. The baseline removes
repository AGENTS.md; the guided variant substitutes the published task-specific
guidance. Both use `codex exec --ephemeral --sandbox workspace-write --json`.
The sandbox must be supported and enabled on the host; do not remove it to obtain
a passing score. Other shared user/global instructions may still be loaded.

## What the experiment can establish

The checks require stable Markdown and JSON cards, no writes in check mode,
correct missing/stale status, and the original test suite. Changes to acceptance
files are outside the allowed paths and invalidate a trial. Passing these tests
does not prove complete correctness or security.

One trial per variant is a **pilot**, not a statistically credible ranking. Record
the Codex version, effective model/reasoning settings, OS, Python/Git versions,
base SHA, task guidance, timeout and trial count with any published result.
Model calls are stochastic and remote model implementations may change.

Raw transcripts stay under the ignored `.repo-agent-bench/` directory. Review and
redact before sharing; automatic redaction is best-effort. Never publish local
paths, account/session identifiers, credentials or full private configuration.

[The 2026-09-17 pilot results](RESULTS.md) record two completed real trials:
both passed functional checks and failed the predeclared file-scope gate.
The report includes the prompt's scope-disclosure limitation and makes no
performance or reliability claim from one trial per variant.
