# ATS Slab Compliance Test Vector Bundle v1

This directory contains deterministic test vectors for verifying consensus-tight ATS slab implementation.

## Files

| File | Purpose |
|------|---------|
| `policy.json` | Canonical retention policy |
| `micro_receipts.jsonl` | 3 micro receipts for merkle root test |
| `expected_micro_merkle_root.txt` | Expected merkle root (sha256:) |
| `expected_slab_receipt.json` | Full STEP_SLAB receipt |
| `expected_chain_hash_sequence.txt` | Chain hash progression |
| `fraudproof_valid.json` | Valid directed merkle fraud proof |
| `finalize_valid.json` | Valid finalize after window |
| `finalize_reject_premature.json` | Rejected finalize (early) |

## Verification Requirements

Implementations MUST verify:
1. JCS canonicalization produces identical bytes
2. Chain hash sequence matches expected
3. Merkle root matches expected_micro_merkle_root
4. Fraud proof validates correctly
5. Premature finalize rejected
6. Valid finalize accepted
7. Slab with zero leaves rejected

## Schema Compatibility

- Receipts: `schemas/receipt.ats.v3.schema.json`
- Slab: `schemas/coh.receipt.slab.v1.schema.json`
- Policy: `schemas/coh.policy.retention.v1.schema.json`

## Deterministic Guarantee

If two independent implementations match all vectors bit-for-bit, they achieve true consensus.
