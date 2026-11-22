# Patchbay Universal Plugin Protocol v1

**Status:** Draft  
**Protocol Version:** 1.0  
**Project:** Patchbay  
**Tagline:** Connect. Extend. Create.

---

## 1. Objective

Define a language-independent communication protocol between Patchbay Core and plugin workers.

The protocol must support plugins written in:

- Python
- TypeScript / JavaScript
- Go
- Other languages through compatible SDKs

The protocol establishes a standardized communication contract between the Patchbay host and independently executing plugin workers.

## 2. Core Design Decisions

- Protocol: JSON-RPC 2.0
- Initial transport: Newline-delimited JSON (NDJSON) over stdio
- Data format: JSON
- Schema validation: JSON Schema
- Protocol version: 1.0
- Communication: Bidirectional
- Execution model: Isolated worker architecture (target)
- Initial implementation: Python

The communication protocol must remain independent of the programming language used to implement a plugin.

## 3. Plugin Lifecycle

The protocol must support the following lifecycle operations:

1. Discovery
2. Initialization
3. Execution
4. Progress reporting
5. Streaming output
6. Cancellation
7. Shutdown

Expected lifecycle:

Discovered -> Validated -> Initialized -> Active -> Executing -> Active -> Shutdown

Failed initialization, execution failures and worker termination must be handled explicitly by the host.

## 4. Message Types

### 4.1 Host-to-plugin requests

- `plugin.initialize`
- `plugin.execute`
- `plugin.cancel`
- `plugin.shutdown`

### 4.2 Plugin-to-host notifications

- `plugin.progress`
- `plugin.output`
- `plugin.event`

### 4.3 Plugin-to-host capability requests

- `host.capability.invoke`

### 4.4 Communication rules

- Requests require responses.
- Notifications do not require responses.
- Capability requests require host responses.
- Every response must correlate with its original request.
- Both host and plugin must be capable of initiating requests.

## 5. Execution Contract

Every execution request must contain:

- `execution_id`
- `input`
- `timeout_ms`

Every successful execution response must contain:

- `status`
- `data`

Every failed execution response must contain:

- Error code
- Error message
- Retryability information

Execution inputs and outputs must use JSON-compatible data structures.

The host must validate execution requests before dispatching them to workers.

## 6. AI Support

The protocol must support the communication requirements of AI-powered plugins.

Required capabilities include:

- Incremental text output
- Structured output
- Token usage events
- Progress reporting
- Tool-call requests
- Execution cancellation
- Long-running operations
- Multimodal data references

AI-specific interfaces and semantics will be defined separately in the Patchbay AI Plugin API specification.

The universal protocol must not depend on a specific LLM provider or AI framework.

## 7. Capability Security

Plugins must not receive unrestricted access to host resources.

Host capabilities must be mediated through explicit permission checks.

Examples of capabilities:

- `filesystem.read`
- `filesystem.write`
- `network.http`
- `model.inference`
- `secrets.read`
- `database.query`

### 7.1 Capability enforcement

The host must:

- Validate every capability request.
- Check whether the plugin has been granted the requested capability.
- Enforce resource-level restrictions.
- Reject unauthorized requests.
- Record capability invocation events.
- Prevent plugins from bypassing capability enforcement.

### 7.2 Least privilege

Plugins must receive only the permissions required for their declared functionality.

Capability declarations in the manifest are not security enforcement.

The runtime must independently enforce permissions.

## 8. Versioning

Protocol versioning must remain independent of:

- Plugin version
- SDK version
- Host API version

The protocol version follows a major.minor format.

Example:

`1.0`

Versioning rules:

- Major-version incompatibilities must be rejected.
- Minor versions must preserve backward compatibility.
- Unsupported protocol versions must produce explicit errors.
- Feature negotiation must happen during initialization.

The host must not assume that a plugin supports a feature merely because the protocol defines it.

## 9. Security Requirements

The protocol and runtime must enforce the following requirements:

- Never treat stdio communication as a complete sandbox.
- Never expose host secrets through unrestricted environment variables.
- Enforce execution timeouts.
- Validate incoming and outgoing messages.
- Restrict filesystem access.
- Restrict network access.
- Enforce resource limits.
- Record structured execution events.
- Handle worker crashes and unexpected termination.
- Prevent unauthorized capability invocation.
- Avoid leaking sensitive information through error messages.

Untrusted plugins must execute outside the host process with appropriate operating-system isolation.

