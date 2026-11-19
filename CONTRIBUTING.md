# Contributing to Patchbay

Contributions of code, tests, documentation, examples and issue reports are welcome.

## Setup
- Python 3.12+
- uv
- Git

```bash
git clone https://github.com/athenaa-7/patchbay-platform.git
cd patchbay-platform
uv sync --all-packages
uv run pytest
uv run ruff check .
```

## Workflow
1. Open or comment on an issue before large changes.
2. Create a focused branch from `main`.
3. Add or update tests and documentation.
4. Run tests and linting.
5. Open a pull request with motivation, design notes and security impact.

## Design guidelines
- Keep the SDK small and stable.
- Keep core independent of specific plugins.
- Do not treat manifest capability declarations as enforcement.
- Do not load untrusted plugin code in-process.
- Prefer explicit errors and deterministic behavior.
- Avoid dependencies without a clear need.

Contributions are offered under the repository's Apache-2.0 license, subject to applicable law.
