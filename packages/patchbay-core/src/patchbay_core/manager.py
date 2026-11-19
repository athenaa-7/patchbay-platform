"""Small local plugin manager for Phase 1."""
from pathlib import Path
from typing import Any
from patchbay_sdk import PluginContext, PluginResult
from patchbay_core.discovery import discover_plugins
from patchbay_core.exceptions import PluginExecutionError, PluginLoadError
from patchbay_core.loader import load_plugin
from patchbay_core.validator import load_manifest

class PluginManager:
    def __init__(self, plugin_root: Path, data_root: Path | None = None) -> None:
        self.plugin_root = plugin_root.resolve()
        self.data_root = (data_root or self.plugin_root / ".data").resolve()

    def list_plugins(self) -> list[dict[str, str]]:
        return [{"id": pid, "path": str(path)} for path, pid in discover_plugins(self.plugin_root)]

    def inspect(self, plugin_id: str) -> tuple[Path, Any]:
        for path, found_id in discover_plugins(self.plugin_root):
            if found_id == plugin_id:
                return path, load_manifest(path)
        raise PluginLoadError(f"Plugin not found: {plugin_id}")

    def run(self, plugin_id: str, inputs: dict[str, Any]) -> PluginResult:
        path, manifest = self.inspect(plugin_id)
        plugin = load_plugin(path, manifest)
        context = PluginContext(plugin_id=manifest.id, data_dir=self.data_root / manifest.id,
                                 config=manifest.configuration)
        context.data_dir.mkdir(parents=True, exist_ok=True)
        try:
            plugin.initialize(context)
            result = plugin.execute(context, inputs)
            if not isinstance(result, PluginResult):
                raise PluginExecutionError("Plugin execute() must return PluginResult")
            return result
        except Exception as exc:
            raise PluginExecutionError(f"Plugin {plugin_id} failed: {exc}") from exc
        finally:
            try:
                plugin.shutdown()
            except Exception:
                pass
