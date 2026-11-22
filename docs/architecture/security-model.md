# Security model

## 1. Trust boundaries

Patchbay supports local plugin development today. Plugin code must be treated as executable code, not passive data.

### 1.1 In-process execution

The current `PluginManager.run()` path imports and executes Python plugin code inside the Patchbay host process.

A plugin executing in-process can access resources available to the host process, including its filesystem permissions, network access, environment and credentials.

Only trusted local plugins should be executed through this path.

### 1.2 Subprocess worker prototype

Patchbay also has a Python worker entry point that can load and execute a plugin in a separate operating-system process.

The worker communicates with a host over JSON-RPC 2.0 using NDJSON over stdio. The worker bootstrap has an integration test covering initialization, execution and shutdown.

This is process separation, not a hardened sandbox.

The worker currently runs with the operating-system permissions of the process that launches it unless an external execution environment applies additional restrictions. A subprocess alone does not provide filesystem, network, environment, credential or resource isolation.

The reusable host-side worker supervisor and forced process-termination management are still under development.

## 2. Capability model

The plugin manifest may declare capabilities such as:

- `filesystem.read`
- `filesystem.write`
- `network.http`
- `model.inference`
- `secrets.read`
- `database.query`

These declarations describe what a plugin requests. They do not independently grant or restrict access.

During worker initialization, the worker checks that capabilities granted by the host are included in the plugin's declared capabilities. This is a consistency check, not complete capability enforcement.

A future host capability broker must:

- Validate every capability invocation.
- Check the plugin's granted permissions.
- Enforce resource-level restrictions.
- Reject unauthorized operations.
- Avoid exposing host credentials directly to plugins.
- Record structured capability audit events.

## 3. Production security requirements

Before untrusted third-party plugins can be executed, Patchbay needs:

- A managed worker supervisor with reliable termination and cleanup.
- Non-root execution identities where supported.
- Read-only base filesystems and narrowly scoped writable mounts.
- Filesystem access controls.
- Network egress policies.
- CPU, memory, process-count and wall-clock limits.
- Secrets isolation and short-lived credentials.
- Host-mediated capability enforcement.
- Package integrity, signing, provenance and revocation.
- Structured execution and audit events.
- Worker crash handling and recovery policies.
- A documented threat model and security testing process.

Docker alone is not a complete security boundary. Isolation must be designed around the threat model and enforced using appropriate operating-system or stronger sandboxing controls.

## 4. Current project restrictions

Patchbay is an early-stage development project.

Do not execute untrusted plugins through the current in-process loader or the subprocess worker prototype.

Do not represent manifest capability declarations, subprocess execution or stdio communication as a production security boundary.
