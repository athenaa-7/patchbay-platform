# Patchbay Plugin API v1

Plugins subclass `patchbay_sdk.PatchbayPlugin` and implement:

- `initialize(context: PluginContext) -> None`
- `execute(context: PluginContext, inputs: dict) -> PluginResult`
- `shutdown() -> None`

The SDK result status is either `success` or `error`. The host validates returned result types. The initial API is synchronous and Python-only.
