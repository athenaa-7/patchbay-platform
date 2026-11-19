"""Validated plugin manifest models."""
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuntimeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str = "python"
    minimum_version: str = "3.12"


class HostSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_version: str


class EntrypointSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    file: str = "plugin.py"
    class_name: str = Field(alias="class")


class PluginManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]*$")
    name: str = Field(min_length=1, max_length=100)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
    description: str = ""
    author: str = ""
    license: str = ""
    runtime: RuntimeSpec = Field(default_factory=RuntimeSpec)
    host: HostSpec
    entrypoint: EntrypointSpec = Field(default_factory=EntrypointSpec)
    capabilities: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)

    def resolve_entrypoint(self, plugin_dir: Path) -> Path:
        """Resolve entrypoint while rejecting traversal and symlink escapes."""
        root = plugin_dir.resolve(strict=True)
        candidate = (root / self.entrypoint.file).resolve(strict=True)
        if not candidate.is_relative_to(root):
            raise ValueError("entrypoint must remain inside the plugin directory")
        if self.runtime.language != "python":
            raise ValueError("Phase 1 supports Python plugins only")
        if not candidate.is_file() or candidate.suffix != ".py":
            raise ValueError("entrypoint must be an existing Python file")
        return candidate