## 10. Implementation Status and Boundary

**Specification status: Draft.** This document describes the intended language-independent protocol. The current implementation supports an initial subset and must not be treated as complete protocol conformance.

### 10.1 Implemented foundation

The repository currently includes:

- A Python `patchbay-protocol` package.
- JSON-RPC 2.0 message encoding and decoding.
- NDJSON framing over stdio.
- JSON Schema validation for the implemented message envelope and selected method parameters.
- A bidirectional asynchronous RPC peer with request correlation.
- Execution tracking, timeout handling and cooperative cancellation.
- A Python worker entry point that can initialize, execute and shut down a plugin in a separate subprocess.
- A worker integration test covering the Hello World plugin lifecycle.

### 10.2 Not yet implemented or complete

The following remain incomplete:

- A reusable host-side worker manager and process supervisor.
- Integration of the managed worker runtime into the normal CLI execution path.
- Reliable process termination escalation for uncooperative plugin code.
- Comprehensive worker crash monitoring and recovery.
- Host-side capability brokering and enforceable permission checks.
- Operating-system-level filesystem, network, credential and resource isolation.
- Full implementation and conformance testing of all proposed protocol methods and features.
- Complete protocol and host API compatibility negotiation.

The current worker validates the protocol version and plugin identity during initialization. Host API compatibility enforcement still needs to be completed.

### 10.3 Security boundary

The existing trusted-local Python plugin loader must not be presented as a sandbox.

The subprocess worker provides process separation, but does not by itself restrict the operating-system permissions available to plugin code. Do not execute untrusted plugins through the current prototype.

The protocol remains a draft and may change as implementation and conformance testing progress.
---

## 11. Transport Rules

### 11.1 Initial transport

Protocol v1 uses newline-delimited JSON over standard input and standard output.

Communication channels:

| Channel | Direction | Purpose |
|---|---|---|
| stdin | Host -> Worker | Requests and responses |
| stdout | Worker -> Host | Responses, notifications and requests |
| stderr | Worker -> Host | Diagnostic logs |

### 11.2 Framing

- Each message must be one JSON object.
- Each message must be serialized onto a single line.
- Messages are terminated by a newline character.
- Encoding must be UTF-8.
- stdout must contain protocol messages only.
- Diagnostic logs must go to stderr.
- Both sides must support bidirectional RPC communication.

### 11.3 Transport constraints

The host must:

- Enforce maximum message sizes.
- Reject malformed JSON.
- Reject unsupported protocol versions.
- Correlate responses with request IDs.
- Handle partial reads and writes.
- Handle broken pipes.
- Detect unexpected worker termination.
- Enforce execution deadlines.

JSON-RPC batch messages are not supported in protocol v1.

---

## 12. Message Envelope

All protocol messages must follow JSON-RPC 2.0.

### 12.1 Initialization request

Example host initialization request:

{
  "jsonrpc": "2.0",
  "id": "host:init-001",
  "method": "plugin.initialize",
  "params": {
    "protocol_version": "1.0",
    "host_api_version": "1.0",
    "plugin_id": "org.patchbay.examples.hello-world",
    "configuration": {},
    "granted_capabilities": []
  }
}

### 12.2 Initialization response

Example worker response:

{
  "jsonrpc": "2.0",
  "id": "host:init-001",
  "result": {
    "status": "success",
    "protocol_version": "1.0",
    "supported_features": [
      "progress",
      "streaming",
      "cancellation"
    ]
  }
}

### 12.3 Shutdown request

Example:

{
  "jsonrpc": "2.0",
  "id": "host:shutdown-001",
  "method": "plugin.shutdown",
  "params": {}
}

Expected response:

{
  "jsonrpc": "2.0",
  "id": "host:shutdown-001",
  "result": {
    "status": "success"
  }
}

---

## 13. Execution Messages

### 13.1 Host execution request

{
  "jsonrpc": "2.0",
  "id": "host:exec-001",
  "method": "plugin.execute",
  "params": {
    "execution_id": "execution-001",
    "input": {
      "message": "Hello Patchbay"
    },
    "timeout_ms": 30000
  }
}

### 13.2 Successful execution response

{
  "jsonrpc": "2.0",
  "id": "host:exec-001",
  "result": {
    "status": "success",
    "data": {
      "message": "Hello from Patchbay"
    }
  }
}

### 13.3 Progress notification

Worker progress notification:

