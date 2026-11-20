# Patchbay

**Connect. Extend. Create.**

Patchbay is an open-source project exploring a developer-first, language-independent plugin platform for building, distributing, integrating and securely executing reusable software capabilities. The initial implementation is Python-first.

> **Project status: Work in progress.** Patchbay is at an early prototype stage. The current codebase demonstrates a local Python plugin SDK, manifest validation, plugin discovery, in-process loading and a CLI. The plugin protocol, isolated worker runtime, cross-language SDKs, AI plugin APIs and distribution infrastructure are still being designed or planned. APIs and specifications may change.

## What exists today

- A Python workspace managed with uv.
- patchbay-sdk: the initial plugin interface, execution context and result type.
- patchbay-core: local manifest validation, discovery, compatibility checking, loading and execution management.
- patchbay-cli: commands to list, inspect, validate and run local example plugins.
- A Hello World example plugin.
- Initial tests, documentation and GitHub Actions workflows.

The current prototype is intended for development and learning. It is not a production plugin host.

## Where the project is going

Our long-term goal is to build an extensible plugin ecosystem with:

- A stable, language-independent plugin protocol.
- Isolated plugin workers and enforceable capability permissions.
- Python, TypeScript, Go and other SDKs.
- A plugin registry for publishing, versioning and installing packages.
- AI integrations for model providers, embeddings, RAG, agents, guardrails and evaluation.
- Developer tooling and documentation for third-party plugin authors.

## Website, registry and marketplace

**There is no Patchbay website, hosted service, public registry or marketplace yet.** These are planned future components. The website, registry backend, marketplace/Hub interface, publishing and installation workflows, and the supporting infrastructure will be designed and developed after the plugin protocol, runtime and security foundations are in place.

Until then, development happens in this GitHub repository. Please do not treat the project as a production service or submit untrusted executable plugins.

## Quick start

Requirements: Python 3.12+ and uv.

\`\`\`bash
uv sync --all-packages
uv run patchbay --help
uv run patchbay plugin list
uv run patchbay plugin validate plugins/examples/hello-world
uv run patchbay plugin run org.patchbay.examples.hello-world --input '{"name":"Developer"}'
uv run pytest
uv run ruff check .
\`\`\`

## Security boundary

Phase 1 loads trusted local Python code in-process. **Python plugins are arbitrary code**: loading one can access the host process, filesystem, network and credentials. Only run plugins you trust. Manifest capability declarations are descriptive in Phase 1 and are not an enforcement boundary. Do not use the current loader for untrusted plugins.

Before public plugin submissions or untrusted execution, Patchbay needs isolated workers, OS-level restrictions, resource limits, capability enforcement, integrity verification and audit logging.

## Ways to contribute

Patchbay is early, so thoughtful feedback is especially useful. Contributions can help with:

- Reviewing the plugin protocol and API specifications.
- Improving Python SDK/Core/CLI tests and implementation.
- Designing worker isolation and capability enforcement.
- Improving documentation and developer experience.
- Exploring AI plugin interfaces and interoperability.

Please read CONTRIBUTING.md, SECURITY.md and docs/architecture/system-design.md before contributing. For substantial architecture changes, open an issue or discussion first.
