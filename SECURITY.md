# Security Policy

## Supported versions
Patchbay is in early development. Security fixes are currently applied to the latest code on `main`.

## Reporting
Do not publish exploitable vulnerability details in a public issue. Use GitHub private vulnerability reporting for this repository, if enabled, or contact maintainers privately through a verified channel. Include affected commit/version, impact, reproduction steps and proof-of-concept details.

## Current limitations
Phase 1 imports and executes trusted local Python plugins inside the Patchbay process. This is not a sandbox. A plugin can execute arbitrary code with the host process's privileges. Do not run untrusted plugins or expose the loader to public uploads.

Manifest capabilities are metadata only in Phase 1. They do not restrict filesystem, network or process access. Production isolation requires separate workers, OS-level controls, resource limits, secrets isolation and explicit IPC.