{
  "jsonrpc": "2.0",
  "method": "plugin.progress",
  "params": {
    "execution_id": "execution-001",
    "progress": 50,
    "message": "Processing"
  }
}

Progress values must be between 0 and 100.

Progress notifications must not contain request IDs.

---

## 14. Capability Requests

Plugins must request host-mediated capabilities instead of accessing protected host resources directly.

### 14.1 Example capability request

{
  "jsonrpc": "2.0",
  "id": "plugin:capability-001",
  "method": "host.capability.invoke",
  "params": {
    "execution_id": "execution-001",
    "capability": "model.inference",
    "operation": "generate",
    "input": {
      "prompt": "Explain JSON-RPC"
    }
  }
}

### 14.2 Successful capability response

{
  "jsonrpc": "2.0",
  "id": "plugin:capability-001",
  "result": {
    "status": "success",
    "data": {
      "text": "JSON-RPC is a remote procedure call protocol..."
    }
  }
}

### 14.3 Unauthorized capability response

The host must reject unauthorized requests.

{
  "jsonrpc": "2.0",
  "id": "plugin:capability-001",
  "error": {
    "code": -32002,
    "message": "Capability access denied",
    "data": {
      "capability": "model.inference",
      "retryable": false
    }
  }
}

The host must validate the permission before executing the requested capability.

Capability requests must never automatically grant additional permissions.

---

## 15. Transport Constraints

Additional protocol constraints:

- Enforce maximum message sizes.
- Reject malformed JSON.
- Reject invalid JSON-RPC envelopes.
- Reject unsupported protocol versions.
- Validate request parameters.
- Correlate every response with its request ID.
- Enforce execution deadlines.
- Reject unauthorized capability requests.
- Handle worker termination and broken pipes.
- Prevent malformed or oversized messages from exhausting host resources.

All protocol messages must be validated before processing.

---

## 16. Error Handling

Errors must follow the JSON-RPC 2.0 error response structure.

### 16.1 Successful response

{
  "jsonrpc": "2.0",
  "id": "host:exec-001",
  "result": {
    "status": "success",
    "data": {}
  }
}

### 16.2 Failed response

{
  "jsonrpc": "2.0",
  "id": "host:exec-001",
  "error": {
    "code": -32001,
    "message": "Plugin execution failed",
    "data": {
      "retryable": false
    }
  }
}

### 16.3 Error requirements

A response must contain either `result` or `error`, never both.

Standard JSON-RPC error codes must be respected:

- `-32700`: Parse error
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

Patchbay application-specific errors must use the reserved server error range.

Proposed application errors:

- `-32001`: Plugin execution failed
- `-32002`: Capability access denied
- `-32003`: Execution timeout
- `-32004`: Plugin initialization failed
- `-32005`: Unsupported protocol version
- `-32006`: Worker unavailable
- `-32007`: Execution cancelled

Retryability information must be provided inside the error data object.

Sensitive host information must never be exposed in error messages.

---

## 17. Request Correlation

Both the host and plugin can initiate RPC requests.

### 17.1 Request ID rules

- Every request must have a unique string ID within its sender session.
- Host-generated request IDs must use the prefix `host:`.
- Plugin-generated request IDs must use the prefix `plugin:`.
- Responses must echo the original request ID.
- Notifications must not contain an ID.
- Notifications must not receive responses.
- JSON-RPC batch messages are not supported in protocol v1.

### 17.2 Bidirectional communication

The host can send requests to the worker.

The worker can send requests to the host.

Example:

1. Host sends `plugin.execute`.
2. Worker begins execution.
3. Worker requests `host.capability.invoke`.
4. Host validates the capability.
5. Host returns the capability response.
6. Worker continues execution.
7. Worker returns the final execution response.

The worker must be able to process host responses while an execution is active.

The host must be able to process plugin-originated requests while awaiting an execution response.

---

## 18. Execution Cancellation

### 18.1 Timeout behavior

`timeout_ms` represents the maximum execution time budget in milliseconds.

- The host starts measuring the execution budget when dispatching the request.
- The host is responsible for enforcing the timeout.
- The worker should respect the supplied timeout.
- A worker must not be trusted to enforce its own execution deadline.

### 18.2 Cancellation request

The host can request cancellation using `plugin.cancel`.

Example:

{
  "jsonrpc": "2.0",
  "id": "host:cancel-001",
  "method": "plugin.cancel",
  "params": {
    "execution_id": "execution-001"
  }
}

### 18.3 Cancellation response

