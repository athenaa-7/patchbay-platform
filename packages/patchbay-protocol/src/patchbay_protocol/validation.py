"""JSON Schema validation for Patchbay protocol messages."""

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from patchbay_protocol.errors import ProtocolValidationError

_METHOD_SCHEMAS = {
    "plugin.initialize": "methods/plugin-initialize.params.schema.json",
    "plugin.execute": "methods/plugin-execute.params.schema.json",
    "plugin.cancel": "methods/plugin-cancel.params.schema.json",
    "plugin.progress": "methods/plugin-progress.params.schema.json",
    "plugin.output": "methods/plugin-output.params.schema.json",
    "host.capability.invoke": (
        "methods/host-capability-invoke.params.schema.json"
    ),
}


@lru_cache(maxsize=32)
def _load_validator(schema_name: str) -> Draft202012Validator:
    """Load and cache a protocol JSON Schema validator."""
    resource = files("patchbay_protocol").joinpath(
        "schemas", "v1", *schema_name.split("/")
    )

    try:
        schema = json.loads(resource.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, ValueError, ValidationError) as exc:
        raise ProtocolValidationError(
            f"Could not load protocol schema {schema_name}: {exc}"
        ) from exc

    return Draft202012Validator(schema)


def validate_params(method: str, params: Any) -> None:
    """Validate parameters for a known protocol method."""
    schema_name = _METHOD_SCHEMAS.get(method)

    if method == "plugin.event" and isinstance(params, dict):
        if params.get("event_type") == "token_usage":
            schema_name = "methods/plugin-token-usage.params.schema.json"

    if schema_name is None:
        return

    try:
        _load_validator(schema_name).validate(params)
    except ValidationError as exc:
        raise ProtocolValidationError(
            f"Invalid parameters for {method}: {exc.message}"
        ) from exc


def validate_message(message: Any) -> None:
    """Validate a JSON-RPC envelope and known method parameters."""
    try:
        _load_validator("message-envelope.schema.json").validate(message)
    except ValidationError as exc:
        raise ProtocolValidationError(
            f"Invalid JSON-RPC message: {exc.message}"
        ) from exc

    if "method" in message:
        validate_params(message["method"], message.get("params", {}))
