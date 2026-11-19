# Patchbay

**Connect. Extend. Create.**

Patchbay is an open-source, Python-first plugin platform for building, validating, managing and executing modular software extensions.

> **Status:** early development. Phase 1 is a local developer engine, not a production sandbox or public plugin marketplace.

## Goals
- Give plugin authors a small, stable SDK.
- Define a versioned manifest and host API contract.
- Discover and validate local plugins.
- Manage plugin lifecycle and execution through a consistent interface.
- Keep the runtime boundary replaceable so isolated workers can be added later.

## Quick start
Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-packages
uv run patchbay --help
uv run patchbay plugin list
uv run patchbay plugin validate plugins/examples/hello-world
uv run patchbay plugin run org.patchbay.examples.hello-world --input '{"name":"Developer"}'
uv run pytest
```

## Security boundary
Phase 1 loads trusted local Python code in-process. **Python plugins are arbitrary code**: loading one can access the host process, filesystem, network and credentials. Only run plugins you trust. Manifest capabilities are descriptive in Phase 1 and are not an enforcement boundary. Public uploads and untrusted execution are out of scope until isolated workers and OS-level controls exist.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [docs/architecture/system-design.md](docs/architecture/system-design.md).
