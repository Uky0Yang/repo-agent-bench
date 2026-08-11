# Contributing

Thanks for helping make coding-agent workflow comparisons more trustworthy.

## Good first contributions

- Add JSONL token-usage fixtures from a documented agent CLI.
- Add edge cases for git rename, deletion, binary, or unusual-path evidence.
- Improve the deterministic demo or report accessibility.
- Propose a provider adapter without coupling the core runner to provider authentication.

## Setup

```bash
python -m pip install -e ".[dev]"
```

## Required checks

```bash
python -m pytest --cov=repo_agent_bench --cov-branch
python -m ruff check .
python -m ruff format --check .
python -m compileall -q repo_agent_bench tests examples
python -m build
```

Behavior changes must follow RED → GREEN → VERIFY: add a test that fails for the intended reason, implement the smallest fix, then run the complete suite.

## Pull requests

- Keep changes focused and deterministic.
- Do not add a hosted dependency or model call to the default path.
- Document any command execution, network, credential, cost, or sandbox implication.
- Never include real transcripts, API keys, cookies, or private repository content in fixtures.
