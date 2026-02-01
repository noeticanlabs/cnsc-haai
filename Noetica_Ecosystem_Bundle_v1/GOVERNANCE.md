# Governance & Coherence Gates (Ecosystem Policy)

## Gate classes
### Structural gates
- Packet schema validity
- Grammar validity
- Bytecode validity

### Semantic gates
- Operator compatibility and closure legality
- Contract adherence (requires/invariants/ensures)
- Layer boundary enforcement

### Execution gates
- Deterministic stepping (no hidden randomness)
- Receipt emission for every step
- Hysteresis policy for warn→fail thresholds

## Failure modes
- Soft fail: retry/rewind with explicit receipts
- Hard fail: abort with failure receipts (class, invariant, checkpoint hash, remediation category)

## Receipt chain integrity
Receipts should provide chained run hashes and include packet/bytecode hashes where available.
