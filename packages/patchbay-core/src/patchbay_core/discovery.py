"""Local plugin directory discovery."""

from pathlib import Path

from patchbay_core.exceptions import ManifestError
from patchbay_core.validator import load_manifest


def discover_plugins(root: Path) -> list[tuple[Path, str]]:
    if not root.exists():
        return []
    found: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.is_symlink():
            continue
        try:
            manifest = load_manifest(child)
        except ManifestError:
            continue
        if manifest.id in seen:
            continue
        seen.add(manifest.id)
        found.append((child, manifest.id))
    return found
