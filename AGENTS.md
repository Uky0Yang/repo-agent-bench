# Agent Instructions

## Purpose

Maintain `repo-agent-bench`: A/B test coding-agent workflows on your own repository with isolated worktrees and deterministic verification.

## Scope

These instructions apply to code, tests, documentation, and GitHub workflow files in this repository.

## Commands

Run these checks before publishing:

```bash
python -m pip install -e ".[dev]"
python -m pytest --cov=repo_agent_bench --cov-branch
python -m ruff check .
python -m ruff format --check .
python -m compileall -q repo_agent_bench tests examples
python -m repo_agent_bench --version
```

## Safety

- Do not commit secrets, tokens, cookies, private keys, or local environment files.
- Do not add network calls to default checks unless they are explicitly documented.
- Treat benchmark YAML as executable configuration. Never run an untrusted definition.
- A git worktree protects the source checkout; it is not an OS sandbox.
- Keep transcripts local and preserve the default best-effort environment-secret redaction.
- Keep generated files out of commits unless they are part of the published artifact.

## Style

- Keep changes small and reviewable.
- Prefer clear names and deterministic behavior.
- Update tests when behavior changes.
