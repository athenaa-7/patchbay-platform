"""Domain exceptions for the Patchbay engine."""


class PatchbayError(Exception):
    """Base exception for expected Patchbay errors."""


class ManifestError(PatchbayError):
    """Plugin manifest is missing or invalid."""


class PluginLoadError(PatchbayError):
    """Plugin could not be loaded or did not satisfy the SDK contract."""


class PluginExecutionError(PatchbayError):
    """Plugin initialization or execution failed."""
