# NPE v1.0.1 Canonical Specification

**Status:** FROZEN (NPE v1.0.1)  
**Date:** 2026-02-21  
**Protocol Version:** 1.0.1

---

## 1. Overview

NPE (Novelty Proposal Engine) v1.0.1 is a deterministic, auditable proposal system for coherence-based search optimization. This specification locks the exact byte-level serialization, canonical hashing, arithmetic, and PRNG behavior needed for RV (Risk Validator) consensus verification.

### Design Principles

- **Deterministic**: Same inputs → byte-identical JCS → identical hashes (across platforms)
- **Auditable**: PRNG seeding is deterministic; all randomness is replayable
- **Canonical**: Single source of truth; no "mood," no drift in numeric formats
- **Fork-proof**: Binary envelope parsing has zero ambiguity; parser rejects unambiguously
- **RV-verifiable**: Proposals are verified locally before RCFA; no surprises at consensus

---

## 2. Numeric Domain: QFixed18

### 2.1 Representation

All numeric values in NPE proposals are **integers scaled by 2^18**.

- **Symbol**: Q18 fixed-point (signed 64-bit)
- **Range**: `[-2^63, 2^63 - 1]` (int64 bounds)
- **Minimum unit**: 1 (representing 2^-18 in "real" units)
- **No floats**: Float types are **forbidden** in all NPE serialization and arithmetic

### 2.2 Arithmetic

All arithmetic operations on Q18 values use deterministic rounding.

#### Multiplication: `q18_mul(a, b, rounding)`

```
result_full = a * b  (computed in int128 or equivalent)
result_scaled = result_full >> 18  (remove scaling)

if rounding == UP:
    if (result_full & 0x3FFFF) != 0:  # Has fractional part
        result_scaled += 1
```

**Debit Calculation** (UP rounding):
```
debit = q18_mul(kappa, cost, UP)
   = ceil((kappa * cost) / 2^18)
```

#### Division: `q18_div(a, b, rounding)`

```
result_full = (a << 18) / b  (add scaling, then divide)

if rounding == DOWN:
    # Floor division is default
    result = result_full
```

**Refund Calculation** (DOWN rounding):
```
refund = q18_div(rho * amount, 1, DOWN)
      = floor((rho * amount) / 2^18)
```

### 2.3 Bounds & Overflow

- **Overflow Check**: All operations reject if result falls outside int64 range
- **Underflow Check**: Reject if intermediate computation overflows int128 (on 64-bit systems)
- **Clamping**: No silent wrapping; always fail loudly with deterministic error code

---

## 3. Canonical Serialization: RFC8785 JCS

### 3.1 JSON Canonicalization Scheme (RFC8785)

All NPE objects are serialized to canonical JSON bytes using RFC8785 rules:

1. **UTF-8 Encoding**: All strings in UTF-8
2. **Key Ordering**: Object keys sorted lexicographically (byte order)
3. **No Whitespace**: No spaces, newlines, or extra separators
4. **Canonical Numbers**: 
   - Integers: decimal representation, no leading zeros (except "0")
   - **Floats: FORBIDDEN** — only integers allowed in canonicalization
5. **Array Order**: Preserved as-is
6. **Null/Boolean/String**: Standard JSON representation

### 3.2 Canonical Bytes

```
jcs_bytes(proposal) = utf8.encode(
    json.dumps(proposal, separators=(',', ':'), sort_keys=True, ensure_ascii=True)
)
```

**Example:**

```json
{
  "domain_separator": "NPE|1.0.1",
  "proposal_type": "RENORM_QUOTIENT",
  "kappa": 262144,
  "rho": 131072
}
```

Canonicalizes to (no spaces):
```
{"domain_separator":"NPE|1.0.1","kappa":262144,"proposal_type":"RENORM_QUOTIENT","rho":131072}
```

### 3.3 Hash Domain Separation

All hashes use domain-separated prefixes:

```
proposal_hash = sha256(jcs_bytes(proposal_envelope))
delta_hash = sha256(raw_delta_bytes)  (after base64 decode)
cert_hash = sha256(cert_bytes_for_hash)  (see Section 5)
```

---

## 4. Proposal Envelope Structure

### 4.1 Fields (Required & Locked)

```json
{
  "domain_separator": "NPE|1.0.1",
  "version": "1.0.1",
  "proposal_id": "<uint64_hex>",
  "proposal_type": "RENORM_QUOTIENT" | "UNFOLD_QUOTIENT" | "CONTINUOUS_FLOW",
  "parent_slab_hash": "<hex_sha256>",
  "npe_state_hash": "<hex_sha256>",
  "timestamp_unix_sec": <int64>,
  "budget_post": {
    "max_steps": <int64_q18>,
    "max_cost": <int64_q18>,
    "max_debits": <int64_q18>,
    "max_refunds": <int64_q18>
  },
  "delta_hash": "<hex_sha256>",
  "delta_bytes_b64": "<base64_encoded_binary_delta>",
  "cert_hash": "<hex_sha256>",
  "certs_b64": "<base64_encoded_cert_block>"
}
```

