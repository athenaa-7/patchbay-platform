"""Bidirectional asynchronous JSON-RPC communication."""

import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Any, Literal

from patchbay_protocol.codec import decode_message, encode_message
from patchbay_protocol.errors import (
    ProtocolError,
    ProtocolFramingError,
    RpcMethodError,
    RpcRemoteError,
)
from patchbay_protocol.framing import DEFAULT_MAX_MESSAGE_BYTES
from patchbay_protocol.messages import RequestIdGenerator

logger = logging.getLogger(__name__)

RpcHandler = Callable[[dict[str, Any]], Any]


class JsonRpcPeer:
    """Bidirectional JSON-RPC endpoint over an asyncio byte stream."""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        sender: Literal["host", "plugin"],
        max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES,
    ) -> None:
        if max_message_bytes < 1:
            raise ValueError("Maximum message size must be positive")

        self._reader = reader
        self._writer = writer
        self._ids = RequestIdGenerator(sender)
        self._max_message_bytes = max_message_bytes

        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._methods: dict[str, RpcHandler] = {}
        self._notifications: dict[str, RpcHandler] = {}

        self._write_lock = asyncio.Lock()
        self._reader_task: asyncio.Task[None] | None = None
        self._dispatch_tasks: set[asyncio.Task[Any]] = set()

        self._closed = False
        self._failure: Exception | None = None

    @property
    def is_closed(self) -> bool:
        """Whether the connection has closed."""
        return self._closed

    def start(self) -> None:
        """Start the background message reader."""
        if self._closed:
            raise ProtocolError("Cannot start a closed RPC peer")

        if self._reader_task is not None:
            raise ProtocolError("RPC peer has already been started")

        self._reader_task = asyncio.create_task(
            self._read_loop(),
            name="patchbay-rpc-reader",
        )

    def register_method(self, method: str, handler: RpcHandler) -> None:
        """Register an incoming request handler."""
        if not method:
            raise ValueError("Method cannot be empty")

        if method in self._methods:
            raise ValueError(f"Method already registered: {method}")

        self._methods[method] = handler

    def register_notification(
        self,
        method: str,
        handler: RpcHandler,
    ) -> None:
        """Register an incoming notification handler."""
        if not method:
            raise ValueError("Method cannot be empty")

        if method in self._notifications:
            raise ValueError(f"Notification already registered: {method}")

        self._notifications[method] = handler

    async def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Send a request and await its correlated response."""
        self._ensure_started()

        if not method:
            raise ValueError("Method cannot be empty")

        if timeout is not None and timeout <= 0:
            raise ValueError("Timeout must be positive")

        request_id = self._ids.next_id()
        future: asyncio.Future[dict[str, Any]] = (
            asyncio.get_running_loop().create_future()
        )

        self._pending[request_id] = future

        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }

        try:
            await self._send_message(message)

            if timeout is None:
                return await future

            return await asyncio.wait_for(
                asyncio.shield(future),
                timeout=timeout,
            )
        except TimeoutError as exc:
            raise TimeoutError(
                f"RPC request timed out: {method}"
            ) from exc
        finally:
            self._pending.pop(request_id, None)

            if not future.done():
                future.cancel()

    async def notify(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Send a notification without expecting a response."""
        self._ensure_started()

        await self._send_message({
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        })

    async def _send_message(self, message: dict[str, Any]) -> None:
        """Serialize and write one NDJSON message."""
        payload = encode_message(message)

        if len(payload) > self._max_message_bytes:
            raise ProtocolFramingError(
                f"Message exceeds {self._max_message_bytes} bytes"
            )

        async with self._write_lock:
            self._ensure_started()

            self._writer.write(payload + b"\n")
            await self._writer.drain()

    async def _read_loop(self) -> None:
        """Continuously read and dispatch incoming messages."""
        try:
            while not self._closed:
                try:
                    line = await self._reader.readline()
                except (ValueError, asyncio.LimitOverrunError) as exc:
                    raise ProtocolFramingError(
                        "Incoming NDJSON frame exceeded the stream limit"
                    ) from exc

                if not line:
                    raise ProtocolError("RPC peer closed the stream")

                if not line.endswith(b"\n"):
                    raise ProtocolFramingError(
                        "Incoming NDJSON frame is missing its newline"
                    )

                payload = line[:-1]

                if payload.endswith(b"\r"):
                    payload = payload[:-1]

                if not payload:
                    raise ProtocolFramingError(
                        "Empty NDJSON frames are not allowed"
                    )

                if len(payload) > self._max_message_bytes:
                    raise ProtocolFramingError(
                        "Incoming message exceeds configured size limit"
                    )

                message = decode_message(payload)
                self._dispatch_message(message)

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._fail(exc)

    def _dispatch_message(self, message: dict[str, Any]) -> None:
        """Classify an incoming JSON-RPC message."""
        if "method" in message:
            if "id" in message:
                self._spawn(self._handle_request(message))
            else:
                self._spawn(self._handle_notification(message))
            return

        if "id" in message:
            self._handle_response(message)
            return

        raise ProtocolError("Unrecognized JSON-RPC message")

    def _spawn(self, coroutine: Any) -> None:
        """Run a handler without blocking the reader loop."""
        task = asyncio.create_task(coroutine)
        self._dispatch_tasks.add(task)
        task.add_done_callback(self._task_finished)

    def _task_finished(self, task: asyncio.Task[Any]) -> None:
        """Collect completed handler tasks and unexpected exceptions."""
        self._dispatch_tasks.discard(task)

        if task.cancelled():
            return

        exc = task.exception()
        if exc is not None:
            logger.error(
                "Unexpected RPC handler failure",
                exc_info=(type(exc), exc, exc.__traceback__),
            )

    async def _handle_request(self, message: dict[str, Any]) -> None:
        """Execute an incoming request and send its response."""
        request_id = message["id"]
        method = message["method"]
        params = message.get("params", {})

        handler = self._methods.get(method)

        if handler is None:
            await self._send_error(
                request_id,
                code=-32601,
                message="Method not found",
            )
            return

        try:
            result = handler(params)

            if inspect.isawaitable(result):
                result = await result

            if not isinstance(result, dict):
                raise TypeError("RPC handlers must return a dictionary")

            await self._send_message({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            })

        except RpcMethodError as exc:
            await self._send_error(
                request_id,
                code=exc.code,
                message=exc.message,
                retryable=exc.retryable,
                data=exc.data,
            )
        except Exception:
            logger.exception("RPC handler failed: %s", method)

            await self._send_error(
                request_id,
                code=-32603,
                message="Internal error",
            )

    async def _handle_notification(
        self,
        message: dict[str, Any],
    ) -> None:
        """Execute an incoming notification handler."""
        method = message["method"]
        handler = self._notifications.get(method)

        if handler is None:
            logger.debug("Ignoring unhandled notification: %s", method)
            return

        try:
            result = handler(message.get("params", {}))

            if inspect.isawaitable(result):
                await result

        except Exception:
            logger.exception("Notification handler failed: %s", method)

    def _handle_response(self, message: dict[str, Any]) -> None:
        """Resolve a pending request using its response ID."""
        request_id = message["id"]
        future = self._pending.pop(request_id, None)

        if future is None:
            logger.warning("Received unmatched RPC response: %s", request_id)
            return

        if future.done():
            return

        if "error" in message:
            error = message["error"]
            future.set_exception(
                RpcRemoteError(
                    code=error["code"],
                    message=error["message"],
                    data=error.get("data", {}),
                )
            )
        else:
            future.set_result(message["result"])

    async def _send_error(
        self,
        request_id: str,
        code: int,
        message: str,
        retryable: bool = False,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Send a structured JSON-RPC error response."""
        error_data = {**(data or {}), "retryable": retryable}

        await self._send_message({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
                "data": error_data,
            },
        })

    def _ensure_started(self) -> None:
        """Ensure the RPC connection is available."""
        if self._closed:
            raise ProtocolError("RPC peer is closed")

        if self._reader_task is None:
            raise ProtocolError("Call start() before using the RPC peer")

    def _fail(self, exc: Exception) -> None:
        """Fail the connection and release pending requests."""
        if self._closed:
            return

        self._closed = True
        self._failure = exc

        for future in self._pending.values():
            if not future.done():
                future.set_exception(
                    ProtocolError(f"RPC connection failed: {exc}")
                )

        self._pending.clear()

    async def close(self) -> None:
        """Close the connection and cancel background tasks."""
        self._fail(ProtocolError("RPC peer closed locally"))

        current = asyncio.current_task()

        if self._reader_task is not None:
            if self._reader_task is not current:
                self._reader_task.cancel()
                await asyncio.gather(
                    self._reader_task,
                    return_exceptions=True,
                )

        tasks = [
            task for task in self._dispatch_tasks
            if task is not current
        ]

        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        if not self._writer.is_closing():
            self._writer.close()

        try:
            await self._writer.wait_closed()
        except (ConnectionError, OSError):
            pass
