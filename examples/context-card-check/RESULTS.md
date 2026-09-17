# Context-card check pilot — 2026-09-17

Two real Codex CLI trials completed: one baseline and one guided. Both passed
their functional tests; both failed the benchmark's file-scope gate because
they also edited `README.md`. No trial was retried, and the original acceptance
tests and allowed paths were not changed after execution.

## Conditions

- Harness: repo-agent-bench 0.1.1, repository commit `8f115cf`.
- Target: repo-context-card at `6cc18043da0256d30d416026f5140e901d8c646d`.
- Case: the adjacent [benchmark.yml](benchmark.yml), [GUIDANCE.md](GUIDANCE.md)
  and [acceptance.py](acceptance.py), as published before the run.
- Codex CLI: `0.155.0-alpha.2.6`; Windows; Python 3.13.14; Git 2.55.0.windows.5.
- Command: `codex exec --ephemeral --sandbox workspace-write --json <prompt>`.
- Local default configuration read after execution: model `gpt-6-astra`,
  reasoning effort `high`. There was no per-command model override. The captured
  result does not independently attest the effective remote model revision.
- One trial per variant, sequential baseline then guided, 600-second timeout each.
  Both agents exited 0 without timing out. Disposable worktrees were removed by
  the harness; the source checkout remained unchanged.
- Shared user/global configuration was not disabled. Removing repository
  AGENTS.md does not make the baseline an instruction-free environment.

## Observations

| Measurement | Baseline | Guided |
| --- | ---: | ---: |
| Overall accepted trials | 0 / 1 | 0 / 1 |
| Repository unit tests | 11 passed | 11 passed |
| Fixed acceptance tests | 2 passed | 2 passed |
| Agent elapsed seconds | 206.43 | 155.24 |
| Changed files | 5 | 4 |
| Added / deleted lines | 154 / 13 | 146 / 13 |
| Out-of-scope file | README.md | README.md |
| Reported input tokens | 320,488 | 207,690 |
| Reported cached input tokens | 274,432 | 164,224 |
| Reported output tokens | 4,949 | 4,037 |

Cached input is a subset of reported input, not an additional quantity. These
are CLI-reported usage counters, not a bill or independently verified cost.
Elapsed seconds cover the agent command, not the subsequent harness checks.
Repository test counts include tests added by each agent; the two acceptance
tests are the fixed checks shared by both.

The predeclared allowed paths were `repo_context_card/*.py` and `tests/*.py`.
Both agents implemented enough of the feature to pass the available tests, but
their README changes made the complete trials fail that gate.

Important design limitation: the allowed-path list was enforced by the harness
but was **not explicitly included in the task prompt or task-specific guidance**.
This is evidence of a scope-gate failure, not a fair demonstration that either
agent knowingly ignored an explicit README prohibition. A future, separately
versioned experiment should state that constraint in both prompts.

## What this does not establish

This n=1 pilot does not establish that guidance improves speed, token efficiency
or reliability. Run order, caching, shared configuration and model variability
are uncontrolled factors. Passing the available tests does not establish full
correctness or security. There is no winning variant in this experiment.

[results.json](results.json) contains the reviewed numerical observations.
Raw transcripts, private configuration and local/session identifiers are not
published. No follow-up model trials were run to obtain a better-looking result.
