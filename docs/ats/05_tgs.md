# TGS (Temporal Governance System)

**Status**: Debug/Telemetry Only - NOT Consensus

> **⚠️ IMPORTANT**: TGS is a debug and telemetry system, NOT a consensus authority.
> **Consensus receipts are Coh/ATS receipts only.** See [ATS Definition](00_identity/ats_definition.md).

---

## Overview

The Temporal Governance System (TGS) provides temporal governance, debugging, and telemetry for cognitive state transitions. It is designed to track and visualize the system's behavior but is explicitly **NOT** part of the consensus layer.

## TGS vs ATS/Coh Consensus

| Aspect | ATS/Coh Consensus | TGS Telemetry |
|--------|------------------|---------------|
| **Receipt Type** | Coh/ATS Receipts | TGSReceipt |
| **Serialization** | RFC8785 JCS | Standard JSON |
| **Chain Hash** | `COH_CHAIN_V1\n` domain | None |
| **Merkle Root** | Yes | No |
| **Retention Policy** | Enforced | Not applicable |
| **Fraud Proofs** | Supported | Not supported |

## Why TGS is Not Consensus

1. **No Merkle Commitment**: TGS receipts are not Merkle-hashed into slabs
2. **No JCS Serialization**: TGS uses JSON, not RFC8785 JCS  
3. **No Chain Hash**: TGS receipts do not participate in the universal chain hash
4. **No Slab Integration**: TGS data is not subject to retention policies
5. **No Fraud Proofs**: TGS disputes are not handled via the ATS dispute mechanism

## Components

### Clock System (`clock.py`)

Manages temporal governance through various clock types:

| Clock | Purpose |
|-------|---------|
| ConsistencyClock | Measures contradiction risk |
| CommitmentClock | Measures obligation load |
| CausalityClock | Enforces temporal ordering |
| ResourceClock | Limits based on budgets |
| TaintClock | Penalizes untrusted input |
| DriftClock | Measures coherence drift |

### Governor (`governor.py`)

Main governance engine that processes proposals and enforces coherence rails.

### Snapshot System (`snapshot.py`)

State snapshot management for TGS operations:
- `begin_attempt_snapshot()` - Create immutable snapshot
- `rollback()` - Restore state
- `commit()` - Finalize state changes

### Proposal System (`proposal.py`)

Proposal validation and processing:
- Proposal creation and validation
- Delta computation
- Resource checking

### Coherence Rails (`rails.py`)

Enforces coherence constraints:
- Consistency rail
- Taint rail
- Resource rail

### Ledger (`ledger.py`)

Storage and retrieval of TGS receipts (debug/telemetry only).

### Receipt System (`receipt.py`)

TGS receipt emission for debugging and telemetry.

## Usage

```python
from cnsc.haai.tgs import TGSGovernor, ClockRegistry, Proposal

# Create governor
governor = TGSGovernor()

# Process proposal (for debugging)
proposal = Proposal(...)
result = governor.process_proposal(proposal)
```

## Migration Note

Any legacy code that treats TGS ledger as authoritative should be redirected to use ATS receipts for consensus purposes.

## References

- [ATS Definition](00_identity/ats_definition.md)
- [Chain Hash Universal](20_coh_kernel/chain_hash_universal.md)
- [Coh Merkle v1](20_coh_kernel/coh.merkle.v1.md)
- [TGS Implementation Plan](../../plans/TGS_Build_Integration_Plan.md)
