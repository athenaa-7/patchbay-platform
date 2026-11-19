"""Standard plugin execution result."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PluginResult:
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"success", "error"}:
            raise ValueError("status must be 'success' or 'error'")
        if self.status == "success" and self.error is not None:
            raise ValueError("successful results cannot contain an error")
        if self.status == "error" and not self.error:
            raise ValueError("error results must include an error message")
