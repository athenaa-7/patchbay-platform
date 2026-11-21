"""JSON encoding and decoding for Patchbay protocol messages."""

import json
from collections.abc import Mapping
from typing import Any

from patchbay_protocol.errors import (
    ProtocolDecodeError,
    ProtocolSerializationError,
)
from patchbay_protocol.validation import validate_message


def _reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Reject duplicate JSON object keys."""
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value

    return result


def _reject_nonstandard_constant(value: str) -> None:
    """Reject NaN and Infinity, which are not valid JSON values."""
    raise ValueError(f"Non-standard JSON constant: {value}")


def encode_message(
    message: Mapping[str, Any] | Any,
    *,
    validate: bool = True,
) -> bytes:
    """Serialize a protocol message to compact UTF-8 JSON bytes."""
    if hasattr(message, "to_dict"):
        payload = message.to_dict()
    elif isinstance(message, Mapping):
        payload = dict(message)
    else:
        raise ProtocolSerializationError(
            "Message must be a mapping or provide to_dict()"
        )

    if validate:
        validate_message(payload)

    try:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        return encoded.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ProtocolSerializationError(
            f"Could not serialize protocol message: {exc}"
        ) from exc


def decode_message(
    raw: bytes | str,
    *,
    validate: bool = True,
) -> dict[str, Any]:
    """Decode UTF-8 JSON and optionally validate its protocol envelope."""
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        if not isinstance(raw, str):
            raise TypeError("Input must be bytes or a string")

        payload = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
        raise ProtocolDecodeError(
            f"Could not decode protocol message: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise ProtocolDecodeError("Protocol message must be a JSON object")

    if validate:
        validate_message(payload)

    return payload
