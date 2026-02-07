# Appendix C: Receipt Schema Reference

> **Canonical Schema**: `schemas/receipt.schema.json` (v1.0.0)
> 
> This appendix provides detailed documentation and examples. The authoritative JSON Schema is at [`schemas/receipt.schema.json`](../../../schemas/receipt.schema.json).

**Complete JSON Schema and Examples for All Receipt Types**

## Schema Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial canonical schema |

## Receipt Schema (Version 1.0.0)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CNHAAI Receipt",
  "type": "object",
  "required": ["version", "receipt_id", "timestamp", "content", "signature"],
  "properties": {
    "version": {
      "type": "string",
      "enum": ["1.0.0"],
      "description": "Receipt schema version"
    },
    "receipt_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this receipt"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of receipt creation"
    },
    "episode_id": {
      "type": "string",
      "format": "uuid",
      "description": "ID of the reasoning episode"
    },
    "content": {
      "type": "object",
      "required": ["step_type"],
      "properties": {
        "step_type": {
          "type": "string",
          "enum": [
            "PARSE",
            "TYPE_CHECK",
            "GATE_EVAL",
            "PHASE_TRANSITION",
            "VM_EXECUTION",
            "COHERENCE_CHECK",
            "TRACE_EVENT",
            "CHECKPOINT",
            "REPLAY",
            "CUSTOM"
          ],
          "description": "Type of step that generated this receipt"
        },
        "input_state": {
          "type": "string",
          "description": "Hash of input state"
        },
        "output_state": {
          "type": "string",
          "description": "Hash of output state"
        },
        "decision": {
          "type": "string",
          "enum": ["PASS", "FAIL", "WARN", "SKIP"]
        },
        "details": {
          "type": "object",
          "description": "Step-specific details"
        }
      }
    },
    "provenance": {
      "type": "object",
      "properties": {
        "parent_receipts": {
          "type": "array",
          "items": { "type": "string", "format": "uuid" }
        },
        "evidence_references": {
          "type": "array",
          "items": { "type": "string", "format": "uri" }
        }
      }
    },
    "signature": {
      "type": "object",
      "required": ["algorithm", "signer", "signature"],
      "properties": {
        "algorithm": {
          "type": "string",
          "enum": ["Ed25519", "ECDSA", "RSA"]
        },
        "signer": {
          "type": "string",
          "description": "Certificate or key ID"
        },
        "signature": {
          "type": "string",
          "description": "Base64-encoded signature"
        }
      }
    }
  }
}
```

## Example Receipts

### Gate Validation Receipt

```json
{
  "version": "1.0.0",
  "receipt_id": "a1b2c3d4",
  "timestamp": "2024-01-15T10:30:00Z",
  "episode_id": "e5f6g7h8",
  "content": {
    "step_type": "GATE_EVAL",
    "input_hash": "sha256:abc123...",
    "output_hash": "sha256:def456...",
    "decision": "PASS",
    "details": {
      "gate_type": "evidence_sufficiency",
      "threshold": 0.95,
      "measured_value": 0.97
    },
    "coherence_before": 0.92,
    "coherence_after": 0.94
  },
  "provenance": {
    "source": "nsc-vm",
    "phase": "execution"
  },
  "signature": {
    "algorithm": "HMAC-SHA256",
    "signer": "system-key-001",
    "signature": "base64signaturestring..."
  },
  "previous_receipt_id": "9i8j7k6l",
  "previous_receipt_hash": "sha256:previous...",
  "chain_hash": "sha256:current..."
}
```

### Phase Transition Receipt

```json
{
  "version": "1.0.0",
  "receipt_id": "m3n4o5p6",
  "timestamp": "2024-01-15T10:35:00Z",
  "episode_id": "e5f6g7h8",
  "content": {
    "step_type": "PHASE_TRANSITION",
    "input_hash": "sha256:ghi789...",
    "output_hash": "sha256:jkl012...",
    "decision": "PASS",
    "details": {
      "from_phase": "reasoning",
      "to_phase": "validation",
      "duration_ms": 5000,
      "steps_completed": 42
    },
    "coherence_before": 0.94,
    "coherence_after": 0.96
  },
  "provenance": {
    "source": "phaseloom",
    "phase": "transition"
  },
  "signature": {
    "algorithm": "HMAC-SHA256",
    "signer": "system-key-001",
    "signature": "base64signaturestring..."
  },
  "previous_receipt_id": "a1b2c3d4",
  "previous_receipt_hash": "sha256:a1b2c3d4...",
  "chain_hash": "sha256:m3n4o5p6..."
}
```

---

## Version Information

| Component | Version |
|-----------|---------|
| Appendix | C-receipt-schema |
| Version | 1.0.0 |
| Updated | 2024-01-01 |
| Status | Canonical |
