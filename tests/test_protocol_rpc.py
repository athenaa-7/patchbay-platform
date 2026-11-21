"""Tests for bidirectional Patchbay RPC communication."""

import asyncio
import socket

import pytest
from patchbay_protocol import JsonRpcPeer, RpcRemoteError


async def create_peers() -> tuple[JsonRpcPeer, JsonRpcPeer]:
    """Create two connected RPC peers using a local socket pair."""
    left_socket, right_socket = socket.socketpair()

    left_reader, left_writer = await asyncio.open_connection(
        sock=left_socket
    )
    right_reader, right_writer = await asyncio.open_connection(
        sock=right_socket
    )

    host = JsonRpcPeer(
        left_reader,
        left_writer,
        sender="host",
    )
    plugin = JsonRpcPeer(
        right_reader,
        right_writer,
        sender="plugin",
    )

    host.start()
    plugin.start()

    return host, plugin


def test_rpc_request_response() -> None:
    async def scenario() -> None:
        host, plugin = await create_peers()

        plugin.register_method(
            "plugin.echo",
            lambda params: {"echo": params["message"]},
        )

        try:
            result = await host.request(
                "plugin.echo",
                {"message": "Hello Patchbay"},
                timeout=2,
            )

            assert result == {"echo": "Hello Patchbay"}
        finally:
            await host.close()
            await plugin.close()

    asyncio.run(scenario())


def test_bidirectional_rpc() -> None:
    async def scenario() -> None:
        host, plugin = await create_peers()

        async def execute(params: dict) -> dict:
            capability_result = await plugin.request(
                "host.capability.invoke",
                {
                    "execution_id": params["execution_id"],
                    "capability": "model.inference",
                    "operation": "generate",
                    "input": {"prompt": "Hello"},
                },
                timeout=2,
            )

            return {"output": capability_result["text"]}

        host.register_method(
            "host.capability.invoke",
            lambda params: {"text": "Generated response"},
        )

        plugin.register_method("plugin.execute", execute)

        try:
            result = await host.request(
                "plugin.execute",
                {
                    "execution_id": "execution-001",
                    "input": {"message": "Hello"},
                    "timeout_ms": 30000,
                },
                timeout=3,
            )

            assert result["output"] == "Generated response"
        finally:
            await host.close()
            await plugin.close()

    asyncio.run(scenario())


def test_rpc_notification() -> None:
    async def scenario() -> None:
        host, plugin = await create_peers()
        received = asyncio.Event()

        def handle_progress(params: dict) -> None:
            assert params["progress"] == 50
            received.set()

        plugin.register_notification(
            "plugin.progress",
            handle_progress,
        )

        try:
            await host.notify(
                "plugin.progress",
                {
                    "execution_id": "execution-001",
                    "progress": 50,
                },
            )

            await asyncio.wait_for(received.wait(), timeout=2)
            assert received.is_set()
        finally:
            await host.close()
            await plugin.close()

    asyncio.run(scenario())


def test_unknown_method_returns_remote_error() -> None:
    async def scenario() -> None:
        host, plugin = await create_peers()

        try:
            with pytest.raises(RpcRemoteError) as error:
                await host.request(
                    "plugin.unknown",
                    {},
                    timeout=2,
                )

            assert error.value.code == -32601
            assert error.value.retryable is False
        finally:
            await host.close()
            await plugin.close()

    asyncio.run(scenario())


def test_rpc_request_timeout() -> None:
    async def scenario() -> None:
        host, plugin = await create_peers()

        async def slow_handler(params: dict) -> dict:
            await asyncio.sleep(1)
            return {"status": "completed"}

        plugin.register_method("plugin.slow", slow_handler)

        try:
            with pytest.raises(TimeoutError):
                await host.request(
                    "plugin.slow",
                    {},
                    timeout=0.05,
                )
        finally:
            await host.close()
            await plugin.close()

    asyncio.run(scenario())
