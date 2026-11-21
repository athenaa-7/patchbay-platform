"""Tests for Patchbay Universal Plugin Protocol schemas."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = (
    ROOT
    / "packages"
    / "patchbay-protocol"
    / "src"
    / "patchbay_protocol"
    / "schemas"
    / "v1"
)


def load_validator(schema_name: str) -> Draft202012Validator:
    """Load a protocol schema and return its validator."""
    schema_path = SCHEMA_ROOT / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


SCHEMA_FILES = sorted(SCHEMA_ROOT.rglob("*.schema.json"))


@pytest.mark.parametrize(
    "schema_path",
    SCHEMA_FILES,
    ids=lambda path: path.name,
)
def test_schema_is_valid_json_schema(schema_path: Path) -> None:
    """Every protocol schema must follow JSON Schema Draft 2020-12."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_valid_initialization_parameters() -> None:
    validator = load_validator("methods/plugin-initialize.params.schema.json")

    payload = {
        "protocol_version": "1.0",
        "host_api_version": "1.0",
        "plugin_id": "org.patchbay.examples.hello-world",
        "configuration": {},
        "granted_capabilities": ["model.inference"],
    }

    validator.validate(payload)


def test_initialization_rejects_missing_fields() -> None:
    validator = load_validator("methods/plugin-initialize.params.schema.json")

    payload = {
        "protocol_version": "1.0",
        "plugin_id": "org.patchbay.examples.hello-world",
        "configuration": {},
        "granted_capabilities": [],
    }

    with pytest.raises(ValidationError):
        validator.validate(payload)


def test_valid_execution_parameters() -> None:
    validator = load_validator("methods/plugin-execute.params.schema.json")

    payload = {
        "execution_id": "execution-001",
        "input": {"prompt": "Hello Patchbay"},
        "timeout_ms": 30000,
    }

    validator.validate(payload)


def test_execution_rejects_invalid_timeout() -> None:
    validator = load_validator("methods/plugin-execute.params.schema.json")

    payload = {
        "execution_id": "execution-001",
        "input": {},
        "timeout_ms": 0,
    }

    with pytest.raises(ValidationError):
        validator.validate(payload)


def test_valid_progress_notification() -> None:
    validator = load_validator("methods/plugin-progress.params.schema.json")

    payload = {
        "execution_id": "execution-001",
        "progress": 50,
        "message": "Processing",
    }

    validator.validate(payload)


def test_progress_rejects_out_of_range_value() -> None:
    validator = load_validator("methods/plugin-progress.params.schema.json")

    payload = {
        "execution_id": "execution-001",
        "progress": 120,
    }

    with pytest.raises(ValidationError):
        validator.validate(payload)


def test_valid_streaming_output() -> None:
    validator = load_validator("methods/plugin-output.params.schema.json")

    payload = {
        "execution_id": "execution-001",
        "sequence": 1,
        "content_type": "text/plain",
        "chunk": "Hello from Patchbay",
    }

    validator.validate(payload)


def test_streaming_output_rejects_invalid_sequence() -> None:
    validator = load_validator("methods/plugin-output.params.schema.json")

    payload = {
        "execution_id": "execution-001",
        "sequence": 0,
        "content_type": "text/plain",
        "chunk": "Hello",
    }

    with pytest.raises(ValidationError):
        validator.validate(payload)


def test_valid_cancellation_parameters() -> None:
    validator = load_validator("methods/plugin-cancel.params.schema.json")

    validator.validate({"execution_id": "execution-001"})


def test_valid_capability_invocation() -> None:
    validator = load_validator(
        "methods/host-capability-invoke.params.schema.json"
    )

    payload = {
        "execution_id": "execution-001",
        "capability": "model.inference",
        "operation": "generate",
        "input": {"prompt": "Explain JSON-RPC"},
    }

    validator.validate(payload)


def test_capability_rejects_invalid_name() -> None:
    validator = load_validator(
        "methods/host-capability-invoke.params.schema.json"
    )

    payload = {
        "execution_id": "execution-001",
        "capability": "INVALID CAPABILITY",
        "operation": "generate",
        "input": {},
    }

    with pytest.raises(ValidationError):
        validator.validate(payload)


def test_valid_token_usage_event() -> None:
    validator = load_validator("methods/plugin-token-usage.params.schema.json")

    payload = {
        "execution_id": "execution-001",
        "event_type": "token_usage",
        "data": {
            "input_tokens": 120,
            "output_tokens": 350,
            "total_tokens": 470,
        },
    }

    validator.validate(payload)


def test_envelope_accepts_request() -> None:
    validator = load_validator("message-envelope.schema.json")

    validator.validate({
        "jsonrpc": "2.0",
        "id": "host:exec-001",
        "method": "plugin.execute",
        "params": {},
    })


def test_envelope_accepts_notification() -> None:
    validator = load_validator("message-envelope.schema.json")

    validator.validate({
        "jsonrpc": "2.0",
        "method": "plugin.progress",
        "params": {"progress": 50},
    })


def test_envelope_accepts_success_response() -> None:
    validator = load_validator("message-envelope.schema.json")

    validator.validate({
        "jsonrpc": "2.0",
        "id": "host:exec-001",
        "result": {"status": "success", "data": {}},
    })


def test_envelope_accepts_error_response() -> None:
    validator = load_validator("message-envelope.schema.json")

    validator.validate({
        "jsonrpc": "2.0",
        "id": "host:exec-001",
        "error": {
            "code": -32001,
            "message": "Plugin execution failed",
            "data": {"retryable": False},
        },
    })


def test_envelope_rejects_unsupported_jsonrpc_version() -> None:
    validator = load_validator("message-envelope.schema.json")

    payload = {
        "jsonrpc": "1.0",
        "id": "host:exec-001",
        "method": "plugin.execute",
    }

    with pytest.raises(ValidationError):
        validator.validate(payload)
