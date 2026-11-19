# Creating a plugin

Create a directory containing `patchbay.json` and a Python entrypoint.

The manifest identifies the plugin, its version, the host API version and the class to load. The entrypoint class must subclass `patchbay_sdk.PatchbayPlugin` and implement `initialize`, `execute` and `shutdown`.

Return a `PluginResult` from `execute`. Keep plugin dependencies explicit and document their purpose.

Validate the directory with:

```bash
uv run patchbay plugin validate ./path/to/plugin
```

Phase 1 runs trusted local Python plugins in-process. Do not distribute or execute untrusted plugins through this loader.
