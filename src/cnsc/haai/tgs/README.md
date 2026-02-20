# TGS (Temporal Governance System) - Debug/Telemetry

> **⚠️ DEPRECATED FOR CONSENSUS**: TGS is a debug and telemetry system, NOT a consensus authority.
>
> **Consensus receipts are Coh/ATS receipts only.** See [ATS Definition](../ats/00_identity/ats_definition.md).

---

## TGS Purpose

The Temporal Governance System (TGS) provides:

| Function | Consensus-Relevant |
|----------|-------------------|
| Clock management | ❌ Debug/telemetry only |
| State snapshots | ❌ Debug/telemetry only |
| Governance receipts | ❌ Debug/telemetry only |
| Ledger storage | ❌ Debug/telemetry only |

## Why TGS is Not Consensus

1. **No Merkle Commitment**: TGS receipts are not Merkle-hashed into slabs
2. **No JCS Serialization**: TGS uses JSON, not RFC8785 JCS
3. **No Chain Hash**: TGS receipts do not participate in the universal chain hash
4. **No Slab Integration**: TGS data is not subject to retention policies
5. **No Fraud Proofs**: TGS disputes are not handled via the ATS dispute mechanism

## Consensus vs Telemetry

| Aspect | ATS/Coh Consensus | TGS Telemetry |
|--------|------------------|---------------|
| Receipt Type | Coh/ATS Receipts | TGSReceipt |
| Serialization | RFC8785 JCS | Standard JSON |
| Chain Hash | `COH_CHAIN_V1\n` domain | None |
| Merkle Root | Yes | No |
| Retention Policy | Enforced | Not applicable |
| Fraud Proofs | Supported | Not supported |

## Migration Note

Any legacy code that treats TGS ledger as authoritative should be redirected to use ATS receipts for consensus purposes.

## References

- [ATS Definition](../ats/00_identity/ats_definition.md)
- [Chain Hash Universal](../ats/20_coh_kernel/chain_hash_universal.md)
- [Coh Merkle v1](../ats/20_coh_kernel/coh.merkle.v1.md)
