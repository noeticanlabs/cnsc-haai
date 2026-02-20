# Receipts and Slabs

**Immutable Evidence and Batched Commitment**

## Micro Receipts

Each cognitive step produces a micro receipt containing:
- State hashes (before/after)
- Risk values (QFixed)
- Budget consumption
- Action details

## Slabs

Multiple micro receipts are batched into a slab:
- Merkle root commitment
- Minimal basis (B_end_q, V_max_q, M_max_int)
- Retention policy binding

## Chain Hash

All receipts use universal chain hashing:
- JCS (RFC8785) serialization
- Domain separator: `COH_CHAIN_V1\n`
- Raw 32-byte previous chain hash

See:
- [Chain Hash Universal](../ats/20_coh_kernel/chain_hash_universal.md)
- [Coh Merkle v1](../ats/20_coh_kernel/coh.merkle.v1.md)
- [Slab Compression Rules](../ats/30_ats_runtime/slab_compression_rules.md)
