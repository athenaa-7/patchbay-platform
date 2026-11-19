# Plugin lifecycle

Intended lifecycle: Discovered -> Validated -> Installed -> Initialized -> Active -> Executing -> Active, with Disabled, Rejected and Failed side states.

Phase 1 implements discovery, validation, initialization, execution and shutdown for local example plugins. It does not yet persist installed state or provide enable/disable commands.
