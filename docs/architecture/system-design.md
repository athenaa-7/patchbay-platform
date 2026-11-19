# System design

Patchbay begins as a modular monolith with three separately packaged Python distributions: SDK, Core and CLI. The SDK defines the plugin contract. Core validates manifests, discovers local plugin directories, loads trusted local Python modules and coordinates lifecycle. CLI exposes developer commands.

Dependency direction: plugins depend on SDK; Core depends on SDK; CLI depends on Core and SDK. Core must never depend on a specific plugin implementation.

The Phase 1 loader imports plugin code into the current process. The manager is the seam for a future worker runtime communicating over a versioned IPC protocol. Production execution must move untrusted code out of process and enforce permissions using OS-level controls.
