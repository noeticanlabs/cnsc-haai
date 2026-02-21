# 12. Cryptographic Layer

## 12.1 Digest Law

- **hash_preimage(data)** → 32 bytes
- **encode_digest(bytes32)** → "sha256:\<hex\>"

**Never hash a digest unless explicitly rehashing.**

## 12.2 Merkle Trees

Merkle trees built over raw digest bytes.

## 12.3 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| hash_preimage | sha256() |
| encode_digest | sha256_prefixed() |
| Merkle | MerkleTree |

## 12.4 JCS Serialization

All canonical serialization uses RFC8785 JSON Canonicalization Scheme (JCS).

See: `cnsc_haai.consensus.jcs`
