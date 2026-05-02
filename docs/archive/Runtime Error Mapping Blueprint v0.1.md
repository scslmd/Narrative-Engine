# Runtime Error Mapping Blueprint v0.1

## Purpose

This document defines the deterministic mapping from generalized inferencer failures to persisted runtime error fields.

It exists to make runtime-backed execution consistent across:

- `app/inference/openai_compatible.py`
- future provider adapters
- runtime-backed executor paths such as `app/services/local_executor.py`
- attempt rows
- step records

The goal is not to preserve provider-specific exception text as the primary contract. The goal is to normalize failures into stable categories suitable for persistence, retry policy, inspect views, and later orchestration behavior.

Current implementation status:

- the blueprint is now part of the reconstruction-grade docs set
- current successful runtime-backed `P-100` execution is implemented
- normalized inferencer failure persistence is still only partially implemented; generic `InferenceBackendError` and executor fallback handling still exist in the active code path

## Contract Goals

- map each runtime failure into one deterministic `error_category`
- assign a stable `error_code`
- assign a stable terminal `finish_reason`
- classify retryability consistently
- preserve provider or transport detail in diagnostic text without making that text the contract
- allow the executor to persist the same shape for jobs, checker runs, and future orchestration steps

## Mapping Targets

The normalized mapping should populate these persistence targets.

### Attempt Rows

Attempt rows should carry:

- `finish_reason`
- `failure_stage`
- `retryable`
- `error_code`
- `error_category`

Recommended failure stage for provider-backed generation failures:

- `failure_stage = "inference"`

### Step Records

Runtime-backed step records should carry:

- `finish_reason`
- `error_code`
- `error_category`

If a request was successfully built and dispatched, the step record should also preserve:

- `prompt_hash`
- `input_hash`
- `output_hash` if any partial or usable output exists
- `backend_name`
- `backend_version` when available
- `model_id`

### Diagnostic Text

Human-readable provider or exception text should be stored in:

- run `detail`
- run `error`
- structured logs when present

That text is diagnostic only. The contract fields above are the durable source of truth.

## Normalized Error Categories

The first runtime slice should normalize provider failures into these categories.

### `timeout`

Definition:

- the request exceeded the configured timeout before a successful response payload was received

Examples:

- `httpx.TimeoutException`
- provider-side timeout surfaced through transport timeout semantics

Persistence mapping:

- `error_category = "timeout"`
- `error_code = "INFERENCE_TIMEOUT"`
- `finish_reason = "timeout"`
- `retryable = true`

Default rationale:

- timeout is usually transient and should be eligible for retry unless a caller explicitly overrides policy

### `transport_failure`

Definition:

- the request failed before a valid HTTP response was available

Examples:

- DNS failure
- connection refused
- TLS handshake failure
- socket reset
- generic network unavailability

Persistence mapping:

- `error_category = "transport_failure"`
- `error_code = "INFERENCE_TRANSPORT_FAILURE"`
- `finish_reason = "transport_failed"`
- `retryable = true`

Default rationale:

- transport failures are usually transient infrastructure failures

### `http_status_failure`

Definition:

- the provider returned a non-success HTTP status and the request completed at the HTTP layer

Examples:

- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `408 Request Timeout`
- `409 Conflict`
- `422 Unprocessable Entity`
- `429 Too Many Requests`
- `500 Internal Server Error`
- `502 Bad Gateway`
- `503 Service Unavailable`
- `504 Gateway Timeout`

Persistence mapping:

- `error_category = "http_status_failure"`
- `error_code = "HTTP_<status_code>"`
  Example: `HTTP_503`
- `finish_reason = "provider_http_error"`
- `retryable =` see retry table below

Retry guidance:

- retryable by default: `408`, `409`, `425`, `429`, `500`, `502`, `503`, `504`
- non-retryable by default: most other `4xx`

### `invalid_json`

Definition:

- the provider returned a response body, but it could not be parsed as JSON

Examples:

