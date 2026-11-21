"""Public API for the Patchbay protocol package."""

from patchbay_protocol.codec import decode_message, encode_message
from patchbay_protocol.errors import (
    ProtocolDecodeError,
    ProtocolError,
    ProtocolFramingError,
    ProtocolSerializationError,
    ProtocolValidationError,
    RpcMethodError,
    RpcRemoteError,
)
from patchbay_protocol.execution import ExecutionRegistry
from patchbay_protocol.framing import (
    DEFAULT_MAX_MESSAGE_BYTES,
    read_message,
    write_message,
)
from patchbay_protocol.messages import (
    JsonRpcErrorResponse,
    JsonRpcNotification,
    JsonRpcRequest,
    JsonRpcSuccessResponse,
    RequestIdGenerator,
)
from patchbay_protocol.rpc import JsonRpcPeer
from patchbay_protocol.validation import validate_message, validate_params

__all__ = [
    "DEFAULT_MAX_MESSAGE_BYTES",
    "ExecutionRegistry",
    "JsonRpcErrorResponse",
    "JsonRpcNotification",
    "JsonRpcPeer",
    "JsonRpcRequest",
    "JsonRpcSuccessResponse",
    "ProtocolDecodeError",
    "ProtocolError",
    "ProtocolFramingError",
    "ProtocolSerializationError",
    "ProtocolValidationError",
    "RequestIdGenerator",
    "RpcMethodError",
    "RpcRemoteError",
    "decode_message",
    "encode_message",
    "read_message",
    "validate_message",
    "validate_params",
    "write_message",
]
