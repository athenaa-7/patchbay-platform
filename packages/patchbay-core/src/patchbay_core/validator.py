"""Manifest loading and compatibility validation."""

import json
from pathlib import Path

from pydantic import ValidationError

from patchbay_core.exceptions import ManifestError
from patchbay_core.models import PluginManifest

MANIFEST_NAME = "patchbay.json"
HOST_API_VERSION = "1.0"


def load_manifest(plugin_dir: Path) -> PluginManifest:
    path = plugin_dir / MANIFEST_NAME
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        manifest = PluginManifest.model_validate(raw)
        manifest.resolve_entrypoint(plugin_dir)
        if manifest.host.api_version != HOST_API_VERSION:
            raise ManifestError(
                f"Plugin requires host API {manifest.host.api_version}; "
                f"engine supports {HOST_API_VERSION}"
            )
        return manifest
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        if isinstance(exc, ManifestError):
            raise
        raise ManifestError(f"Invalid plugin at {plugin_dir}: {exc}") from exc