- malformed JSON body
- truncated JSON body
- HTML error page returned where JSON was expected

Persistence mapping:

- `error_category = "invalid_json"`
- `error_code = "INVALID_JSON_RESPONSE"`
- `finish_reason = "invalid_response"`
- `retryable = true`

Default rationale:

- malformed transport payloads are often transient provider or gateway failures

### `protocol_shape_failure`

Definition:

- the response was valid JSON, but did not match the minimum adapter protocol shape expected by the runtime

Examples:

- top-level JSON payload is not an object
- `choices` missing
- `choices` is empty
- completion message content is structurally unusable
- required fields exist but are of incompatible types

Persistence mapping:

- `error_category = "protocol_shape_failure"`
- `error_code = "INVALID_RESPONSE_SHAPE"`
- `finish_reason = "invalid_response"`
- `retryable = false`

Default rationale:

- protocol-shape failures usually indicate provider or adapter incompatibility rather than a transient condition

### `provider_rejected_request`

Definition:

- the provider rejected the request as invalid for semantic or policy reasons

Examples:

- unsupported model name
- unsupported parameter combination
- context window exceeded
- provider-side validation error
- safety or policy rejection surfaced as a deterministic request rejection

Persistence mapping:

- `error_category = "provider_rejected_request"`
- `error_code =` provider-specific normalized code when available, otherwise `PROVIDER_REJECTED_REQUEST`
- `finish_reason = "request_rejected"`
- `retryable = false`

Default rationale:

- the same request will usually fail again until the request payload changes

### `configuration_error`

Definition:

- runtime configuration was invalid before or during dispatch

Examples:

- base URL missing or malformed
- unsupported backend selection
- missing API key when required
- missing default model when the request does not specify one
- executor built an impossible request because required config was absent

Persistence mapping:

- `error_category = "configuration_error"`
- `error_code = "RUNTIME_CONFIGURATION_ERROR"`
- `finish_reason = "configuration_error"`
- `retryable = false`

Default rationale:

- retries will not help until configuration changes

## Retry Classification Table

These defaults should drive initial executor persistence.

| Category | Default `retryable` |
| --- | --- |
| `timeout` | `true` |
| `transport_failure` | `true` |
| `http_status_failure` | depends on status code |
| `invalid_json` | `true` |
| `protocol_shape_failure` | `false` |
| `provider_rejected_request` | `false` |
| `configuration_error` | `false` |

For `http_status_failure`, use:

- `true` for `408`, `409`, `425`, `429`, `500`, `502`, `503`, `504`
- `false` for all other statuses unless a provider-specific override is introduced later

## Stable Finish Reasons

The runtime-backed error path should use these normalized terminal `finish_reason` values.

Success-related values may still include:

- `completed`
- `stop`
- `report_saved`
- `passed`
- `validation_failed`

Failure-related runtime values should normalize to:

- `timeout`
- `transport_failed`
- `provider_http_error`
- `invalid_response`
- `request_rejected`
- `configuration_error`
- `executor_error`

Rules:

- provider-native finish reasons such as `stop` may be preserved on success
- provider-native finish reasons should not replace normalized runtime failure reasons on failure
- if the failure occurs outside the inferencer contract entirely, the executor may still use `executor_error`

## Stable Error Codes

The following codes should be treated as the initial stable contract.

- `INFERENCE_TIMEOUT`
- `INFERENCE_TRANSPORT_FAILURE`
- `INVALID_JSON_RESPONSE`
- `INVALID_RESPONSE_SHAPE`
- `PROVIDER_REJECTED_REQUEST`
- `RUNTIME_CONFIGURATION_ERROR`
- `HTTP_<status_code>`

Optional provider-specific extension:

- adapters may later emit more specific codes such as `MODEL_NOT_FOUND` or `CONTEXT_LENGTH_EXCEEDED`
- those codes should still map into one of the normalized categories above

## Adapter Responsibilities

### `app/inference/openai_compatible.py`

