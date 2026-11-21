"""Errors raised by the Patchbay protocol implementation."""

from typing import Any


class ProtocolError(Exception):
    """Base exception for protocol failures."""


class ProtocolDecodeError(ProtocolError):
    """Raised when a message cannot be decoded."""


class ProtocolSerializationError(ProtocolError):
    """Raised when a message cannot be serialized."""


class ProtocolValidationError(ProtocolError):
    """Raised when a message violates the protocol schema."""


class ProtocolFramingError(ProtocolError):
    """Raised when an NDJSON frame is invalid."""


class RpcMethodError(ProtocolError):
    """An application-level error raised by an RPC method."""

    def __init__(
        self,
        code: int,
        message: str,
        data: dict[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data or {}
        self.retryable = retryable


class RpcRemoteError(ProtocolError):
    """Represents an error returned by a remote RPC peer."""

    def __init__(
        self,
        code: int,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"RPC error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data or {}
        self.retryable = bool(self.data.get("retryable", False))
