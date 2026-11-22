# System design

## 1. Project architecture

Patchbay is being developed as a modular Python workspace with separately packaged components:

- `patchbay-sdk`: public plugin interfaces, execution context and result types.
- `patchbay-core`: manifest validation, discovery, loading and runtime coordination.
- `patchbay-cli`: developer-facing command-line interface.
- `patchbay-protocol`: language-independent host-to-worker communication contract and Python implementation.

Plugins depend on the SDK. Core depends on the SDK and protocol packages. CLI depends on Core. Core must not depend on a particular plugin implementation.

The initial implementation is Python-first. The protocol is intended to support workers written in other languages in the future.

## 2. Current execution paths

Two execution paths currently exist.

### 2.1 Trusted-local in-process execution

The current `PluginManager.run()` method discovers and loads a Python plugin in the Patchbay host process.

The CLI's `patchbay plugin run` command uses this path.

The plugin executes with the privileges of the host process. This path is intended only for trusted local plugins and is not a sandbox.

### 2.2 Subprocess worker bootstrap

`patchbay-core` contains a worker entry point in `worker.py`.

The worker:

1. Loads and validates a plugin manifest.
2. Accepts a protocol initialization request.
3. Loads and initializes the plugin.
4. Accepts execution requests.
5. Tracks executions through the protocol execution registry.
6. Returns structured results.
7. Handles plugin shutdown and connection closure.

The worker communicates over standard input and standard output using JSON-RPC 2.0 messages framed as NDJSON. Diagnostic output is directed to standard error.

A worker integration test launches the Python worker as a subprocess and verifies initialization, execution and shutdown of the Hello World plugin.

This implementation establishes a working subprocess communication path. It does not yet provide a reusable host-side process supervisor or a hardened security sandbox.

## 3. Protocol layer

`patchbay-protocol` defines the communication boundary between the host and plugin workers.

The initial transport is NDJSON over stdio.

The protocol package includes:

- JSON-RPC message encoding and decoding.
- JSON Schema validation.
- Message framing and size limits.
- Bidirectional asynchronous RPC.
- Request correlation and structured errors.
- Execution tracking and cooperative cancellation.

The protocol specification remains a draft. Some proposed protocol features and runtime behaviours are not yet implemented.

The protocol must remain independent of the language used to implement a worker.

## 4. Intended host runtime architecture

The next runtime component is a host-side `WorkerManager`.

Its responsibilities are expected to include:

- Resolving plugin manifests and runtime configuration.
- Starting and supervising worker subprocesses.
- Establishing JSON-RPC communication.
- Performing protocol and host API compatibility checks.
- Routing execution requests.
- Enforcing execution deadlines.
- Coordinating cooperative cancellation.
- Terminating workers that fail to stop.
- Monitoring process exits and broken connections.
- Capturing worker diagnostics.
- Cleaning up processes and temporary resources.

A `WorkerHandle` should represent one worker process and its RPC connection. The manager should own and coordinate multiple worker handles.

The normal CLI execution path should eventually use this managed runtime rather than loading plugin code directly into the host process.

## 5. Worker lifecycle

The intended managed worker lifecycle is:

`STARTING -> READY -> BUSY -> READY -> STOPPING -> STOPPED`

Failure paths include:

- Startup failure.
- Initialization failure.
- Execution failure.
- Execution timeout.
- Cancellation escalation.
- Unexpected process exit.
- Communication failure.
- Shutdown failure.

A worker that has failed or required forced termination must not be reused.

The initial runtime should serialize executions per worker. Concurrent execution can be introduced later through an explicit, documented concurrency contract.

## 6. Security architecture

A subprocess is a process boundary, not automatically a security boundary.

The worker currently executes with the operating-system permissions available to the process that launches it. A production runtime must add operating-system-level controls and host-mediated capabilities.

Manifest capability declarations and the worker's initialization checks do not constitute complete permission enforcement.

The production security model is described in `security-model.md`.

## 7. Future ecosystem components

After the runtime and security foundations mature, Patchbay is expected to add:

- TypeScript and Go worker SDKs.
- Plugin packaging and distribution.
- A registry for publishing and versioning plugins.
- A website and marketplace/Hub interface.
- AI plugin interfaces for model providers, embeddings, RAG, agents, guardrails and evaluation.

These are future components, not current repository capabilities.
