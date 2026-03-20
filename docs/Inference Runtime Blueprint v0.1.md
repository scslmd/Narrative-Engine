# Inference Runtime Blueprint v0.1

## Purpose

This document defines the deterministic runtime contract for provider-backed text generation in Narrative-Engine.

It exists to keep orchestration, executor, and checker code stable while allowing the backing inference provider to change through configuration instead of backend-specific control flow.

This blueprint covers:

- supported providers
- environment-variable configuration
- generalized request and response contracts
- provider defaults
- runtime error taxonomy

## Current Implementation Scope

The current backend implements:

- a provider-agnostic inference interface
- a reusable OpenAI-compatible HTTP transport
- provider selection through environment variables
- runtime descriptors for provider identity, capabilities, and defaults

The current backend does not yet implement:

- provider-specific transports beyond the generalized OpenAI-compatible path
- normalized structured runtime error objects beyond `InferenceBackendError`
- runtime-backed orchestration across all phases

## Supported Providers

The generalized inferencer supports these configured backends:

- `llama.cpp`
- `lmstudio`
- `vllm`
- `openai_compatible`

Implementation note:

- `llama.cpp`, `lmstudio`, `vllm`, and `openai_compatible` currently all use the same OpenAI-compatible HTTP adapter
- `stub` also exists as a local fallback backend, but it is not a real provider target and is outside the provider-runtime scope of this document

## Provider Identity And Transport

Each configured backend resolves to an `InferenceProviderDescriptor` with these deterministic fields:

- `backend`
- `display_name`
- `transport`
- `base_url`
- `default_model`
- `timeout_seconds`
- `supports_model_listing`
- `supports_chat_completions`
- `aliases`

Current transport mapping:

- `llama.cpp` -> `openai_compatible_http`
- `lmstudio` -> `openai_compatible_http`
- `vllm` -> `openai_compatible_http`
- `openai_compatible` -> `openai_compatible_http`

Current display-name mapping:

- `llama.cpp` -> `llama.cpp Server`
- `lmstudio` -> `LM Studio`
- `vllm` -> `vLLM`
- `openai_compatible` -> `OpenAI-Compatible Runtime`

Current alias mapping:

- `llama.cpp` -> `llama-server`, `openai-compatible`
- `lmstudio` -> `lm-studio`, `openai-compatible`
- `vllm` -> `openai-compatible`
- `openai_compatible` -> `openai-compatible`

## Environment Variables

The inference runtime is configured through these environment variables:

### `NARRATIVE_INFERENCE_BACKEND`

Purpose:

- selects the active inference backend

Accepted values:

- `stub`
- `llama.cpp`
- `lmstudio`
- `vllm`
- `openai_compatible`

Default:

- `stub`

### `NARRATIVE_INFERENCE_BASE_URL`

Purpose:

- overrides the runtime base URL for the selected backend

Default behavior:

- if explicitly set, the configured value is used
- if unset, the backend-specific default base URL is used

### `NARRATIVE_INFERENCE_API_KEY`

Purpose:

- sets the bearer token used for OpenAI-compatible HTTP requests

Default:

- unset

Behavior:

- if absent or empty, no `Authorization` header is sent

### `NARRATIVE_INFERENCE_MODEL`

Purpose:

- defines the runtime-default model name passed when a request does not provide `model`

Default:

- unset

Behavior:

- if both the request and environment are missing a model value, the generated payload sends `model: null`

### `NARRATIVE_INFERENCE_TIMEOUT_SECONDS`

Purpose:

- controls request timeout for provider HTTP calls

Default:

- `120`

Behavior:

- parsed as a float
- invalid values fall back deterministically to `120.0`

## Provider Defaults

If `NARRATIVE_INFERENCE_BASE_URL` is unset, these provider defaults apply:

- `llama.cpp` -> `http://127.0.0.1:8080`
- `lmstudio` -> `http://127.0.0.1:1234`
- `vllm` -> `http://127.0.0.1:8000`
- `openai_compatible` -> `http://127.0.0.1:8000`

Base URL normalization rules:

- trailing `/` is removed
- if the configured URL does not already end in `/v1`, `/v1` is appended
- if it already ends in `/v1`, it is used as-is

Capability defaults for OpenAI-compatible providers:

- `supports_model_listing = true`
- `supports_chat_completions = true`

## Generalized Inferencer Contract

The generalized inferencer exposes two backend-facing operations:

- `list_models() -> list[str]`
- `generate_text(request: InferenceRequest) -> InferenceResponse`

The inferencer surface is provider-agnostic. Callers should construct one request shape and consume one response shape regardless of the configured backend.

## Request Contract

`generate_text()` accepts an `InferenceRequest` with these fields:

- `messages`
- `model`
- `temperature`
- `max_tokens`
- `metadata`

### Request Field Definitions

`messages`

- type: `list[InferenceMessage]`
- default: `[]`
- each message contains:
  - `role`: `system` | `user` | `assistant`
  - `content`: `str`

`model`

- type: `str | None`
- if unset, the runtime uses the descriptor default model from `NARRATIVE_INFERENCE_MODEL`

`temperature`

- type: `float | None`
- omitted from the outbound provider payload if unset

`max_tokens`

- type: `int | None`
- omitted from the outbound provider payload if unset

`metadata`

- type: `dict[str, Any]`
- default: `{}`
- forwarded to OpenAI-compatible providers as a `metadata` object when present

### Outbound OpenAI-Compatible Payload

For OpenAI-compatible providers, the outbound payload is:

```json
{
  "model": "string or null",
  "messages": [
    {
      "role": "system|user|assistant",
      "content": "string"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "metadata": {
    "role": "architect"
  }
}
```

