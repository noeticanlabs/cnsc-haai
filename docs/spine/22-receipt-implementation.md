# Module 22: Receipt Implementation

**Practical Implementation of the Receipt System**

| Field | Value |
|-------|-------|
| **Module** | 22 |
| **Version** | 1.0.0 |
| **Lines** | ~650 |
| **Prerequisites** | Module 21 |

---

## Table of Contents

1. Implementation Fundamentals
2. Receipt Schema
3. Implementation Patterns
4. Storage Implementation
5. Verification Implementation
6. Performance Optimization
7. Testing Receipts
8. Deployment and Operations
9. Troubleshooting Guide
10. References and Further Reading

---

## 1. Implementation Fundamentals

### 1.1 Implementation Requirements

| Requirement | Description |
|-------------|-------------|
| **Atomicity** | Receipt creation is atomic |
| **Durability** | Once created, receipts persist |
| **Immutability** | Receipts cannot be modified |
| **Linkability** | Receipts can be chained |

### 1.2 Implementation Components

```python
class ReceiptSystem:
    def __init__(self, config):
        self.emitter = ReceiptEmitter(config.emitter)
        self.storage = ReceiptStorage(config.storage)
        self.verifier = ReceiptVerifier(config.verifier)
```

---

## 2. Receipt Schema

### 2.1 Schema Definition

```python
receipt_schema = {
    "type": "object",
    "properties": {
        "version": {"type": "string", "enum": ["1.0.0"]},
        "receipt_id": {"type": "string", "format": "uuid"},
        "timestamp": {"type": "string", "format": "date-time"},
        "episode_id": {"type": "string", "format": "uuid"},
        "content": {
            "type": "object",
            "properties": {
                "step_type": {"type": "string"},
                "input_state": {"type": "string"},
                "output_state": {"type": "string"},
                "decision": {"type": "string", "enum": ["PASS", "FAIL", "WARN"]}
            }
        },
        "provenance": {
            "type": "object",
            "properties": {
                "parent_receipts": {"type": "array", "items": {"type": "string"}},
                "evidence_references": {"type": "array", "items": {"type": "string"}}
            }
        },
        "signature": {
            "type": "object",
            "properties": {
                "algorithm": {"type": "string"},
                "signer": {"type": "string"},
                "signature": {"type": "string"}
            }
        }
    },
    "required": ["version", "receipt_id", "timestamp", "content", "signature"]
}
```

### 2.2 Schema Validation

```python
def validate_receipt(receipt):
    jsonschema.validate(receipt, receipt_schema)
    if not verify_receipt_structure(receipt):
        raise ValidationError("Invalid receipt structure")
```

---

## 3. Implementation Patterns

### 3.1 Basic Receipt Pattern

```python
class ReceiptEmitter:
    def emit(self, step_type, input_state, output_state, decision, evidence):
        receipt_id = generate_uuid()
        timestamp = get_current_time()
        
        receipt = {
            "version": "1.0.0",
            "receipt_id": receipt_id,
            "timestamp": timestamp,
            "episode_id": self.current_episode,
            "content": {
                "step_type": step_type,
                "input_state": hash_state(input_state),
                "output_state": hash_state(output_state),
                "decision": decision
            },
            "provenance": {
                "parent_receipts": self.get_parent_receipts(),
                "evidence_references": evidence
            },
            "signature": self.sign(receipt_id + timestamp + content)
        }
        
        self.storage.store(receipt)
        return receipt
```

### 3.2 Chain Receipt Pattern

```python
class ChainReceiptEmitter(ReceiptEmitter):
    def __init__(self, config):
        super().__init__(config)
        self.last_receipt_id = None
        
    def emit(self, step_type, input_state, output_state, decision, evidence):
        parent_receipts = []
        if self.last_receipt_id:
            parent_receipts = [self.last_receipt_id]
            
        receipt = super().emit(step_type, input_state, output_state, decision, 
                              evidence + parent_receipts)
        
        self.last_receipt_id = receipt["receipt_id"]
        return receipt
```

---

## 4. Storage Implementation

### 4.1 Storage Backends

```python
class ReceiptStorage:
    def store(self, receipt):
        raise NotImplementedError
        
class LocalFileStorage(ReceiptStorage):
    def __init__(self, base_path):
        self.base_path = base_path
        
    def store(self, receipt):
        path = f"{self.base_path}/{receipt['receipt_id']}.json"
        with open(path, 'w') as f:
            json.dump(receipt, f)

class DatabaseStorage(ReceiptStorage):
    def __init__(self, connection_string):
        self.db = create_connection(connection_string)
        
    def store(self, receipt):
        self.db.receipts.insert(receipt)
```

