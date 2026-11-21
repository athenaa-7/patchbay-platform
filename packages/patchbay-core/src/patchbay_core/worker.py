"""Subprocess entry point for Patchbay Python plugin workers."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from patchbay_protocol import (
    DEFAULT_MAX_MESSAGE_BYTES,
    ExecutionRegistry,
    JsonRpcPeer,
    RpcMethodError,
)
from patchbay_sdk import PatchbayPlugin, PluginContext, PluginResult

from patchbay_core.loader import load_plugin
from patchbay_core.models import PluginManifest
from patchbay_core.validator import load_manifest

logger = logging.getLogger("patchbay.worker")


class PluginWorkerRuntime:
    """Manage one plugin instance inside a worker process."""

    def __init__(self, plugin_dir: Path, data_dir: Path) -> None:
        self.plugin_dir = plugin_dir.resolve(strict=True)
        self.data_dir = data_dir.resolve()
        self.manifest: PluginManifest = load_manifest(self.plugin_dir)

        self.plugin: PatchbayPlugin | None = None
        self.configuration: dict[str, Any] = {}
        self.granted_capabilities: tuple[str, ...] = ()

    async def initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Initialize the plugin after host protocol negotiation."""
        if self.plugin is not None:
            raise RpcMethodError(
                -32004,
                "Plugin is already initialized",
            )

        if params.get("protocol_version") != "1.0":
            raise RpcMethodError(
                -32005,
                "Unsupported protocol version",
            )

        if params.get("plugin_id") != self.manifest.id:
            raise RpcMethodError(
                -32004,
                "Plugin identity mismatch",
            )

        configuration = params.get("configuration", {})
        granted = params.get("granted_capabilities", [])

        if not isinstance(configuration, dict):
            raise RpcMethodError(-32602, "Configuration must be an object")

        if not isinstance(granted, list) or not all(
            isinstance(item, str) for item in granted
        ):
            raise RpcMethodError(-32602, "Granted capabilities must be strings")

        undeclared = set(granted) - set(self.manifest.capabilities)

        if undeclared:
            raise RpcMethodError(
                -32002,
                "Host granted capabilities not declared by the plugin",
                data={"capabilities": sorted(undeclared)},
            )

        self.data_dir.mkdir(parents=True, exist_ok=True)

        plugin = await asyncio.to_thread(
            load_plugin,
            self.plugin_dir,
            self.manifest,
        )

        context = PluginContext(
            plugin_id=self.manifest.id,
            data_dir=self.data_dir,
            config=configuration,
            granted_capabilities=tuple(sorted(granted)),
        )

        try:
            await asyncio.to_thread(plugin.initialize, context)
        except Exception as exc:
            logger.exception("Plugin initialization failed")
            try:
                await asyncio.to_thread(plugin.shutdown)
            except Exception:
                logger.exception("Cleanup after initialization failure failed")

            raise RpcMethodError(
                -32004,
                "Plugin initialization failed",
                data={"exception_type": type(exc).__name__},
            ) from exc

        self.plugin = plugin
        self.configuration = configuration
        self.granted_capabilities = tuple(sorted(granted))

        return {
            "status": "success",
            "protocol_version": "1.0",
            "supported_features": ["cancellation"],
        }

    async def execute(
        self,
        params: dict[str, Any],
        cancellation_event: asyncio.Event,
    ) -> dict[str, Any]:
        """Execute a plugin operation in a worker thread."""
        if self.plugin is None:
            raise RpcMethodError(
                -32004,
                "Plugin is not initialized",
            )

        inputs = params.get("input")

        if not isinstance(inputs, dict):
            raise RpcMethodError(
                -32602,
                "Plugin input must be an object",
            )

        context = PluginContext(
            plugin_id=self.manifest.id,
            data_dir=self.data_dir,
            config=self.configuration,
            granted_capabilities=self.granted_capabilities,
            cancellation_event=cancellation_event,
        )

        result = await asyncio.to_thread(
            self.plugin.execute,
            context,
            inputs,
        )

        if not isinstance(result, PluginResult):
            raise RpcMethodError(
                -32603,
                "Plugin must return PluginResult",
            )

        if result.status == "error":
            raise RpcMethodError(
                -32001,
                result.error or "Plugin execution failed",
                data={"execution_id": params["execution_id"]},
            )

        return result.data

    async def shutdown(self, params: dict[str, Any]) -> dict[str, Any]:
        """Shut down the plugin and release its resources."""
        if self.plugin is None:
            return {"status": "already_stopped"}

        plugin = self.plugin
        self.plugin = None

        try:
            await asyncio.to_thread(plugin.shutdown)
        except Exception as exc:
            logger.exception("Plugin shutdown failed")
            raise RpcMethodError(
                -32001,
                "Plugin shutdown failed",
                data={"exception_type": type(exc).__name__},
            ) from exc

        return {"status": "success"}


