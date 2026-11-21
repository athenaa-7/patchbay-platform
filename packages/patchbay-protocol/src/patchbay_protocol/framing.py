"""Newline-delimited JSON transport helpers."""

from typing import Any, BinaryIO

from patchbay_protocol.codec import decode_message, encode_message
from patchbay_protocol.errors import ProtocolFramingError

DEFAULT_MAX_MESSAGE_BYTES = 1_048_576


def read_message(
    stream: BinaryIO,
    *,
    max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES,
) -> dict[str, Any] | None:
    """Read one NDJSON message from a binary stream.

    Returns None when the stream reaches EOF before another frame.
    """
    if max_message_bytes < 1:
        raise ValueError("Maximum message size must be positive")

    line = stream.readline(max_message_bytes + 2)

    if not line:
        return None

    if not line.endswith(b"\n"):
        oversized = len(line) > max_message_bytes

        # Drain the remainder of an oversized frame to preserve framing.
        while oversized and line and not line.endswith(b"\n"):
            line = stream.readline(max_message_bytes + 2)

        if oversized:
            raise ProtocolFramingError(
                f"NDJSON message exceeds {max_message_bytes} bytes"
            )

        raise ProtocolFramingError("NDJSON message is missing its newline")

    payload = line[:-1]

    if payload.endswith(b"\r"):
        payload = payload[:-1]

    if not payload:
        raise ProtocolFramingError("Empty NDJSON frames are not allowed")

    if len(payload) > max_message_bytes:
        raise ProtocolFramingError(
            f"NDJSON message exceeds {max_message_bytes} bytes"
        )

    return decode_message(payload)


def write_message(
    stream: BinaryIO,
    message: Any,
    *,
    max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES,
) -> None:
    """Write one validated NDJSON message to a binary stream."""
    if max_message_bytes < 1:
        raise ValueError("Maximum message size must be positive")

    payload = encode_message(message)

    if len(payload) > max_message_bytes:
        raise ProtocolFramingError(
            f"NDJSON message exceeds {max_message_bytes} bytes"
        )

    frame = memoryview(payload + b"\n")

    while frame:
        written = stream.write(frame)

        if written is None or written <= 0:
            raise ProtocolFramingError("Could not write complete NDJSON frame")

        frame = frame[written:]

    stream.flush()