### 4.2 Field Constraints

- **domain_separator**: Must be exactly `"NPE|1.0.1"` (string)
- **version**: Must be exactly `"1.0.1"` (string)
- **proposal_id**: Lowercase hex, 16 characters (uint64)
- **proposal_type**: One of {RENORM_QUOTIENT, UNFOLD_QUOTIENT, CONTINUOUS_FLOW}
- **parent_slab_hash**: Lowercase hex, 64 characters (sha256)
- **npe_state_hash**: Lowercase hex, 64 characters (sha256)
- **timestamp_unix_sec**: Positive int64
- **budget_post**: All fields are int64 Q18 values (integers, no floats)
- **delta_hash**: Lowercase hex, 64 characters (sha256)
- **delta_bytes_b64**: Valid base64 string
- **cert_hash**: Lowercase hex, 64 characters (sha256)
- **certs_b64**: Valid base64 string (or empty)

### 4.3 Field Order (Lexicographic for JCS)

After JCS encoding, fields are ordered alphabetically:
1. cert_hash
2. certs_b64
3. delta_bytes_b64
4. delta_hash
5. domain_separator
6. npe_state_hash
7. parent_slab_hash
8. proposal_id
9. proposal_type
10. timestamp_unix_sec
11. version
12. budget_post (nested fields sorted)

---

## 5. Binary Delta Envelope

The `delta_bytes_b64` field contains a base64-encoded binary structure with strict parsing rules.

### 5.1 DELTA_Z Format (Continuous Flow)

```
uint32_be(d)        // Number of deltas
int64_be[d]         // Array of signed 64-bit deltas
```

**Parsing:**
1. Decode base64
2. Read uint32_be at offset 0 → `d`
3. Expect exactly `4 + 8*d` bytes remaining
4. Read `d` int64_be values
5. **Reject if trailing bytes exist**

### 5.2 DELTA_A Format (Renorm/Unfold)

```
uint8(kind)                              // 0 = RENORM, 1 = UNFOLD, etc.
uint32_be(atlas_len)                     // Length of atlas bytes
<atlas_len bytes: atlas_payload>
uint32_be(cert_len)                      // Length of cert block
<cert_len bytes: cert_payload>
```

**Parsing:**
1. Decode base64
2. Read uint8 at offset 0 → `kind`
3. Read uint32_be at offset 1 → `atlas_len`
4. Read exactly `atlas_len` bytes from offset 5
5. Read uint32_be at offset `5 + atlas_len` → `cert_len`
6. Read exactly `cert_len` bytes from offset `9 + atlas_len`
7. **Reject if trailing bytes exist**
8. **Reject if atlas_len mismatches actual bytes read**
9. **Reject if cert_len mismatches actual bytes read**

### 5.3 Atlas Payload Structure

Atlas is a fixed-layout structure with variable-length payloads:

```
uint16_be(num_entries)
for each entry:
    uint8(entry_type)
    uint16_be(payload_len)
    <payload_len bytes>
```

Each entry's payload_hash is computed as `sha256(payload_bytes)`.

### 5.4 Cert Block Structure

```
uint16_be(num_certs)
for each cert:
    uint8(cert_type)
    uint16_be(cert_len)
    <cert_len bytes>
```

Cert order must be canonical (stable-sorted by type, then by first appearance).

---

## 6. PRNG: ChaCha20_Q18_STREAM_V1

### 6.1 Seed Derivation (Deterministic)

The PRNG seed is derived from fixed inputs, making randomness fully auditable.

```
seed_preimage = b"COH_NPE_PRNG_V1"
              || parent_slab_hash (32 bytes, raw hex decoded)
              || npe_state_hash (32 bytes, raw hex decoded)
              || uint64_be(proposal_id)  (8 bytes)

seed = sha256(seed_preimage)  // 32 bytes
```

### 6.2 Nonce Derivation

```
nonce_preimage = b"COH_NPE_PRNG_NONCE_V1" || seed_preimage

nonce = sha256(nonce_preimage)[:16]  // First 16 bytes
```

### 6.3 Keystream Generation

ChaCha20 is initialized with `(key=seed, nonce=nonce)` and generates a keystream using standard ChaCha20 spec (RFC 7539).

- **Block counter**: Starts at 0, increments per 64-byte block
- **Stream position**: Tracks current byte offset in keystream

### 6.4 Q18 Extraction

To extract a Q18 value from the keystream:

```
def extract_q18(stream_pos: int) -> int:
    # Read 4 bytes at stream_pos from keystream (little-endian)
    bytes_4 = keystream[stream_pos : stream_pos + 4]
    int32_val = int.from_bytes(bytes_4, 'little', signed=True)
    
    # Scale and clamp to valid Q18 range
    q18_val = int32_val  # Direct interpretation as Q18
    
    # Clamp to int64 bounds if needed
    if q18_val > 2**63 - 1:
        q18_val = 2**63 - 1
    elif q18_val < -2**63:
        q18_val = -2**63
    
    return q18_val
```

