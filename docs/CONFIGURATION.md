# Configuration reference

Benchmark definitions are YAML files. They are executable configuration because `command` and `checks` start local processes. Review them before running.

## Top-level fields

| Field | Required | Meaning |
| --- | --- | --- |
| `version` | yes | Schema version. v0.1 accepts `1`. |
| `name` | yes | Lowercase artifact identifier using letters, numbers, and hyphens. |
| `repository` | yes | Git worktree root, relative to the YAML file or absolute. |
| `base_ref` | no | Commit/ref used for every detached worktree. Default: `HEAD`. |
| `prompt` | yes | Identical task prompt passed to each command. |
| `trials` | no | Repetitions per variant. Default: `1`. |
| `timeout_seconds` | no | Deadline for each agent command and each check. Default: `900`. |
| `checks` | no | Deterministic verifier commands, each expressed as an argument array. |
| `allowed_paths` | no | Glob patterns for acceptable changed files. Any unmatched change fails the trial. |
| `variants` | yes | Named workflow configurations to compare. |

## Variant fields

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | yes | Lowercase stable identifier. |
| `command` | yes | Agent executable and arguments. No shell interpolation is used. |
| `remove` | no | Repository-relative files/directories hidden from this variant. |
| `overlay` | no | Files/directories copied into the worktree before the measurement baseline is committed. |

Overlay sources are relative to the benchmark YAML. Targets are relative to the disposable worktree:

```yaml
variants:
  - name: candidate
    overlay:
      - source: variants/candidate-agents.md
        target: AGENTS.md
      - source: variants/review-skill
        target: .agents/skills/review
    command: [codex, exec, --json, "{prompt}"]
```

Absolute targets and `..` traversal are rejected. Symlink-resolved targets that escape the worktree are also rejected at runtime.

## Placeholders

Every command argument may contain:

- `{prompt}` — the benchmark prompt
- `{workspace}` — absolute path to the temporary worktree

Placeholders are string replacements inside individual arguments. Commands are not passed to a shell, so pipes, redirects, `$()` and shell variables are not interpreted.

## Pass/fail rules

A trial passes only when all conditions hold:

1. The agent command exits with code `0` before the timeout.
2. Every verifier command exits with code `0` before the timeout.
3. Every changed path matches at least one `allowed_paths` pattern, when the list is present.

No LLM judge is used in v0.1.

## Exit codes

| Code | Meaning |
| ---: | --- |
| `0` | Validation succeeded, or every selected trial passed. |
| `1` | The benchmark ran and at least one trial failed. |
| `2` | Configuration or harness error; trials were not meaningfully comparable. |

## Artifacts

The run directory contains:

- `summary.json` — schema-versioned machine-readable data
- `summary.md` — PR-ready comparison
- `summary.html` — self-contained report with no external assets
- `trial-<variant>-<n>.stdout.txt` and `.stderr.txt`
- `trial-<variant>-<n>.check-<n>.stdout.txt` and `.stderr.txt`

The tool attempts to redact values from environment variables whose names look like tokens, keys, secrets, passwords, credentials, cookies, or auth material. Treat output as sensitive anyway: arbitrary tools may transform or split secrets in ways best-effort redaction cannot recognize.
