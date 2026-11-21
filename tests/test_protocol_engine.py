"""Tests for the Patchbay JSON-RPC engine."""

from io import BytesIO

import pytest
from patchbay_protocol import (
    JsonRpcErrorResponse,
    JsonRpcNotification,
    JsonRpcRequest,
    JsonRpcSuccessResponse,
    ProtocolDecodeError,
    ProtocolFramingError,
    ProtocolSerializationError,
    ProtocolValidationError,
    RequestIdGenerator,
    decode_message,
    encode_message,
    read_message,
    write_message,
)


def test_request_round_trip() -> None:
    request = JsonRpcRequest(
        id="host:1",
        method="plugin.execute",
        params={
            "execution_id": "execution-001",
            "input": {"message": "hello"},
            "timeout_ms": 30000,
        },
    )

    decoded = decode_message(encode_message(request))

    assert decoded["id"] == "host:1"
    assert decoded["method"] == "plugin.execute"


def test_notification_round_trip() -> None:
    notification = JsonRpcNotification(
        method="plugin.progress",
        params={
            "execution_id": "execution-001",
            "progress": 50,
        },
    )

    decoded = decode_message(encode_message(notification))

    assert decoded["method"] == "plugin.progress"
    assert "id" not in decoded


def test_success_response_round_trip() -> None:
    response = JsonRpcSuccessResponse(
        id="host:1",
        result={"status": "success", "data": {"ok": True}},
    )

    decoded = decode_message(encode_message(response))

    assert decoded["result"]["data"]["ok"] is True


def test_error_response_round_trip() -> None:
    response = JsonRpcErrorResponse(
        id="host:1",
        code=-32001,
        message="Execution failed",
        retryable=False,
    )

    decoded = decode_message(encode_message(response))

    assert decoded["error"]["code"] == -32001
    assert decoded["error"]["data"]["retryable"] is False


def test_invalid_message_is_rejected() -> None:
    with pytest.raises(ProtocolValidationError):
        encode_message({
            "jsonrpc": "1.0",
            "id": "host:1",
            "method": "plugin.execute",
        })


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(ProtocolDecodeError):
        decode_message(b'{"jsonrpc":')


def test_duplicate_json_keys_are_rejected() -> None:
    raw = b'{"jsonrpc":"2.0","jsonrpc":"2.0"}'

    with pytest.raises(ProtocolDecodeError):
        decode_message(raw, validate=False)


def test_non_object_json_is_rejected() -> None:
    with pytest.raises(ProtocolDecodeError):
        decode_message(b'["not", "an", "object"]')


def test_invalid_unicode_is_rejected() -> None:
    with pytest.raises(ProtocolDecodeError):
        decode_message(b"\xff")


def test_non_json_nan_is_rejected() -> None:
    with pytest.raises(ProtocolDecodeError):
        decode_message(
            '{"jsonrpc":"2.0","id":"host:1","result":{"value":NaN}}',
            validate=False,
        )


def test_request_id_generator() -> None:
    generator = RequestIdGenerator("host")

    assert generator.next_id() == "host:1"
    assert generator.next_id() == "host:2"


def test_plugin_request_id_generator() -> None:
    generator = RequestIdGenerator("plugin")

    assert generator.next_id() == "plugin:1"


def test_invalid_request_id_sender() -> None:
    with pytest.raises(ValueError):
        RequestIdGenerator("invalid")  # type: ignore[arg-type]


def test_request_rejects_invalid_id() -> None:
    with pytest.raises(ValueError):
        JsonRpcRequest(id="invalid", method="plugin.execute")


def test_reader_reads_one_frame() -> None:
    stream = BytesIO(
        b'{"jsonrpc":"2.0","id":"host:1","result":{"status":"success"}}\n'
    )

    message = read_message(stream)

    assert message is not None
    assert message["id"] == "host:1"


def test_reader_handles_multiple_frames() -> None:
    first = JsonRpcNotification("plugin.progress", {
        "execution_id": "execution-001",
        "progress": 20,
    })
    second = JsonRpcNotification("plugin.progress", {
        "execution_id": "execution-001",
        "progress": 60,
    })

    stream = BytesIO(
        encode_message(first) + b"\n" + encode_message(second) + b"\n"
    )

    assert read_message(stream)["params"]["progress"] == 20
    assert read_message(stream)["params"]["progress"] == 60
    assert read_message(stream) is None


def test_reader_rejects_missing_newline() -> None:
    stream = BytesIO(b'{"jsonrpc":"2.0"}')

    with pytest.raises(ProtocolFramingError):
        read_message(stream)


def test_reader_rejects_empty_frame() -> None:
    with pytest.raises(ProtocolFramingError):
        read_message(BytesIO(b"\n"))


def test_reader_rejects_oversized_frame() -> None:
    stream = BytesIO(b"x" * 20 + b"\n")

    with pytest.raises(ProtocolFramingError):
        read_message(stream, max_message_bytes=10)


def test_writer_adds_newline() -> None:
    stream = BytesIO()
    notification = JsonRpcNotification(
        "plugin.progress",
        {"execution_id": "execution-001", "progress": 10},
    )

    write_message(stream, notification)

    assert stream.getvalue().endswith(b"\n")


def test_writer_rejects_oversized_message() -> None:
    stream = BytesIO()
    notification = JsonRpcNotification(
        "plugin.progress",
        {
            "execution_id": "execution-001",
            "progress": 10,
            "message": "x" * 100,
        },
    )

    with pytest.raises(ProtocolFramingError):
        write_message(stream, notification, max_message_bytes=20)


def test_serialization_rejects_unsupported_object() -> None:
    with pytest.raises(ProtocolSerializationError):
        encode_message(object())