---

## 7. Certificate Hashing

### 7.1 Cert Bytes for Hash

The `cert_hash` field is recomputed from the cert block bytes:

```
cert_bytes_for_hash = <raw binary cert block before base64 encoding>
cert_hash = sha256(cert_bytes_for_hash)  (hex lowercase)
```

### 7.2 Cert Validation

During proposal verification, the JSON `cert_hash` value is recomputed from decoded cert bytes and must match exactly. Mismatch is immediate rejection.

---

## 8. Proposal Verification (RV-Compatible)

### 8.1 Verification Order

Proposals are verified in strict order:

1. **Version & Domain**: Check `domain_separator == "NPE|1.0.1"` and `version == "1.0.1"`
2. **JCS Canonicalization**: Recompute `sha256(jcs_bytes(proposal_envelope))` and verify against `proposal_hash` (if present)
3. **Base64 Decode**: Decode `delta_bytes_b64` and `certs_b64` (reject if invalid)
4. **Delta Hash**: Compute `sha256(decoded_delta_bytes)` and verify against `delta_hash` field
5. **Delta Parse**: Parse delta envelope (DELTA_Z or DELTA_A); reject if parse fails
6. **Budget Arithmetic**: Verify all Q18 calculations using deterministic rounding
7. **Cert Parse**: Parse cert block; recompute `cert_hash` and verify match
8. **Type-Specific Checks**: 
   - RENORM_QUOTIENT: Verify variance bounds, mismatch tolerance, wedge cert presence
   - UNFOLD_QUOTIENT: Verify unfold semantics, cost threshold
   - CONTINUOUS_FLOW: Verify flow continuity

### 8.2 Verification Result

Verifier returns one of:
- **ACCEPT**: Proposal is valid, safe to apply
- **PROJECT**: Proposal is valid but requires special handling (reserved for future use)
- **REJECT**: Proposal fails verification (includes reason code)

---

## 9. Domain Separators & Constants

### 9.1 Locked Constants

```python
DOMAIN_SEPARATOR = "NPE|1.0.1"
PROTOCOL_VERSION = "1.0.1"
NUMERIC_DOMAIN = "QFixed18"

# Rounding enums
ROUNDING_UP = "UP"      # For debits
ROUNDING_DOWN = "DOWN"  # For refunds

# PRNG preimages (never change)
PRNG_SEED_PREFIX = b"COH_NPE_PRNG_V1"
PRNG_NONCE_PREFIX = b"COH_NPE_PRNG_NONCE_V1"

# Hash lengths
SHA256_HEX_LEN = 64
PROPOSAL_ID_HEX_LEN = 16
```

---

## 10. EBNF Grammar (Syntax Reference)

```ebnf
proposal_envelope = "{"
    "domain_separator" ":" quoted_string ","
    "version" ":" quoted_string ","
    "proposal_id" ":" quoted_hex_uint64 ","
    "proposal_type" ":" proposal_type_enum ","
    "parent_slab_hash" ":" quoted_hex_sha256 ","
    "npe_state_hash" ":" quoted_hex_sha256 ","
    "timestamp_unix_sec" ":" integer ","
    "budget_post" ":" budget_object ","
    "delta_hash" ":" quoted_hex_sha256 ","
    "delta_bytes_b64" ":" quoted_base64_string ","
    "cert_hash" ":" quoted_hex_sha256 ","
    "certs_b64" ":" quoted_base64_string
"}"

proposal_type_enum = "RENORM_QUOTIENT" | "UNFOLD_QUOTIENT" | "CONTINUOUS_FLOW"

budget_object = "{"
    "max_steps" ":" integer ","
    "max_cost" ":" integer ","
    "max_debits" ":" integer ","
    "max_refunds" ":" integer
"}"

quoted_hex_sha256 = '"' /[0-9a-f]{64}/ '"'
quoted_hex_uint64 = '"' /[0-9a-f]{1,16}/ '"'
quoted_base64_string = '"' /[A-Za-z0-9+/]+=?/ '"'
integer = ["-"] /[0-9]+/
quoted_string = '"' /[^"\\]*(?:\\.[^"\\]*)*/ '"'
```

---

## 11. Verification Checklist

Before freezing this spec, verify:

- [ ] No float types anywhere in numeric domain (all Q18)
- [ ] JCS canonicalization matches RFC8785 exactly
- [ ] PRNG seeding is fully deterministic given proposal inputs
- [ ] Binary envelope parsing has zero ambiguity
- [ ] Rounding rules (UP for debits, DOWN for refunds) are explicit
- [ ] Domain separators are frozen and locked
- [ ] Test vectors TV1 and TV2 produce identical hashes on all platforms

---

## 12. Test Vectors

See `tests/vectors/npe/v1_0_1/TV1.proposal.json`, `TV2.proposal.json`, and expected output files.

---

## Document History

- **v1.0.1** (2026-02-21): Initial specification freeze. Locks JCS, Q18, PRNG, binary envelopes, cert hashing.
