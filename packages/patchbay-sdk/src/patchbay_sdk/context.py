"""Execution context exposed to plugins."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PluginContext:
    """Host-provided context. Capabilities are descriptive in Phase 1, not enforced."""

    plugin_id: str
    data_dir: Path
    config: dict[str, Any] = field(default_factory=dict)
    granted_capabilities: tuple[str, ...] = ()
