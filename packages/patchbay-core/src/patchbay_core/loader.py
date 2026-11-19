"""Trusted-local Python plugin loader. This is not a sandbox."""

import importlib.util
import sys
import uuid
from pathlib import Path

from patchbay_sdk import PatchbayPlugin

from patchbay_core.exceptions import PluginLoadError
from patchbay_core.models import PluginManifest


def load_plugin(plugin_dir: Path, manifest: PluginManifest) -> PatchbayPlugin:
    entrypoint = manifest.resolve_entrypoint(plugin_dir)
    module_name = f"_patchbay_plugin_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, entrypoint)
    if spec is None or spec.loader is None:
        raise PluginLoadError(f"Cannot create import spec for {entrypoint}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        plugin_class = getattr(module, manifest.entrypoint.class_name)
        if not isinstance(plugin_class, type) or not issubclass(plugin_class, PatchbayPlugin):
            raise PluginLoadError("Entrypoint class must subclass PatchbayPlugin")
        return plugin_class()
    except Exception as exc:
        sys.modules.pop(module_name, None)
        if isinstance(exc, PluginLoadError):
            raise
        raise PluginLoadError(f"Plugin import failed: {exc}") from exc
