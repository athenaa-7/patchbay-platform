# Security model

## Phase 1 trust model
Only trusted local plugins may be loaded. Importing Python code executes it with the host process privileges. This is arbitrary code execution, not a sandbox.

Capabilities in `patchbay.json` are declarations only in Phase 1. They do not grant or restrict access.

## Production requirements
- Separate worker processes or hardened containers.
- Non-root identity, read-only base filesystem and narrowly scoped mounts.
- Network egress policy and explicit capability mediation.
- CPU, memory, process and wall-clock limits.
- Secrets isolation and short-lived credentials.
- Package integrity, signatures/provenance and revocation.
- Structured audit events and a documented threat model.

Docker alone is not a complete security boundary.