Deterministic payload rules:

- `model` is `request.model` if present, otherwise the descriptor default model
- `temperature` is included only when not `null`
- `max_tokens` is included only when not `null`
- `metadata` is included only when non-empty

## Response Contract

`generate_text()` returns an `InferenceResponse` with these fields:

- `backend`
- `model`
- `content`
- `finish_reason`
- `usage`
- `raw_response`

### Response Field Definitions

`backend`

- type: configured backend literal
- examples: `llama.cpp`, `lmstudio`, `vllm`, `openai_compatible`

`model`

- type: `str | None`
- resolved from the provider response if present, otherwise from the request payload model

`content`

- type: `str`
- extracted from the first choice in the provider response

`finish_reason`

- type: `str | None`
- extracted from the first choice when available

`usage`

- type: `InferenceUsage`
- fields:
  - `prompt_tokens`
  - `completion_tokens`
  - `total_tokens`

`raw_response`

- type: `dict[str, Any]`
- contains the unmodified provider payload returned by the transport layer

### Content Extraction Rules

The current OpenAI-compatible adapter reads the first item in `choices`.

Content is extracted deterministically as follows:

- if `choices` is missing or empty, the request fails
- if `choices[0].message.content` is a string, that string becomes `content`
- if `choices[0].message.content` is a list, `content` is the concatenation of `text` values from list items that contain string `text`
- otherwise, `content` is an empty string

### Model Listing Contract

`list_models()` expects an OpenAI-compatible `/models` response with a top-level `data` array.

Model-listing rules:

- non-dict entries are ignored
- entries without a non-empty string `id` are ignored
- returned values are deduplicated and sorted

## Deterministic Caller Expectations

All callers should treat the generalized inferencer as:

- message-based
- single-response
- first-choice only
- transport-agnostic above the backend factory

Callers should not:

- construct provider-specific URLs
- inject provider-specific headers directly
- parse provider-specific payload shapes outside the inference package
- assume token usage is always present

## Runtime Error Taxonomy

The current transport raises `InferenceBackendError` with provider-specific text, but the runtime layer should normalize failures into the following deterministic categories.

### `configuration`

Meaning:

- runtime configuration is invalid before a request is sent

Examples:

- unsupported backend selection
- missing required base URL for a non-default deployment
- unusable timeout configuration after parsing safeguards are exhausted

Retryability:

- non-retryable until configuration changes

### `timeout`

Meaning:

- the provider did not respond before `NARRATIVE_INFERENCE_TIMEOUT_SECONDS`

Examples:

- HTTP request timeout
- socket read timeout

Retryability:

- retryable

### `transport`

Meaning:

- the request failed before a valid HTTP response was received

Examples:

- DNS failure
- connection refused
- connection reset
- TLS or socket-level transport failure

Retryability:

- usually retryable

### `http_status`

Meaning:

- the provider returned an HTTP response outside the success range

Examples:

- `401 Unauthorized`
- `404 Not Found`
- `429 Too Many Requests`
- `500 Internal Server Error`

Retryability:

- depends on status class
- `429`, `502`, `503`, and `504` should be treated as retryable by default
- most `4xx` configuration or request errors should be treated as non-retryable

### `invalid_json`

Meaning:

- the provider returned a non-JSON or malformed JSON response body

Examples:

- HTML error page
- truncated JSON body
- invalid JSON syntax

Retryability:

- retryable if the failure is transient
- otherwise operationally suspicious and should be surfaced clearly

### `protocol`

Meaning:

- the provider returned JSON that does not satisfy the expected OpenAI-compatible shape

Examples:

- top-level payload is not an object
- `/chat/completions` returns no `choices`
- `/models` returns a non-list `data` payload

Retryability:

- usually non-retryable until the provider or adapter contract is fixed

### `provider_rejected`

Meaning:

- the provider accepted the transport request but rejected the semantic request

Examples:

- unknown model name
- invalid parameter combination
- unsupported chat-completions feature

Retryability:

- non-retryable unless the request payload changes

## Current Error Mapping Status

Current implementation behavior in `app/inference/openai_compatible.py`:

- `httpx.HTTPError` -> wrapped as `InferenceBackendError` with provider display-name context
- JSON decode failure -> wrapped as `InferenceBackendError` with invalid-JSON text
- missing or empty `choices` -> wrapped as `InferenceBackendError`
- non-object JSON payload -> wrapped as `InferenceBackendError`

Current limitation:

- these failures are not yet persisted as normalized structured runtime error categories on step records
- timeout, HTTP-status, invalid-JSON, and protocol-shape failures still need explicit category mapping in the runtime-backed execution path

## Provider Default Summary

| Backend | Transport | Default Base URL | Default Model Source | API Key |
|---|---|---|---|---|
| `llama.cpp` | `openai_compatible_http` | `http://127.0.0.1:8080/v1` | `NARRATIVE_INFERENCE_MODEL` | optional |
| `lmstudio` | `openai_compatible_http` | `http://127.0.0.1:1234/v1` | `NARRATIVE_INFERENCE_MODEL` | optional |
| `vllm` | `openai_compatible_http` | `http://127.0.0.1:8000/v1` | `NARRATIVE_INFERENCE_MODEL` | optional |
| `openai_compatible` | `openai_compatible_http` | `http://127.0.0.1:8000/v1` | `NARRATIVE_INFERENCE_MODEL` | optional |

## Integration Rule

All future runtime-backed pipeline phases and checker roles should depend on:

- `InferenceRequest`
- `InferenceResponse`
- `InferenceProviderDescriptor`
- `InferenceBackendError`

and not on provider-specific request construction outside the inference package.
