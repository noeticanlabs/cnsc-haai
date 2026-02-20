# Consensus Upgrade Checklist

**Purpose**: Checklist for reviewers to verify consensus-tight implementation

---

## Pre-Merge Checklist

Before merging any PR that affects consensus, verify:

### 1. JCS Enforcement
- [ ] All serialization uses RFC8785 JCS
- [ ] No custom canonicalization
- [ ] `jcs_canonical_bytes()` used for all hash inputs

### 2. Domain Separation
- [ ] Chain hashing uses `COH_CHAIN_V1\n` domain
- [ ] Merkle uses proper prefixes (`0x01` for leaf/internal)
- [ ] No raw concatenation without domain

### 3. SHA256 Prefix Rule
- [ ] All JSON digests use `sha256:` prefix
- [ ] Internal decoding handles prefix correctly
- [ ] Schemas enforce `sha256:` pattern

### 4. Slab FSM
- [ ] `slab_accept_height` derived correctly
- [ ] `disputed_flag` blocks finalize
- [ ] `window_end_height` verified before deletion

### 5. Micro Codec
- [ ] Micro leaf codec ID defined
- [ ] Codec encodes using JCS UTF-8
- [ ] Fraud proofs use correct codec

---

## Schema Versioning

| Version | Chain Rule | Digest Format | Status |
|---------|------------|--------------|--------|
| v2 | sha256(prev\|\|curr) | bare hex | FROZEN |
| v3 | sha256(sha256(COH_CHAIN_V1\|\|JCS)) | sha256: prefix | ACTIVE |

---

## Test Vector Requirements

All consensus changes MUST include:

1. **Input**: Test input data
2. **Expected Output**: Known-good output
3. **Deterministic**: Same input → same output
4. **Format**: JSON or JSONL

---

## Common Pitfalls

| Pitfall | How to Avoid |
|---------|---------------|
| Using v2 chain rule | Use `chain_hash_universal.md` |
| Bare hex digests | Use `sha256:` prefix |
| Custom serialization | Use JCS RFC8785 |
| Float in consensus | Use QFixed |
| Wrong coherence module | Use `cnsc.haai.ats.risk` |

---

## Related Documents

- [Chain Hash Universal](../20_coh_kernel/chain_hash_universal.md)
- [Coh Merkle v1](../20_coh_kernel/coh.merkle.v1.md)
- [Spec Governance](../00_identity/spec_governance.md)
- [Spec to Code Map](../01_spec_to_code_map.md)
