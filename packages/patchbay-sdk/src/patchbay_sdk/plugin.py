"""Base class every Patchbay plugin must implement."""

from abc import ABC, abstractmethod
from typing import Any

from patchbay_sdk.context import PluginContext
from patchbay_sdk.result import PluginResult


class PatchbayPlugin(ABC):
    """Stable lifecycle contract for Python plugins."""

    @abstractmethod
    def initialize(self, context: PluginContext) -> None:
        """Prepare plugin state before execution."""

    @abstractmethod
    def execute(self, context: PluginContext, inputs: dict[str, Any]) -> PluginResult:
        """Execute one operation and return a structured result."""

    @abstractmethod
    def shutdown(self) -> None:
        """Release plugin-owned resources."""