### 4.2 Indexing

```python
class IndexedStorage(ReceiptStorage):
    def __init__(self, base_storage):
        self.base = base_storage
        self.indexes = {
            "by_episode": {},
            "by_timestamp": {},
            "by_type": {}
        }
        
    def store(self, receipt):
        self.base.store(receipt)
        self._update_indexes(receipt)
```

---

## 5. Verification Implementation

### 5.1 Signature Verification

```python
class ReceiptVerifier:
    def __init__(self, public_keys):
        self.public_keys = public_keys
        
    def verify_signature(self, receipt):
        signer = receipt["signature"]["signer"]
        signature = receipt["signature"]["signature"]
        algorithm = receipt["signature"]["algorithm"]
        
        public_key = self.public_keys[signer]
        data = self._get_signable_data(receipt)
        
        return verify_signature(public_key, data, signature, algorithm)
```

### 5.2 Chain Verification

```python
class ChainVerifier:
    def verify_chain(self, receipts):
        if not receipts:
            return True
            
        for i in range(1, len(receipts)):
            if receipts[i]["receipt_id"] not in receipts[i-1]["provenance"]["parent_receipts"]:
                return False
                
        return True
```

---

## 6. Performance Optimization

### 6.1 Batching

```python
class BatchedEmitter:
    def __init__(self, base_emitter, batch_size=100):
        self.base = base_emitter
        self.batch_size = batch_size
        self.buffer = []
        
    def emit(self, step_type, input_state, output_state, decision, evidence):
        self.buffer.append((step_type, input_state, output_state, decision, evidence))
        if len(self.buffer) >= self.batch_size:
            self._flush()
            
    def _flush(self):
        for item in self.buffer:
            self.base.emit(*item)
        self.buffer = []
```

### 6.2 Compression

```yaml
compression:
  algorithm: "zstd"
  level: 3
  threshold: "receipts > 1KB"
```

---

## 7. Testing Receipts

### 7.1 Unit Testing

```python
def test_receipt_emission():
    emitter = ReceiptEmitter(config)
    receipt = emitter.emit("test", state1, state2, "PASS", [])
    
    assert receipt["receipt_id"] is not None
    assert receipt["version"] == "1.0.0"
    assert receipt["content"]["decision"] == "PASS"
```

### 7.2 Integration Testing

```python
def test_receipt_system():
    system = ReceiptSystem(config)
    
    # Emit receipts
    r1 = system.emit("step1", s1, s2, "PASS", [])
    r2 = system.emit("step2", s2, s3, "PASS", [r1["receipt_id"]])
    
    # Verify chain
    assert system.verifier.verify_chain([r1, r2])
```

---

## 8. Deployment and Operations

### 8.1 Configuration

```yaml
receipt_system:
  storage:
    type: "database"
    connection: "postgresql://..."
  signing:
    algorithm: "Ed25519"
    key_id: "system_key_1"
  verification:
    cache_size: 10000
```

### 8.2 Monitoring

```python
class MonitoredReceiptSystem(ReceiptSystem):
    def emit(self, *args):
        start = time.time()
        result = super().emit(*args)
        duration = time.time() - start
        metrics.record("receipt_emit_duration", duration)
        return result
```

---

## 9. Troubleshooting Guide

### 9.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Verification Failure** | Wrong key | Update key store |
| **Storage Error** | Disk full | Clean up old receipts |
| **Performance Issue** | No indexing | Add indexes |

### 9.2 Debugging Procedures

```yaml
debugging:
  steps:
    - "enable_verbose_logging"
    - "check_receipt_integrity"
    - "verify_storage_health"
    - "check_signature_keys"
```

---

## 10. References and Further Reading

### Primary Sources

1. Noetican Labs. "Receipt Implementation Guide." 2024.
2. Noetican Labs. "Testing Framework for Receipts." 2024.
3. Noetican Labs. "Deployment Best Practices." 2024.

### Software Engineering

4. Fowler, M. "Patterns of Enterprise Application Architecture." 2002.
5. Nygard, M. "Release It!" 2007.

---

## Previous Module

[Module 21: Receipt System](21-receipt-system.md)

## Next Module

[Module 23: Learning Under Coherence](23-learning-under-coherence.md)

---

## Version Information

| Component | Version |
|-----------|---------|
| Module | 22-receipt-implementation |
| Version | 1.0.0 |
| Updated | 2024-01-01 |
| Status | Canonical |
