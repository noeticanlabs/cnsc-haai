# Appendix C: Receipt Schema Reference

**Complete JSON Schema and Examples for All Receipt Types**

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
          "enum": ["gate_validation", "phase_transition", "recovery_action", "manual_annotation"]
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
  "receipt_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:30:00Z",
  "episode_id": "660e8400-e29b-41d4-a716-446655440000",
  "content": {
    "step_type": "gate_validation",
    "input_state": "sha256:abc123...",
    "output_state": "sha256:def456...",
    "decision": "PASS",
    "details": {
      "gate_type": "evidence_sufficiency",
      "threshold": 0.95,
      "measured_value": 0.97
    }
  },
  "provenance": {
    "parent_receipts": ["440e8400-e29b-41d4-a716-446655440000"],
    "evidence_references": ["urn:evidence:patient-123"]
  },
  "signature": {
    "algorithm": "Ed25519",
    "signer": "system-key-001",
    "signature": "base64signaturestring..."
  }
}
```

### Phase Transition Receipt

```json
{
  "version": "1.0.0",
  "receipt_id": "770e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:35:00Z",
  "episode_id": "660e8400-e29b-41d4-a716-446655440000",
  "content": {
    "step_type": "phase_transition",
    "input_state": "sha256:ghi789...",
    "output_state": "sha256:jkl012...",
    "decision": "PASS",
    "details": {
      "from_phase": "reasoning",
      "to_phase": "validation",
      "duration_ms": 5000,
      "steps_completed": 42
    }
  },
  "provenance": {
    "parent_receipts": ["660e8400-e29b-41d4-a716-446655440001"],
    "evidence_references": []
  },
  "signature": {
    "algorithm": "Ed25519",
    "signer": "system-key-001",
    "signature": "base64signaturestring..."
  }
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
