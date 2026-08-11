# Security Policy

## Execution boundary

Benchmark YAML is executable configuration. Agent commands and verifier commands run with the permissions and environment of the current user.

Detached git worktrees isolate ordinary repository edits from the source checkout. They do not provide filesystem, process, credential, or network isolation. Use only definitions you trust, and put untrusted agents or repositories inside a separate sandbox or disposable machine.

## Artifact privacy

Artifacts stay local. The harness makes no network or model calls by itself and sends no telemetry.

Transcript redaction is best effort. Values of environment variables with secret-like names are replaced before logs are written, but transformed, encoded, split, or independently loaded secrets may remain. Review artifacts before sharing or committing them. `.repo-agent-bench/` is ignored by default.

## Reporting vulnerabilities

Please do not open a public issue containing exploit details or sensitive output. Use GitHub private vulnerability reporting when available. If it is unavailable, open a minimal issue requesting a private maintainer contact without disclosing the vulnerability.
