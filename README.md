# Patchbay

**Connect. Extend. Create.**

Patchbay is an open-source project exploring a developer-first, language-independent plugin platform for building, integrating and executing reusable software capabilities. The initial implementation is Python-first.

> **Project status: Work in progress.** Patchbay is an early-stage prototype. The repository currently contains an initial Python SDK, Core, CLI, manifest validation, a JSON-RPC protocol implementation and a Python subprocess worker bootstrap. APIs and specifications may change as the project develops.

## What exists today

- **Python workspace:** A multi-package workspace managed with `uv`.
- **Patchbay SDK:** Plugin interface, execution context and result types.
- **Patchbay Core:** Manifest validation, plugin discovery, trusted-local loading and execution management.
- **Patchbay CLI:** Commands to list, inspect, validate and run local example plugins.
- **Patchbay Protocol:** JSON-RPC 2.0 communication over NDJSON, message validation, asynchronous RPC and execution tracking.
- **Python worker bootstrap:** A worker entry point that can initialize, execute and shut down a plugin in a separate subprocess.
- **Example plugin:** A Hello World reference plugin.
- **Quality checks:** Unit tests, protocol tests, worker integration tests and GitHub Actions workflows.

The worker bootstrap has been integration-tested, but a reusable host-side worker manager has not yet been implemented. The standard CLI execution command still uses the trusted-local in-process execution path.

## Project vision

Patchbay aims to provide a common foundation for developers to create and connect reusable plugins, regardless of the language used to implement them.

The long-term architecture is organized around these areas:

- **Core:** Plugin discovery, manifest validation, orchestration and lifecycle management.
- **SDKs:** Language-specific developer interfaces built around a language-independent protocol. Python comes first, with TypeScript, Go and other languages as future goals.
- **Protocol:** A defined communication contract between the host and plugin workers.
- **Runtime:** Managed worker processes, execution control, lifecycle supervision and resource management.
- **Security:** Enforceable capabilities, isolation, permissions, package integrity and audit events.
- **AI integrations:** Interfaces for model providers, embeddings, RAG, agents, guardrails, evaluation and observability.
- **Registry and marketplace:** Future publishing, discovery, versioning, distribution and installation of plugins.

These are project goals, not claims that every component is already implemented.

## Website, registry and marketplace

**The Patchbay website, hosted service, public registry and marketplace do not exist yet.**

A website and the infrastructure needed to operate a plugin marketplace will be developed in a later phase, after the protocol, runtime and security foundations have matured. Planned work includes the registry backend, marketplace or Hub interface, plugin publishing and installation workflows, version management, documentation and supporting services.

For now, development, issue tracking and contributions take place in this GitHub repository.

## Getting started

### Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

### Install the workspace

```bash
uv sync --all-packages
```

### Explore the CLI

```bash
uv run patchbay --help
uv run patchbay plugin list
```

### Validate and inspect the example plugin

```bash
uv run patchbay plugin validate plugins/examples/hello-world
uv run patchbay plugin inspect org.patchbay.examples.hello-world
```

### Run the example plugin

```bash
uv run patchbay plugin run org.patchbay.examples.hello-world --input '{"name":"Developer"}'
```

The current `patchbay plugin run` command executes trusted local Python plugins in-process. It does not use the subprocess worker yet.

### Run quality checks

```bash
uv run pytest
uv run ruff check .
git diff --check
```

## Runtime and security status

Patchbay currently has two distinct execution paths:

1. **Trusted-local in-process execution:** The existing CLI execution path loads and runs Python plugin code inside the Patchbay host process.
2. **Subprocess worker prototype:** A separate worker entry point communicates over JSON-RPC 2.0 using NDJSON over standard input and output. The worker bootstrap has an integration test, but a reusable host-side worker manager and supervisor are still planned.

A subprocess is a process boundary, not automatically a security sandbox. The current worker runs with the operating-system permissions of the process that launches it unless an external execution environment applies additional restrictions.

Manifest capability declarations are not yet enforceable permissions. The worker currently checks that capabilities granted during initialization were declared by the plugin, but this is not complete capability enforcement or a security boundary.

Before Patchbay can safely support untrusted third-party plugins, the project needs a managed host-side worker supervisor, operating-system-level restrictions, filesystem and network controls, resource limits, secrets isolation, host-mediated capability enforcement, package integrity and provenance checks, and structured audit logging.

**Do not treat the current prototype as a production plugin sandbox. Only run plugins you trust.**

See [`docs/architecture/security-model.md`](docs/architecture/security-model.md) for the current security model and outstanding requirements.

## Contributing

Patchbay is an open-source project in active development. Contributions and thoughtful technical feedback are welcome, especially around:

- Reviewing the plugin protocol and API specifications.
- Improving the Python SDK, Core and CLI.
- Building the host-side worker manager and lifecycle supervisor.
- Designing capability enforcement and runtime isolation.
- Adding tests and improving documentation.
- Exploring cross-language plugin interoperability and AI integrations.

Before contributing, please review:

- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- [`SECURITY.md`](SECURITY.md)
- [`docs/architecture/system-design.md`](docs/architecture/system-design.md)

For substantial changes, open an issue or discussion first so the design can be reviewed before implementation.

## Project status and roadmap

Patchbay is still under development. The immediate engineering priority is to evolve the subprocess worker bootstrap into a managed host runtime with reliable startup, execution, cancellation, process termination, failure detection and cleanup.

After that foundation is established, development can progress toward enforceable capabilities, stronger isolation, additional language SDKs, plugin packaging and eventually the registry and marketplace ecosystem.

The repository's specifications and APIs are subject to change while these foundations are being built.

## License

See the repository's `LICENSE` file for the applicable license terms.
