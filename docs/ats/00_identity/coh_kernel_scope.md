# Coh Kernel Scope

**What the Coh Kernel Governs and What It Does Not**

| Field | Value |
|-------|-------|
| **Module** | 00_identity |
| **Section** | Coh Kernel Scope |
| **Version** | 1.0.0 |

---

## 1. Kernel Boundary

The Coh kernel is the **verification layer** of the ATS. It sits between the hosted cognitive system and the execution environment, ensuring all state transitions satisfy the ATS invariants.

```
┌─────────────────────────────────────────────────────────────┐
│                    Execution Environment                     │
│                   (Untrusted Runtime)                         │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │ Untrusted execution
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      COH KERNEL                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  - Receipt Verification (RV)                           │  │
│  │  - Budget Law Enforcement                              │  │
│  │  - Deterministic Numeric Domain                        │  │
│  │  - Canonical Serialization                             │  │
│  │  - Chain Hash Validation                               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │ Verified actions only
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 Hosted Cognitive System                      │
│            (NSC / GML / GHLL / GLLL)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. What the Coh Kernel Governs

### 2.1 Deterministic Numeric Domain

| Concern | Kernel Action |
|---------|----------------|
| **Numeric Representation** | Enforces QFixed(18) or scaled int64 |
| **Rounding Rules** | Specifies deterministic rounding (truncate vs round-half-up) |
| **Overflow Behavior** | Defines overflow as rejection, not wrap-around |
| **Canonical Formatting** | All numbers serialize to canonical form |

### 2.2 Receipt Verification

| Concern | Kernel Action |
|---------|----------------|
| **State Hashing** | Recomputes sha256(state_bytes) |
| **Risk Delta** | Validates V(x_{k+1}) - V(x_k) computation |
| **Budget Law** | Enforces B_{k+1} = f(B_k, ΔV_k) |
| **Chain Integrity** | Validates receipt_id = first8(sha256(receipt_bytes)) |

### 2.3 Canonical Serialization

| Concern | Kernel Action |
|---------|----------------|
| **Byte Order** | Enforces big-endian serialization |
| **Type Tagging** | Includes type information in serialized form |
| **Ordering** | Dict keys sorted, list order preserved |
| **Versioning** | Includes schema version in canonical form |

### 2.4 Admissibility Enforcement

The kernel accepts or rejects each step:

```
ACCEPT:  All invariants satisfied
REJECT:  Deterministic error code (see rejection_reason_codes.md)
```

---

## 3. What the Coh Kernel Does NOT Govern

### 3.1 Physics and Computation

| Excluded | Reason |
|----------|--------|
| **Physical Laws** | The kernel does not simulate physics |
| **Computation Logic** | The hosted system computes whatever it wants |
| **Algorithm Choice** | NSC programs can use any algorithm |
| **Data Content** | The kernel verifies structure, not semantics |

### 3.2 Runtime Concerns

| Excluded | Reason |
|----------|--------|
| **Timing** | No timestamps in consensus (only step indices) |
| **Network** | No network protocol is enforced |
| **Storage** | Storage backend is unspecified |
| **Concurrency** | Single-threaded deterministic execution |

### 3.3 External Systems

| Excluded | Reason |
|----------|--------|
| **User Input** | External input is treated as untrusted oracle |
| **Third-Party APIs** | Not governed — only receipt verification |
| **Hardware** | Assumes deterministic execution hardware |

---

## 4. The Sovereignty Principle

> **The Receipt Verifier is sovereign. The Runtime is untrusted.**

This is the foundational security assumption:

1. **Verification is deterministic** — same inputs always produce same output
2. **Runtime can be malicious** — kernel validates all claims
3. **No trust required** — every step is independently verifiable
4. **Fail-secure** — any verification failure results in rejection

---

## 5. Kernel Interfaces

### 5.1 Input Interface (Untrusted → Kernel)

```
VerifyStep(
    state_before: bytes,
    state_after: bytes,
    action: bytes,
    receipt: Receipt,
    budget_before: QFixed,
    budget_after: QFixed,
) → ACCEPT | REJECT(code)
```

### 5.2 Output Interface (Kernel → Untrusted)

```
ACCEPT:
    receipt_id: 8-char-hex
    state_hash_after: sha256
    budget_after: QFixed

REJECT(code):
    error_code: enum
    reason: string
    diagnostic: optional bytes
```

---

## 6. References

- [Project Identity](./project_identity.md)
- [ATS Definition](./ats_definition.md)
- [Deterministic Numeric Domain](../20_coh_kernel/deterministic_numeric_domain.md)
- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Security Model](../50_security_model/adversary_model.md)
