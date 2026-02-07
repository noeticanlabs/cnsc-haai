# Replay Verifier Interface

**Spec Version:** 1.0.0  
**Status:** Canonical

## Overview

The replay verifier interface defines how to verify that a replay execution matches the original execution.

## Interface Contract

```python
interface ReplayVerifier:
    """Interface for replay verification."""
    
    def verify_replay(
        original: ReceiptChain,
        replay: ReceiptChain,
    ) -> ReplayResult:
        """
        Verify replay matches original execution.
        
        Args:
            original: Original execution receipts
            replay: Replay execution receipts
            
        Returns:
            ReplayResult with match status and details
        """
```

## Replay Result

```python
@dataclass
class ReplayResult:
    """Result of replay verification."""
    match: bool
    message: str
    details: Dict[str, Any]  # Breakdown of comparisons
```

## Verification Criteria

| Criterion | Description | Weight |
|-----------|-------------|--------|
| **Step Count** | Same number of steps | Required |
| **Step Types** | Same sequence of step types | Required |
| **Decisions** | Same gate decisions | Required |
| **Output Hashes** | Same output hashes | Required |
| **Timing** | Within tolerance | Optional |

## Wire Format

### Input

```json
{
  "original_chain": [...],
  "replay_chain": [...]
}
```

### Output

```json
{
  "match": true,
  "message": "Replay matches original",
  "details": {
    "step_count_match": true,
    "step_types_match": true,
    "decisions_match": true,
    "output_hashes_match": true,
    "mismatches": []
  }
}
```

## Error Codes

| Code | Meaning | Handling |
|------|---------|----------|
| `STEP_COUNT_MISMATCH` | Different number of steps | Fail verification |
| `DECISION_MISMATCH` | Gate decision differs | Fail verification |
| `OUTPUT_MISMATCH` | Output hash differs | Fail verification |
| `TIMING_DRIFT` | Timing exceeds tolerance | Warn only |

## Implementation

```python
def verify_replay(original: List[Receipt], replay: List[Receipt]) -> ReplayResult:
    """Verify replay matches original."""
    
    details = {}
    
    # Check step count
    if len(original) != len(replay):
        return ReplayResult(
            match=False,
            message="Step count mismatch",
            details={"expected": len(original), "actual": len(replay)}
        )
    
    # Check each receipt
    for i, (orig, rep) in enumerate(zip(original, replay)):
        if orig.content.step_type != rep.content.step_type:
            return ReplayResult(
                match=False,
                message=f"Step type mismatch at step {i}",
                details={"step": i, "expected": orig.content.step_type, "actual": rep.content.step_type}
            )
        
        if orig.content.decision != rep.content.decision:
            return ReplayResult(
                match=False,
                message=f"Decision mismatch at step {i}",
                details={"step": i, "expected": orig.content.decision, "actual": rep.content.decision}
            )
        
        if orig.content.output_hash != rep.content.output_hash:
            return ReplayResult(
                match=False,
                message=f"Output hash mismatch at step {i}",
                details={"step": i}
            )
    
    return ReplayResult(
        match=True,
        message="Replay matches original",
        details={"steps_compared": len(original)}
    )
```

## See Also

- Implementation: [`src/cnsc/haai/gml/replay.py`](../../src/cnsc/haai/gml/replay.py)
- Receipts: [`src/cnsc/haai/gml/receipts.py`](../../src/cnsc/haai/gml/receipts.py)