This adapter currently wraps failures into `InferenceBackendError` with provider-specific text.

The next implementation slice should make the adapter expose enough structured failure detail for normalization, either by:

- extending `InferenceBackendError` with structured attributes, or
- introducing a dedicated runtime error type that carries:
  - `category`
  - `code`
  - `retryable`
  - `http_status` optional
  - `provider_message` optional

Expected mapping points in the current adapter:

- `httpx.TimeoutException` -> `timeout`
- non-timeout `httpx.TransportError` or equivalent -> `transport_failure`
- `httpx.HTTPStatusError` -> `http_status_failure` or `provider_rejected_request` based on status classification
- JSON decode failure -> `invalid_json`
- non-object payload or missing `choices` -> `protocol_shape_failure`

Suggested split for HTTP statuses:

- `400`, `401`, `403`, `404`, `422` -> `provider_rejected_request`
- `408`, `409`, `425`, `429`, `500`, `502`, `503`, `504` -> `http_status_failure`

This split keeps deterministic request rejection separate from transient provider availability failures.

## Executor Responsibilities

Runtime-backed executor paths such as `app/services/local_executor.py` should:

1. catch normalized inferencer failures
2. persist attempt-row fields:
   - `finish_reason`
   - `failure_stage = "inference"`
   - `retryable`
   - `error_code`
   - `error_category`
3. persist step-record fields:
   - `finish_reason`
   - `error_code`
   - `error_category`
4. preserve human-readable exception text in:
   - run `detail`
   - run `error`

Rules:

- executors should not invent category values outside this blueprint
- executors may add provider text to diagnostics, but not replace normalized contract fields
- retry policy should read `retryable` from the normalized mapping rather than parsing exception text

## Step Record Expectations

When a runtime-backed step fails during inference:

- `state = "FAILED"`
- `finish_reason` should use the normalized failure reason
- `error_category` should use one of the categories above
- `error_code` should use the normalized code
- `prompt_hash` should still be persisted if the request was fully constructed
- `input_hash` should still be persisted if step input was available
- `output_hash` should remain `null` unless partial usable output exists and is intentionally captured

When the failure occurs before request construction:

- `error_category = "configuration_error"` or `executor_error`, depending on source
- `prompt_hash` may be `null`

## Attempt Row Expectations

When a run fails due to inference:

- `finish_reason` should use the normalized runtime failure reason
- `failure_stage = "inference"`
- `retryable` should follow the category mapping
- `error_code` should use the normalized stable code
- `error_category` should use the normalized category

If the run fails later during validation or persistence, those later stages should keep their own stage-specific mappings and must not be mislabeled as inference failures.

## Initial Deterministic Mapping Summary

| Failure mode | `error_category` | `error_code` | `finish_reason` | `retryable` |
| --- | --- | --- | --- | --- |
| timeout | `timeout` | `INFERENCE_TIMEOUT` | `timeout` | `true` |
| transport failure | `transport_failure` | `INFERENCE_TRANSPORT_FAILURE` | `transport_failed` | `true` |
| HTTP 429/5xx style failure | `http_status_failure` | `HTTP_<status>` | `provider_http_error` | `true` |
| HTTP deterministic rejection | `provider_rejected_request` | `HTTP_<status>` or provider code | `request_rejected` | `false` |
| invalid JSON | `invalid_json` | `INVALID_JSON_RESPONSE` | `invalid_response` | `true` |
| invalid protocol shape | `protocol_shape_failure` | `INVALID_RESPONSE_SHAPE` | `invalid_response` | `false` |
| runtime configuration failure | `configuration_error` | `RUNTIME_CONFIGURATION_ERROR` | `configuration_error` | `false` |

## Deliberate Boundary

This blueprint does not require implementation changes by itself.

It is a normalization contract for the next runtime slice so that:

- adapter failures become structured
- executor persistence becomes deterministic
- step-record and attempt storage use stable categories
- retry behavior stops depending on free-form exception strings
