"""Execution tracking and cooperative cancellation for Patchbay."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from patchbay_protocol.errors import RpcMethodError

ExecutionHandler = Callable[
    [dict[str, Any], asyncio.Event],
    Awaitable[dict[str, Any]],
]


@dataclass(slots=True)
class _ExecutionRecord:
    """State associated with one active plugin execution."""

    execution_id: str
    task: asyncio.Task[dict[str, Any]]
    cancellation_event: asyncio.Event
    reason: str | None = None


class ExecutionRegistry:
    """Track active executions and coordinate cancellation."""

    def __init__(
        self,
        cancellation_grace_seconds: float = 1.0,
    ) -> None:
        if cancellation_grace_seconds < 0:
            raise ValueError("Cancellation grace period cannot be negative")

        self._grace = cancellation_grace_seconds
        self._active: dict[str, _ExecutionRecord] = {}
        self._lock = asyncio.Lock()
        self._handler: ExecutionHandler | None = None

    @property
    def active_execution_ids(self) -> tuple[str, ...]:
        """Return IDs of currently tracked executions."""
        return tuple(self._active)

    def attach(
        self,
        peer: Any,
        handler: ExecutionHandler,
    ) -> None:
        """Register execution and cancellation methods on an RPC peer."""
        if self._handler is not None:
            raise RuntimeError("Execution registry is already attached")

        self._handler = handler
        peer.register_method("plugin.execute", self._handle_execute)
        peer.register_method("plugin.cancel", self._handle_cancel)

    async def _handle_execute(
        self,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle an incoming plugin.execute request."""
        if self._handler is None:
            raise RuntimeError("Execution registry has no handler")

        return await self.execute(
            execution_id=params["execution_id"],
            params=params,
            timeout_ms=params["timeout_ms"],
        )

    async def _handle_cancel(
        self,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle an incoming plugin.cancel request."""
        return await self.cancel(params["execution_id"])

    async def execute(
        self,
        execution_id: str,
        params: dict[str, Any],
        timeout_ms: int,
    ) -> dict[str, Any]:
        """Run one execution while tracking its lifecycle."""
        if not execution_id:
            raise ValueError("Execution ID cannot be empty")

        if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
            raise ValueError("timeout_ms must be an integer")

        if timeout_ms < 1:
            raise ValueError("timeout_ms must be positive")

        if self._handler is None:
            raise RuntimeError("Attach an execution handler before use")

        cancellation_event = asyncio.Event()

        async with self._lock:
            if execution_id in self._active:
                raise RpcMethodError(
                    code=-32001,
                    message="Execution ID is already active",
                    retryable=False,
                )

            task = asyncio.create_task(
                self._handler(params, cancellation_event),
                name=f"patchbay-execution-{execution_id}",
            )

            record = _ExecutionRecord(
                execution_id=execution_id,
                task=task,
                cancellation_event=cancellation_event,
            )

            self._active[execution_id] = record

            task.add_done_callback(
                lambda _: asyncio.create_task(self._remove_record(record))
            )

        try:
            try:
                result = await asyncio.wait_for(
                    asyncio.shield(task),
                    timeout=timeout_ms / 1000,
                )
            except TimeoutError as exc:
                record.reason = "timeout"
                await self._request_cancellation(record)
                raise RpcMethodError(
                    code=-32003,
                    message="Execution timed out",
                    data={"execution_id": execution_id},
                    retryable=True,
                ) from exc
            except asyncio.CancelledError as exc:
                if record.reason == "cancelled":
                    raise self._cancellation_error(record) from exc

                if record.reason == "timeout":
                    raise self._timeout_error(record) from exc

                record.reason = "cancelled"
                await self._request_cancellation(record)
                raise

            if record.reason == "cancelled":
                raise self._cancellation_error(record)

            if record.reason == "timeout":
                raise self._timeout_error(record)

            if not isinstance(result, dict):
                raise RpcMethodError(
                    code=-32603,
                    message="Execution handler must return a dictionary",
                )

            return {
                "status": "success",
                "data": result,
            }

        finally:
            if task.done():
                await self._remove_record(record)

    async def cancel(self, execution_id: str) -> dict[str, Any]:
        """Request cancellation of one active execution."""
        async with self._lock:
            record = self._active.get(execution_id)

        if record is None:
            return {
                "status": "not_found",
                "execution_id": execution_id,
            }

        if record.reason is None:
            record.reason = "cancelled"

        stopped = await self._request_cancellation(record)

        return {
            "status": "accepted" if stopped else "termination_requested",
            "execution_id": execution_id,
        }

    async def _request_cancellation(
        self,
        record: _ExecutionRecord,
    ) -> bool:
        """Signal cooperative cancellation, then escalate to task cancellation."""
        record.cancellation_event.set()

        if record.task.done():
            return True

        try:
            await asyncio.wait_for(
                asyncio.shield(record.task),
                timeout=self._grace,
            )
            return True
        except TimeoutError:
            record.task.cancel()
            return False
        except asyncio.CancelledError:
            return True
        except Exception:
            return True

    async def _remove_record(
        self,
        record: _ExecutionRecord,
    ) -> None:
        """Remove a completed execution without affecting a replacement."""
        async with self._lock:
            if self._active.get(record.execution_id) is record:
                self._active.pop(record.execution_id, None)

    @staticmethod
    def _cancellation_error(
        record: _ExecutionRecord,
    ) -> RpcMethodError:
        """Build the protocol error for a cancelled execution."""
        return RpcMethodError(
            code=-32007,
            message="Execution cancelled",
            data={"execution_id": record.execution_id},
            retryable=False,
        )

    @staticmethod
    def _timeout_error(
        record: _ExecutionRecord,
    ) -> RpcMethodError:
        """Build the protocol error for a timed-out execution."""
        return RpcMethodError(
            code=-32003,
            message="Execution timed out",
            data={"execution_id": record.execution_id},
            retryable=True,
        )
