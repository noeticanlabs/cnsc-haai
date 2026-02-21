# NPE Wire Protocol Security Documentation

This document describes the security hardening applied to the NPE (Noetican Proposal Engine) wire protocol client in the CNSC-HAAI system.

## Overview

The NPE wire protocol is the communication channel between the CNSC (Noetican Semantic Controller) and the NPE service. Security hardening has been implemented to ensure:

1. **Data Integrity**: Validating all requests and responses against JSON schemas
2. **Input Sanitization**: Preventing injection attacks through strict input validation
3. **Request Tracing**: Adding security headers for debugging and auditing
4. **Error Safety**: Sanitizing error messages to avoid information leakage
5. **Rate Limiting**: Preventing abuse through request rate controls

## Wire Protocol Security Considerations

### Protocol Version

The NPE wire protocol uses versioned schemas to ensure compatibility and prevent downgrade attacks:

- **Request Schema**: `npe_request.schema.json` (version 1.0.0)
- **Response Schema**: `npe_response.schema.json` (version 1.0.0)

All requests must include `spec_version: "1.0.0"` and responses are validated against the corresponding schema.

### Transport Security

While this implementation uses HTTP for local development, production deployments should:

1. Use HTTPS with TLS 1.2 or higher
2. Implement certificate pinning for NPE service verification
3. Use mutual TLS (mTLS) for bidirectional authentication

### Request Fields Security

| Field | Security Consideration |
|-------|----------------------|
| `request_id` | Must be unique per request; UUID, SHA-256, or timestamp-based format |
| `timestamp` | ISO 8601 format with timezone; prevents replay attacks with freshness checks |
| `domain` | Validated against allowed domains; prevents domain spoofing |
| `candidate_type` | Validated against allowed types; prevents injection |
| `budget` | Constrained to reasonable limits; prevents resource exhaustion |
| `context` | Validated against schema; arbitrary additional properties allowed |

## Validation Rules

### Domain Validation

```python
- Must be a non-empty string
- Maximum length: 64 characters
- Allowed characters: alphanumeric, underscore, hyphen
- Must be one of: "gr", "default"
```

### Candidate Type Validation

```python
- Must be a non-empty string
- Maximum length: 64 characters
- Allowed characters: alphanumeric, underscore, hyphen
- Must be one of: "proposal", "repair", "explanation"
```

### Budget Validation

| Parameter | Minimum | Maximum | Type |
|-----------|---------|---------|------|
| `max_wall_ms` | 1 | 300,000 | integer |
| `max_candidates` | 1 | 100 | integer |
| `max_input_tokens` | 0 | 1,000,000 | integer |
| `max_output_tokens` | 0 | 100,000 | integer |

### Request ID Validation

The `request_id` field accepts three formats:

1. **UUID**: `550e8400-e29b-41d4-a716-446655440000`
2. **SHA-256 Hex**: `a1b2c3d4e5f6...` (64 hex characters)
3. **Timestamp-based**: `ts_1704067200` (prefixed with Unix timestamp)

### Determinism Tier Validation

```python
- Must be one of: "d0", "d1", "d2"
- d0: Best effort (non-deterministic)
- d1: Reproducible (same seed produces same results)
- d2: Deterministic (fully deterministic execution)
```

## Security Headers

All HTTP requests include the following security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Type` | `application/json` | Specifies JSON content type |
| `X-Request-ID` | UUID | Request tracing and correlation |
| `X-Client-Version` | `1.0.0` | Client version for compatibility |
| `X-Client` | `CNSC-ProposerClient` | Client identification |

## Error Handling Behavior

### Error Message Sanitization

Error messages are sanitized to prevent information leakage:

- Internal file paths are replaced with generic placeholders
- Sensitive system information is removed
- Message length is capped at 500 characters

Example:
```
# Before sanitization
Failed to connect to NPE service at http://localhost:8000: [Errno 111] Connection refused
  File "/workspaces/cnsc-haai/src/cnsc/haai/nsc/proposer_client.py", line 142, in _make_request

# After sanitization
Failed to connect to NPE service at http://localhost:8000: Connection refused
```

### Exception Hierarchy

```
ProposerClientError (base)
├── ConnectionError
├── TimeoutError
├── ValidationError (field, message)
├── SchemaValidationError (schema_path, message)
└── SecurityError
```

### Error Response Format

The NPE service returns errors in the following format:

```json
{
  "spec_version": "1.0.0",
  "status": "error",
  "error": {
    "code": "BUDGET_EXCEEDED",
    "message": "Request exceeded maximum wall-clock time budget",
    "details": {
      "requested_ms": 10000,
      "elapsed_ms": 10005,
      "candidates_generated": 3
    }
  }
}
```

## Rate Limiting

The client implements client-side rate limiting to prevent abuse:

| Parameter | Value |
|-----------|-------|
| Max requests per window | 100 |
| Window duration | 60 seconds |

When the rate limit is exceeded, a `SecurityError` is raised.

## Schema Validation

### Request Schema (`npe_request.schema.json`)

Required fields:
- `spec_version`: Must be "1.0.0"
- `request_id`: Unique request identifier
- `timestamp`: ISO 8601 timestamp
- `domain`: Valid domain string
- `candidate_type`: Valid candidate type string
- `budget`: Object with budget constraints

### Response Schema (`npe_response.schema.json`)

Required fields:
- `spec_version`: Must be "1.0.0"
- `status`: "success", "partial", or "error"
- `request_id`: Correlated with original request

Optional fields:
- `candidates`: Array of candidate objects (when status is success/partial)
- `error`: Error details (when status is error)
- `metadata`: Additional response metadata

## Security Best Practices

### 1. Always Validate Inputs

Never trust external input. All parameters must be validated before use:

```python
# Good practice
client._validate_domain(domain)
client._validate_candidate_type(candidate_type)
client._validate_budget(budget)

# Bad practice - using raw input
request_data["domain"] = domain  # No validation
```

### 2. Use Schema Validation

Validate all requests and responses against the schemas:

```python
# Validate request before sending
client._validate_request(request_data)

# Validate response after receiving
client._validate_response(response_data)
```

### 3. Sanitize Error Messages

Never expose internal details in error messages:

```python
# Good practice
sanitized_msg = self._sanitize_error_message(str(e))
raise ConnectionError(f"Connection failed: {sanitized_msg}")

# Bad practice - exposing internal details
raise ConnectionError(f"Connection failed: {str(e)}")
```

### 4. Use Security Headers

Always include security headers for tracing:

```python
headers = self._get_security_headers(request_id)
response = self.session.request(..., headers=headers)
```

### 5. Implement Rate Limiting

Protect against abuse with rate limiting:

```python
self._check_rate_limit()  # Before each request
```

## Future Security Enhancements

Potential future enhancements (out of scope for current implementation):

1. **Authentication**: JWT-based or OAuth2 authentication
2. **Message Signing**: HMAC signatures for request integrity
3. **Encryption**: Payload encryption for sensitive data
4. **Audit Logging**: Detailed request/response logging for compliance
5. **Circuit Breaker**: Prevent cascading failures

## References

- [JSON Schema Specification](https://json-schema.org/)
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [RFC 6750 - OAuth 2.0 Bearer Token Usage](https://tools.ietf.org/html/rfc6750)
