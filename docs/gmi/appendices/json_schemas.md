# Appendix: JSON Schemas

## State Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "world_model": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "items": {"type": "string", "pattern": "^-?[0-9]+$"}
      }
    },
    "memory": {
      "type": "array",
      "items": {"type": ["string", "null"]}
    },
    "budget": {
      "type": "array",
      "items": {"type": "string", "pattern": "^-?[0-9]+$"},
      "minItems": 1
    },
    "chain_tip": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$"
    }
  },
  "required": ["world_model", "memory", "budget", "chain_tip"]
}
```

## Proposal Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "candidate_id": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$"
    },
    "payload": {"type": "object"},
    "required_witness_fields": {
      "type": "array",
      "items": {"type": "string"}
    },
    "predicted_cost": {
      "type": "string",
      "pattern": "^-?[0-9]+$"
    },
    "source_tag": {"type": "string"}
  },
  "required": ["candidate_id", "payload", "required_witness_fields"]
}
```

## Receipt Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^v[0-9]+$"
    },
    "decision_record_hash": {"type": "string"},
    "pre_state_hash": {"type": "string"},
    "post_state_hash": {"type": "string"},
    "work_spent": {
      "type": "array",
      "items": {"type": "string"}
    },
    "merkle_root": {"type": "string"},
    "parent_chain_tip": {"type": "string"},
    "new_chain_tip": {"type": "string"}
  },
  "required": ["version", "pre_state_hash", "post_state_hash", "new_chain_tip"]
}
```

## DecisionRecord Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "accepted": {
      "type": "array",
      "items": {"type": "string"}
    },
    "rejected": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "candidate_id": {"type": "string"},
          "reason": {
            "type": "string",
            "enum": ["REJECT_SCHEMA", "REJECT_WITNESS", "REJECT_CYCLE", "REJECT_POLICY", "REJECT_BUDGET"]
          }
        }
      }
    }
  },
  "required": ["accepted", "rejected"]
}
```
