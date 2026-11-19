# Patchbay manifest v1

Each plugin directory contains `patchbay.json`.

Required fields: `id`, `name`, `version`, `host.api_version`. Optional fields include description, author, license, runtime, entrypoint, capabilities, dependencies and configuration.

Plugin IDs use lowercase letters, digits, dots and hyphens. Versions use a SemVer-like three-component format. Phase 1 supports Python only and requires host API `1.0`.

Capabilities are declarations only in Phase 1. They do not grant or restrict access.
