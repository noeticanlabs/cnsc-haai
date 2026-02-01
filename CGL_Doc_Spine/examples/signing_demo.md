# Signing demo (Ed25519)

This folder includes a **real, verifiable** signature example for a CGL policy bundle.

## What is signed?
CGL signs the **bundle hash**, where:

- `bundle_hash = sha256(canonical_json(bundle_payload))`
- `bundle_payload` excludes:
  - `bundle_hash` itself
  - `signatures` (to avoid circularity)

In this example:

- **bundle_hash:** `sha256:c56b360d34bbd503e5b7c9a28a5ff56be323b8ce6e23683f03f570bea1119b46`

## How to verify (Python snippet)

```python
import json, hashlib, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

bundle = json.load(open("policy_bundle_example.json", "r", encoding="utf-8"))

# Reconstruct bundle_payload (remove signatures + bundle_hash)
bundle_payload = dict(bundle)
bundle_payload.pop("signatures", None)
bundle_payload.pop("bundle_hash", None)

canonical = json.dumps(bundle_payload, sort_keys=True, separators=(",",":")).encode("utf-8")
bundle_hash = hashlib.sha256(canonical).hexdigest()

assert bundle["bundle_hash"] == "sha256:" + bundle_hash

for sig in bundle["signatures"]:
    pub_pem = open("keys/" + sig["signer_id"].replace(":","_") + ".pub.pem", "rb").read()
    pub = serialization.load_pem_public_key(pub_pem)
    pub.verify(base64.b64decode(sig["signature"]), bundle_hash.encode("utf-8"))

print("All signatures verified.")
```

## Key files
Public keys are stored in `examples/keys/*.pub.pem`.

Private keys are intentionally **not** shipped in this doc spine.