{
  "jsonrpc": "2.0",
  "id": "host:cancel-001",
  "result": {
    "status": "accepted",
    "execution_id": "execution-001"
  }
}

### 18.4 Cancellation requirements

- The worker should stop execution cooperatively.
- The worker must acknowledge cancellation.
- The original execution request must eventually receive a terminal response.
- The host must enforce a configurable cancellation grace period.
- The host may terminate the worker if it fails to stop within that period.
- Cancellation must not affect unrelated executions.

The runtime must support receiving cancellation requests while an execution is active.

---

## 19. Streaming Output

Plugins may produce incremental output during execution.

This is particularly important for LLM integrations, agent workflows and long-running operations.

### 19.1 Streaming notification

Example:

{
  "jsonrpc": "2.0",
  "method": "plugin.output",
  "params": {
    "execution_id": "execution-001",
    "sequence": 1,
    "content_type": "text/plain",
    "chunk": "Hello from Patchbay"
  }
}

### 19.2 Streaming requirements

- Each output notification must identify its execution.
- Sequence numbers must increase within an execution.
- Output notifications must not contain request IDs.
- The final execution response indicates completion.
- Token usage must be reported through structured events.
- The host must preserve output ordering.
- The runtime must enforce streaming buffer limits.

### 19.3 Supported output types

Initial supported content types:

- `text/plain`
- `application/json`

Additional multimodal content types may be introduced in future protocol versions.

### 19.4 Token usage event

Example:

{
  "jsonrpc": "2.0",
  "method": "plugin.event",
  "params": {
    "execution_id": "execution-001",
    "event_type": "token_usage",
    "data": {
      "input_tokens": 120,
      "output_tokens": 350,
      "total_tokens": 470
    }
  }
}

Events must be structured and associated with the corresponding execution.

---

## 20. Feature Negotiation

During initialization, the plugin must advertise the protocol features it supports.

Example:

{
  "jsonrpc": "2.0",
  "id": "host:init-001",
  "result": {
    "status": "success",
    "protocol_version": "1.0",
    "supported_features": [
      "progress",
      "streaming",
      "cancellation",
      "capability_invocation"
    ]
  }
}

The host must determine which features are available before starting executions.

Unsupported optional features must not cause initialization failure unless they are explicitly required by the plugin.

---

## 21. Future Extensions

The following capabilities are candidates for future protocol versions:

- WebSocket transport
- HTTP-based transport
- Remote plugin workers
- Distributed plugin execution
- Multimodal streaming
- Binary data transfer
- Advanced execution scheduling
- Plugin-to-plugin communication
- Distributed agent orchestration
- Worker pooling and autoscaling

These features are outside the initial protocol v1 implementation scope.

---

## 22. Implementation Roadmap

Implementation must proceed in stages.

### Stage 1: Protocol foundation

- Define JSON-RPC message schemas.
- Define request and response validation.
- Implement newline-delimited JSON framing.
- Implement request correlation.
- Implement structured errors.

### Stage 2: Worker runtime

- Implement worker process creation.
- Implement host-worker communication.
- Implement initialization and shutdown.
- Implement execution dispatch.
- Implement worker failure handling.

### Stage 3: Security

- Implement capability enforcement.
- Implement execution timeouts.
- Implement cancellation.
- Implement resource restrictions.
- Implement audit events.

### Stage 4: Advanced execution

- Implement streaming output.
- Implement progress notifications.
- Implement feature negotiation.
- Implement structured events.

### Stage 5: Cross-language support

- Implement Python worker SDK.
- Implement TypeScript worker SDK.
- Implement Go worker SDK.
- Validate cross-language interoperability.

---

## 23. Acceptance Criteria

Protocol v1 must not be considered implementation-ready until the following tests pass:

1. A worker can initialize successfully.
2. A worker can execute a valid request.
3. A worker can return structured results.
4. Invalid messages are rejected.
5. Unknown methods produce explicit errors.
6. Request and response IDs are correlated correctly.
7. Workers can request host capabilities.
8. Unauthorized capabilities are rejected.
9. Execution timeouts are enforced by the host.
10. Cancellation works during active execution.
11. Streaming output preserves ordering.
12. Worker crashes are detected and handled.
13. Shutdown releases worker resources.
14. Python and another language can communicate using the same protocol.

The protocol must be validated through automated unit and integration tests before being declared stable.

---

**End of Patchbay Universal Plugin Protocol v1**