async def open_stdio_streams(
    max_message_bytes: int,
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Connect asyncio streams to worker stdin and stdout."""
    loop = asyncio.get_running_loop()

    protocol_output = sys.stdout.buffer

    reader = asyncio.StreamReader(
        limit=max_message_bytes + 2,
    )
    reader_protocol = asyncio.StreamReaderProtocol(reader)

    await loop.connect_read_pipe(
        lambda: reader_protocol,
        sys.stdin.buffer,
    )

    writer_protocol = asyncio.streams.FlowControlMixin(loop=loop)

    transport, _ = await loop.connect_write_pipe(
        lambda: writer_protocol,
        protocol_output,
    )

    writer = asyncio.StreamWriter(
        transport,
        writer_protocol,
        reader,
        loop,
    )

    # Plugin print() calls must never corrupt the JSON-RPC stdout stream.
    sys.stdout = sys.stderr
    sys.__stdout__ = sys.stderr

    return reader, writer


async def serve_worker(
    plugin_dir: Path,
    data_dir: Path,
    max_message_bytes: int,
    cancellation_grace_seconds: float,
) -> None:
    """Run the worker until the host closes its connection."""
    reader, writer = await open_stdio_streams(max_message_bytes)

    runtime = PluginWorkerRuntime(plugin_dir, data_dir)

    peer = JsonRpcPeer(
        reader,
        writer,
        sender="plugin",
        max_message_bytes=max_message_bytes,
    )

    registry = ExecutionRegistry(
        cancellation_grace_seconds=cancellation_grace_seconds,
    )

    peer.register_method("plugin.initialize", runtime.initialize)
    registry.attach(peer, runtime.execute)

    async def shutdown_handler(params: dict[str, Any]) -> dict[str, Any]:
        if registry.active_execution_ids:
            raise RpcMethodError(
                -32001,
                "Cannot shut down while executions are active",
                retryable=True,
            )

        return await runtime.shutdown(params)

    peer.register_method("plugin.shutdown", shutdown_handler)

    peer.start()

    try:
        await peer.wait_closed()
    finally:
        if not registry.active_execution_ids:
            try:
                await runtime.shutdown({})
            except Exception:
                logger.exception("Final plugin cleanup failed")

        await peer.close()


def main() -> None:
    """Parse worker arguments and start the protocol server."""
    parser = argparse.ArgumentParser(description="Patchbay plugin worker")

    parser.add_argument("--plugin-dir", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--max-message-bytes",
        type=int,
        default=DEFAULT_MAX_MESSAGE_BYTES,
    )
    parser.add_argument(
        "--cancellation-grace-ms",
        type=int,
        default=1000,
    )

    args = parser.parse_args()

    if args.max_message_bytes < 1:
        parser.error("--max-message-bytes must be positive")

    if args.cancellation_grace_ms < 0:
        parser.error("--cancellation-grace-ms cannot be negative")

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        asyncio.run(
            serve_worker(
                plugin_dir=args.plugin_dir,
                data_dir=args.data_dir,
                max_message_bytes=args.max_message_bytes,
                cancellation_grace_seconds=(
                    args.cancellation_grace_ms / 1000
                ),
            )
        )
    except Exception:
        logger.exception("Worker process failed")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
