"""Execution context exposed to plugins."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PluginContext:
    """Host-provided context for one plugin lifecycle or execution."""

    plugin_id: str
    data_dir: Path
    config: dict[str, Any] = field(default_factory=dict)
    granted_capabilities: tuple[str, ...] = ()
    cancellation_event: Any | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    @property
    def cancellation_requested(self) -> bool:
        """Check whether the current execution has been cancelled."""
        return (
            self.cancellation_event is not None
            and self.cancellation_event.is_set()
        )
