# Adversary Model

**Threat Model for ATS Security**

| Field | Value |
|-------|-------|
| **Module** | 50_security_model |
| **Section** | Adversary Model |
| **Version** | 1.0.0 |

---

## 1. Security Assumptions

### 1.1 The Sovereignty Principle

> **The Receipt Verifier is sovereign. The Runtime is untrusted.**

This is the foundational security assumption. All verification is done independently by the RV.

### 1.2 Trusted Components

| Component | Trust Level |
|-----------|-------------|
| **ATS Kernel (RV)** | Fully trusted |
| **Deterministic Domain** | Fully trusted |
| **Serialization** | Fully trusted |

### 1.3 Untrusted Components

| Component | Trust Level |
|-----------|-------------|
| **Runtime** | Untrusted |
| **N Untrusted |
|SC VM** | **Policy** | Untrusted |
| **External Input** | Untrusted |

---

## 2. Threat Model

### 2.1 Threat Categories

| Category | Description | Mitigation |
|----------|-------------|------------|
| **T1** | Malicious runtime | Receipt verification |
| **T2** | Tampered receipt | Hash validation |
| **T3** | Replay attack | Chain verification |
| **T4** | Non-deterministic execution | State hash mismatch detection |
| **T5** | Budget manipulation | Independent computation |

### 2.2 Attack Vectors

```
┌─────────────────────────────────────────────────────┐
│                    ATTACKER                          │
│                                                      │
│  ┌─────────┐  ┌──────────┐  ┌─────────────────┐   │
│  │Runtime  │  │Receipt   │  │Trajectory       │   │
│  │Compromise│ │Forgery  │  │Replay           │   │
│  └────┬────┘  └────┬─────┘  └────────┬────────┘   │
│       │             │                   │            │
│       └─────────────┼───────────────────┘            │
│                     │                                │
│                     ▼                                │
│       ┌─────────────────────────┐                   │
│       │      ATS Kernel         │                   │
│       │   (Sovereign Verifier)  │                   │
│       └─────────────────────────┘                   │
└─────────────────────────────────────────────────────┘
```

---

## 3. Adversary Capabilities

### 3.1 What the Adversary Can Do

| Capability | Description |
|------------|-------------|
| **Modify execution** | Runtime can execute any computation |
| **Forge receipts** | Can create fake receipts |
| **Skip verification** | Can attempt to bypass RV |
| **Manipulate state** | Can provide false state data |
| **Replay old receipts** | Can replay past trajectories |

### 3.2 What the Adversary Cannot Do

| Capability | Description |
|------------|-------------|
| **Forge RV verification** | Cannot fake ACCEPT from RV |
| **Break hashing** | Cannot reverse SHA-256 |
| **Bypass deterministic checks** | Hash mismatch detected |
| **Manipulate budget law** | Kernel recomputes independently |

---

## 4. Security Properties

### 4.1 Properties Ensured by ATS

| Property | Description |
|----------|-------------|
| **Integrity** | Receipts cannot be tampered |
| **Authenticity** | Receipts verified independently |
| **Non-replay** | Old trajectories rejected |
| **Determinism** | Non-determinism detected |
| **Budget safety** | Budget law enforced |

### 4.2 Property Mappings

| Threat | Security Property | ATS Mechanism |
|--------|------------------|---------------|
| T1 | Integrity | Receipt hash verification |
| T2 | Authenticity | Chain hash validation |
| T3 | Non-replay | Chain linkage verification |
| T4 | Determinism | State hash comparison |
| T5 | Budget safety | Independent budget recomputation |

---

## 5. References

- [Coh Kernel Scope](../00_identity/coh_kernel_scope.md)
- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Deterministic Replay Requirements](./deterministic_replay_requirements.md)
- [Float Prohibition](./float_prohibition.md)
