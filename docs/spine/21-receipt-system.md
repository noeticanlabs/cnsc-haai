# Module 21: Receipt System

**Theory of the Receipt System for Auditability**

| Field | Value |
|-------|-------|
| **Module** | 21 |
| **Version** | 1.0.0 |
| **Lines** | ~700 |
| **Prerequisites** | Module 20 |

---

## Table of Contents

1. Receipt Fundamentals
2. Receipt Architecture
3. Receipt Emission
4. Receipt Verification
5. Receipt Storage
6. Receipt Security
7. Receipt Examples
8. Advanced Topics
9. References and Further Reading

---

## 1. Receipt Fundamentals

### 1.1 What is a Receipt

A **receipt** is a cryptographic record of a reasoning step that enables auditability and verification.

### 1.2 Receipt Properties

| Property | Description |
|----------|-------------|
| **Completeness** | Captures all relevant information |
| **Integrity** | Cannot be tampered with |
| **Traceability** | Links to other receipts |
| **Verifiability** | Can be independently verified |

### 1.3 Receipt Functions

| Function | Description |
|----------|-------------|
| **Evidence** | Proves reasoning occurred |
| **Audit** | Enables inspection of reasoning |
| **Recovery** | Enables state reconstruction |
| **Attestation** | Provides third-party verification |

---

## 2. Receipt Architecture

### 2.1 Receipt Structure

> **Canonical Schema**: See [`schemas/receipt.schema.json`](../../../schemas/receipt.schema.json)

```yaml
receipt:
  version: "1.0.0"          # Schema version (required)
  receipt_id: "a1b2c3d4"    # 8-char hex identifier
  timestamp: "ISO8601"      # Creation timestamp
  episode_id: "e5f6g7h8"    # Episode identifier
  
  content:
    step_type: PARSE|TYPE_CHECK|GATE_EVAL|...  # Step type enum
    input_hash: "sha256:..." # Input state hash
    output_hash: "sha256:..." # Output state hash
    decision: PASS|FAIL|WARN|SKIP|PENDING  # Decision
    details: {}              # Step-specific metadata
    coherence_before: 0.92   # Pre-step coherence (optional)
    coherence_after: 0.94    # Post-step coherence (optional)
    
  provenance:
    source: "nsc-vm"         # Source component
    phase: "execution"       # Execution phase
    span: {...}              # Provenance span (optional)
    
  signature:
    algorithm: HMAC-SHA256|Ed25519|ECDSA|RSA
    signer: "system-key-001" # Key/certificate ID
    signature: "base64..."   # Signature
  
  # Chain fields
  previous_receipt_id: "9i8j7k6l"
  previous_receipt_hash: "sha256:..."
  chain_hash: "sha256:..."    # Chain hash
  metadata: {}               # Extensibility
```

### 2.2 Receipt Types

| Type | Purpose | Content |
|------|---------|---------|
| **Step Receipt** | Individual reasoning step | Input/output/decision |
| **Phase Receipt** | Phase completion | Summary of phase |
| **Episode Receipt** | Full episode | Complete trace |
| **Recovery Receipt** | Recovery action | Before/after state |

---

## 3. Receipt Emission

### 3.1 Emission Triggers

| Trigger | Description |
|---------|-------------|
| **Gate Evaluation** | After gate decision |
| **Phase Transition** | When phase ends |
| **Recovery Action** | When recovery occurs |
| **Manual Trigger** | Explicit request |

### 3.2 Emission Timing

| Timing | Description |
|--------|-------------|
| **Immediate** | As soon as step completes |
| **Batched** | After batch of steps |
| **Buffered** | At phase end |

---

## 4. Receipt Verification

### 4.1 Verification Methods

| Method | Description |
|--------|-------------|
| **Signature Verification** | Check cryptographic signature |
| **Chain Verification** | Verify receipt chain integrity |
| **State Verification** | Verify state consistency |
| **Temporal Verification** | Verify timestamp order |

### 4.2 Verification Protocols

```yaml
verification_protocol:
  steps:
    - "verify_signature"
    - "verify_chain"
    - "verify_state"
    - "verify_temporal_order"
  result: "valid|invalid|uncertain"
```

---

## 5. Receipt Storage

### 5.1 Storage Strategies

| Strategy | Description |
|----------|-------------|
| **Local** | Store locally |
| **Distributed** | Replicate across nodes |
| **Archive** | Long-term cold storage |

### 5.2 Retrieval Methods

| Method | Description |
|--------|-------------|
| **By ID** | Direct lookup |
| **By Episode** | All receipts in episode |
| **By Time** | Receipts in time range |
| **By Content** | Content-based search |

---

## 6. Receipt Security

### 6.1 Integrity Protection

```yaml
integrity_protection:
  mechanisms:
    - "digital_signature"
    - "hash_chain"
    - "merkle_tree"
  algorithms:
    - "Ed25519"  # Signing
    - "SHA-256"  # Hashing
```

### 6.2 Confidentiality

```yaml
confidentiality:
  encryption: "AES-256"
  access_control: "role_based"
  anonymization: "optional"
```

### 6.3 Access Control

| Role | Access |
|------|--------|
| **System** | Write only |
| **Auditor** | Read only |
| **Admin** | Read/write |
| **Owner** | Full control |

---

## 7. Receipt Examples

### 7.1 Gate Validation Receipt

```yaml
example:
  type: "gate_validation"
  gate: "evidence_sufficiency"
  input: "abstraction_state_v1"
  output: "abstraction_state_v2"
  decision: "PASS"
  evidence: ["patient_record_123"]
```

### 7.2 Phase Completion Receipt

```yaml
example:
  type: "phase_completion"
  phase: "reasoning"
  duration_ms: 5000
  steps: 42
  coherence_score: 0.98
  next_phase: "validation"
```

---

## 8. Advanced Topics

### 8.1 Privacy-Preserving Receipts

```yaml
privacy_receipts:
  technique: "zero_knowledge_proof"
  purpose: "prove_validity_without_revealing_content"
  use_cases:
    - "compliance_verification"
    - "third_party_audit"
```

### 8.2 Scalable Receipt Systems

```yaml
scalability:
  techniques:
    - "sharding"
    - "caching"
    - "compression"
  throughput: "100000 receipts/second"
```

---

## 9. References and Further Reading

### Primary Sources

1. Noetican Labs. "Receipt System Specification." 2024.
2. Noetican Labs. "Receipt Security Framework." 2024.
3. Noetican Labs. "Verification Protocol." 2024.

### Cryptography

4. Katz, J. and Lindell, Y. "Introduction to Modern Cryptography." 2014.
5. Merkle, R. "A Digital Signature Based on a Conventional Encryption Function." 1987.

---

## Previous Module

[Module 20: Memory Models](20-memory-models.md)

## Next Module

[Module 22: Receipt Implementation](22-receipt-implementation.md)

---

## Version Information

| Component | Version |
|-----------|---------|
| Module | 21-receipt-system |
| Version | 1.0.0 |
| Updated | 2024-01-01 |
| Status | Canonical |
