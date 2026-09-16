# Task-specific repository guidance

Implement the smallest CLI change backed by regression tests.

- Write a failing generate-then-check test before implementation.
- A generated output inside the scanned root must not count as input on the next run.
- Compare the same rendering mode and scan options when checking.
- A missing or stale card is exit code 1, not an implicit request to regenerate it.
- Cover Markdown and JSON; keep the existing tests passing.
- Do not alter the acceptance tests, commit changes, access the network, use subagents or touch files outside this worktree.
- Run `python -m unittest discover -s tests` and `python -m unittest discover -s .benchmark`.
