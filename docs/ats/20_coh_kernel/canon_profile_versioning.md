# Canon Profile Versioning

**Schema and Policy Version Freeze Rules**

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | Canon Profile Versioning |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |
| **Revised** | 2026-02-23 |

---

## 1. Overview

This document defines the rules for when schema and policy changes require a version bump in the canon profile. This protects against silent breakage during upgrades.

---

## 2. Versioned Fields

### 2.1 Schema ID

```
schema_id: "coh.receipt.v1.0.0"
```

Identifies the receipt schema version.

### 2.2 Policy Hash

```
policy_hash: "sha256:..."
```

Hash of the policy configuration used for this slab.

### 2.3 Canon Profile Hash

```
canon_profile_hash: "sha256:..."
```

Hash of the canonical profile (schema + policy + rules).

---

## 3. Version Bump Rules

| Change Type | Requires Version Bump? | Example |
|-------------|----------------------|---------|
| **Hash domain tag change** | ✅ YES | Adding new `COH_*` prefix |
| **JSON key rename** | ✅ YES | `chain_hash` → `chain_digest` |
| **New required field** | ✅ YES | Adding mandatory `policy_id` |
| **New reject code** | ✅ YES | Adding `REJECT_UNKNOWN_ACTION` |
| **New optional field** | ❌ NO | Adding `metadata: {}` |
| **Documentation-only** | ❌ NO | Fixing typos |
| **Comment changes** | ❌ NO | Adding internal comments |
| **Formatting changes** | ❌ NO | Indentation/whitespace |

---

## 4. Version Numbering

### 4.1 Format

```
major.minor.patch
```

- **major**: Breaking changes (incompatible with previous)
- **minor**: New features (backward compatible)
- **patch**: Bug fixes (backward compatible)

### 4.2 When to Bump Major

Major version MUST be bumped when:
1. Removing a required field
2. Changing hash algorithm
3. Changing serialization format
4. Changing domain separator

### 4.3 When to Bump Minor

Minor version SHOULD be bumped when:
1. Adding new optional field
2. Adding new reject code
3. Adding new policy parameter

---

## 5. Migration Path

### 5.1 Version Compatibility Matrix

| From \ To | v1.0.0 | v1.1.0 | v2.0.0 |
|-----------|--------|--------|--------|
| v1.0.0 | ✅ | ✅ | ❌ |
| v1.1.0 | ❌ | ✅ | ❌ |
| v2.0.0 | ❌ | ❌ | ✅ |

### 5.2 Migration Steps

When upgrading:

1. **Check schema_id**: Verify version compatibility
2. **Migrate fields**: Transform deprecated fields to new format
3. **Verify hashes**: Recompute policy_hash and canon_profile_hash
4. **Test**: Run compliance tests against new version

---

## 6. Enforcement

### 6.1 CI Requirements

- All PRs MUST check for version bump requirements
- Schema changes MUST include version bump in PR
- Test vectors MUST include version-specific cases

### 6.2 Rejection Codes

| Code | Description | Version |
|------|-------------|---------|
| `INCOMPATIBLE_SCHEMA` | Schema version mismatch | v1.0.0+ |
| `POLICY_HASH_MISMATCH` | Policy hash doesn't match | v1.0.0+ |
| `PROFILE_HASH_MISMATCH` | Canon profile hash mismatch | v1.0.0+ |

---

## 7. References

- [Receipt Schema](./receipt_schema.md)
- [Chain Hash Universal](./chain_hash_universal.md)
- [Slab Compression Rules](../30_ats_runtime/slab_compression_rules.md)
