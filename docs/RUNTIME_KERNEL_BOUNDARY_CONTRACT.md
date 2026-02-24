# Runtime / Kernel Boundary Contract

> **Status**: Active  
> **Created**: 2026-02-24

This document defines the explicit boundary between the **Protocol Kernel** (`cnsc_haai`) and the **Runtime** (`cnsc.haai`). Without this contract, implicit dependencies will cause the two sides to drift.

---

## Namespace Mapping

| Canonical Name | Status | Description |
|---------------|--------|-------------|
| `cnsc.haai` | **Active** | Runtime (GHLL, GLLL, GML, NSC, TGS) |
| `cnsc_haai` | **Deprecated** | Protocol kernel (consensus, hashing, merkle) |
| `cnhaai` | **Deprecated** | Legacy namespace, do not use |

---

## Protocol Kernel (`cnsc_haai`)

**Characteristics:**
- Pure functions, no side effects
- Deterministic hashing primitives
- Consensus-critical operations only
- No network calls, no file IO
- Serializable state

**Location:** `src/cnsc_haai/consensus/`

**Exports:**
- `receipt_id()` - Compute content hash
- `chain_digest()` - Compute chain hash with history
- `merkle_*` - Merkle tree operations
- `jcs_canonical_bytes()` - Canonical serialization
- `compute_canonical_steps()` - Deterministic time stepping

---

## Runtime (`cnsc.haai`)

**Characteristics:**
- Side-effectful operations
- User interaction
- IO-bound operations
- Gate evaluation
- Proposal generation (NPE client)

**Location:** `src/cnsc/haai/`

**Submodules:**
- `ghll/` - High-level language
- `glll/` - Low-level language  
- `gml/` - Graph modeling language
- `nsc/` - Neural structure compiler
- `tgs/` - Temporal governance system

---

## Seam Module

All kernel imports must go through explicit seam:

```python
# src/cnsc/haai/kernel_interface.py
"""
Kernel Interface - Stable API for runtime to access protocol kernel.

This module provides a stable interface between the runtime (cnsc.haai)
and the protocol kernel (cnsc_haai).
"""

from cnsc_haai.consensus.chain import receipt_id, chain_digest
from cnsc_haai.consensus.merkle import merkle_root, verify_proof
from cnsc_haai.consensus.jcs import jcs_canonical_bytes
from cnsc_haai.consensus.continuous import compute_canonical_steps

__all__ = [
    "receipt_id",
    "chain_digest", 
    "merkle_root",
    "verify_proof",
    "jcs_canonical_bytes",
    "compute_canonical_steps",
]
```

---

## Rule: No Direct Kernel Imports in Runtime

**Do NOT do this:**
```python
# BAD - Direct import from kernel
from cnsc_haai.consensus.chain import receipt_id
```

**DO this:**
```python
# GOOD - Import from seam
from cnsc.haai.kernel_interface import receipt_id
```

---

## Rationale

1. **Testability**: Runtime can mock the kernel interface
2. **Stability**: Kernel can change internal structure without breaking runtime
3. **Auditability**: All kernel access is visible through seam
4. **Migration Path**: Eventually, kernel code can be moved into cnsc.haai

---

## Transition Plan

1. ✅ `cnsc_haai` has deprecation warning
2. ✅ `cnhaai` has deprecation warning  
3. 🔄 Create `kernel_interface.py` in cnsc.haai
4. 🔄 Update runtime imports to use kernel_interface
5. 🔄 Eventually remove deprecation warnings when all imports are through seam
