"""Tests for Patchbay execution tracking and cancellation."""

import asyncio
import socket

import pytest
from patchbay_protocol import (
    ExecutionRegistry,
    JsonRpcPeer,
    RpcRemoteError,
)


async def create_peers() -> tuple[JsonRpcPeer, JsonRpcPeer]:
    """Create connected host and plugin RPC peers."""
    left_socket, right_socket = socket.socketpair()

    left_reader, left_writer = await asyncio.open_connection(sock=left_socket)
    right_reader, right_writer = await asyncio.open_connection(sock=right_socket)

    host = JsonRpcPeer(left_reader, left_writer, sender="host")
    plugin = JsonRpcPeer(right_reader, right_writer, sender="plugin")

    host.start()
    plugin.start()

    return host, plugin


def test_execution_completes_successfully() -> None:
    async def scenario() -> None:
        host, plugin = await create_peers()
        registry = ExecutionRegistry()

        async def handler(params: dict, cancellation: asyncio.Event) -> dict:
            return {"message": params["input"]["message"]}

        registry.attach(plugin, handler)

        try:
            result = await host.request(
                "plugin.execute",
                {
                    "execution_id": "execution-001",
                    "input": {"message": "Hello Patchbay"},
                    "timeout_ms": 30000,
                },
                timeout=2,
            )

            assert result == {
                "status": "success",
                "data": {"message": "Hello Patchbay"},
            }
            assert registry.active_execution_ids == ()
        finally:
            await host.close()
            await plugin.close()

    asyncio.run(scenario())


def test_execution_can_be_cancelled() -> None:
    async def scenario() -> None:
        host, plugin = await create_peers()
        registry = ExecutionRegistry(cancellation_grace_seconds=0.5)
        started = asyncio.Event()

        async def handler(params: dict, cancellation: asyncio.Event) -> dict:
            started.set()
            await cancellation.wait()
            return {"message": "Cancellation acknowledged"}

        registry.attach(plugin, handler)

        try:
            execution = asyncio.create_task(
                host.request(
                    "plugin.execute",
                    {
                        "execution_id": "execution-002",
                        "input": {},
                        "timeout_ms": 30000,
                    },
                    timeout=3,
                )
            )

            await asyncio.wait_for(started.wait(), timeout=2)

            assert "execution-002" in registry.active_execution_ids

            acknowledgement = await host.request(
                "plugin.cancel",
                {"execution_id": "execution-002"},
                timeout=2,
            )

            assert acknowledgement["status"] == "accepted"

            with pytest.raises(RpcRemoteError) as error:
                await execution

            assert error.value.code == -32007
            assert registry.active_execution_ids == ()
        finally:
            await host.close()
            await plugin.close()

    asyncio.run(scenario())


def test_execution_timeout_is_enforced() -> None:
    async def scenario() -> None:
        host, plugin = await create_peers()
        registry = ExecutionRegistry(cancellation_grace_seconds=0.01)

        async def handler(params: dict, cancellation: asyncio.Event) -> dict:
            await asyncio.sleep(5)
            return {"message": "This should not complete"}

        registry.attach(plugin, handler)

        try:
            with pytest.raises(RpcRemoteError) as error:
                await host.request(
                    "plugin.execute",
                    {
                        "execution_id": "execution-003",
                        "input": {},
                        "timeout_ms": 50,
                    },
                    timeout=2,
                )

            assert error.value.code == -32003
            assert error.value.retryable is True
        finally:
            await host.close()
            await plugin.close()

    asyncio.run(scenario())


def test_cancelling_unknown_execution() -> None:
    async def scenario() -> None:
        host, plugin = await create_peers()
        registry = ExecutionRegistry()

        async def handler(params: dict, cancellation: asyncio.Event) -> dict:
            return {"ok": True}

        registry.attach(plugin, handler)

        try:
            result = await host.request(
                "plugin.cancel",
                {"execution_id": "does-not-exist"},
                timeout=2,
            )

            assert result == {
                "status": "not_found",
                "execution_id": "does-not-exist",
            }
        finally:
            await host.close()
            await plugin.close()

    asyncio.run(scenario())
