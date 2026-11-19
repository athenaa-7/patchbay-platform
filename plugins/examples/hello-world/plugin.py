"""Reference hello-world plugin."""
from patchbay_sdk import PatchbayPlugin, PluginContext, PluginResult

class HelloWorldPlugin(PatchbayPlugin):
    def initialize(self, context: PluginContext) -> None:
        self.context = context

    def execute(self, context: PluginContext, inputs: dict) -> PluginResult:
        name = str(inputs.get("name", "developer"))
        return PluginResult(status="success",
                            data={"message": f"Hello, {name}!", "plugin": context.plugin_id})

    def shutdown(self) -> None:
        pass
