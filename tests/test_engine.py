from pathlib import Path

import pytest
from patchbay_core.exceptions import ManifestError
from patchbay_core.manager import PluginManager
from patchbay_core.validator import load_manifest

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "plugins" / "examples" / "hello-world"

def test_example_manifest_is_valid() -> None:
    manifest = load_manifest(EXAMPLE)
    assert manifest.id == "org.patchbay.examples.hello-world"

def test_example_plugin_executes() -> None:
    manager = PluginManager(ROOT / "plugins" / "examples")
    result = manager.run("org.patchbay.examples.hello-world", {"name": "Patchbay"})
    assert result.status == "success"
    assert result.data["message"] == "Hello, Patchbay!"

def test_missing_manifest_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ManifestError):
        load_manifest(tmp_path)

def test_entrypoint_path_traversal_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "patchbay.json").write_text(
        '{"id":"org.example.bad","name":"Bad","version":"1.0.0",'
        '"host":{"api_version":"1.0"},'
        '"entrypoint":{"file":"../escape.py","class":"Bad"}}',
        encoding="utf-8",
    )
    with pytest.raises(ManifestError):
        load_manifest(tmp_path)
