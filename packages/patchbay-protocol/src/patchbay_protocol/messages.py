"""Typed JSON-RPC message models for Patchbay."""

import re
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Literal

_REQUEST_ID_PATTERN = re.compile(r"^(host|plugin):.+$")


def validate_request_id(request_id: str) -> None:
    """Validate a Patchbay request identifier."""
    if not isinstance(request_id, str):
        raise ValueError("Request ID must be a string")

    if not _REQUEST_ID_PATTERN.fullmatch(request_id):
        raise ValueError("Request ID must start with 'host:' or 'plugin:'")


@dataclass(frozen=True, slots=True)
class JsonRpcRequest:
    """JSON-RPC request requiring a response."""

    id: str
    method: str
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_request_id(self.id)

        if not self.method:
            raise ValueError("Method cannot be empty")

        if not isinstance(self.params, dict):
            raise ValueError("Request params must be an object")

    def to_dict(self) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": self.id,
            "method": self.method,
            "params": self.params,
        }


@dataclass(frozen=True, slots=True)
class JsonRpcNotification:
    """JSON-RPC notification that does not require a response."""

    method: str
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.method:
            raise ValueError("Method cannot be empty")

        if not isinstance(self.params, dict):
            raise ValueError("Notification params must be an object")

    def to_dict(self) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "method": self.method,
            "params": self.params,
        }


@dataclass(frozen=True, slots=True)
class JsonRpcSuccessResponse:
    """Successful JSON-RPC response."""

    id: str
    result: dict[str, Any]

    def __post_init__(self) -> None:
        validate_request_id(self.id)

        if not isinstance(self.result, dict):
            raise ValueError("Response result must be an object")

    def to_dict(self) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": self.id,
            "result": self.result,
        }


@dataclass(frozen=True, slots=True)
class JsonRpcErrorResponse:
    """Failed JSON-RPC response using Patchbay error conventions."""

    id: str
    code: int
    message: str
    retryable: bool = False
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_request_id(self.id)

        if not self.message:
            raise ValueError("Error message cannot be empty")

        if not isinstance(self.code, int):
            raise ValueError("Error code must be an integer")

        if not isinstance(self.data, dict):
            raise ValueError("Error data must be an object")

    def to_dict(self) -> dict[str, Any]:
        error_data = {
            **self.data,
            "retryable": self.retryable,
        }

        return {
            "jsonrpc": "2.0",
            "id": self.id,
            "error": {
                "code": self.code,
                "message": self.message,
                "data": error_data,
            },
        }


class RequestIdGenerator:
    """Generate unique request IDs for one side of a worker session."""

    def __init__(self, sender: Literal["host", "plugin"]) -> None:
        if sender not in {"host", "plugin"}:
            raise ValueError("Sender must be 'host' or 'plugin'")

        self._sender = sender
        self._counter = 0
        self._lock = Lock()

    def next_id(self) -> str:
        """Generate the next request ID."""
        with self._lock:
            self._counter += 1
            return f"{self._sender}:{self._counter}"
