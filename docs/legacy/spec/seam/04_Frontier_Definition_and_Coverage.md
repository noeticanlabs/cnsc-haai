# Frontier Definition and Coverage

**Spec Version:** 1.0.0  
**Status:** Canonical

## Overview

The "frontier" is the boundary between processed and unprocessed bytecode. Coverage metrics track how much of the bytecode has been executed.

## Definitions

| Term | Definition |
|------|------------|
| **Frontier** | The PC value marking the boundary between executed and unexecuted code |
| **Coverage** | Percentage of bytecode that has been executed |
| **Hot Path** | Frequently executed code path |
| **Cold Path** | Rarely executed code path |

## Frontier State

```python
@dataclass
class FrontierState:
    """State of the execution frontier."""
    pc: int                    # Current program counter
    coverage: float           # 0.0 to 1.0
    hot_paths: List[str]      # Frequently executed paths
    cold_paths: List[str]     # Rarely executed paths
    visited_blocks: Set[int]  # Set of visited block indices
```

## Coverage Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Block Coverage** | visited_blocks / total_blocks | Percentage of basic blocks visited |
| **Edge Coverage** | visited_edges / total_edges | Percentage of control flow edges traversed |
| **Instruction Coverage** | executed_instructions / total_instructions | Percentage of instructions executed |

## Wire Format

```json
{
  "frontier": {
    "pc": 42,
    "coverage": 0.75,
    "visited_blocks": [0, 1, 2, 4],
    "total_blocks": 6,
    "visited_edges": [10],
    "total_edges": 12
  },
  "coverage_metrics": {
    "block_coverage": 0.667,
    "edge_coverage": 0.833,
    "instruction_coverage": 0.75
  }
}
```

## Coverage Goals

| Goal Type | Target | Description |
|-----------|--------|-------------|
| **Minimum** | 0.8 | At least 80% coverage required |
| **Target** | 0.95 | Desired coverage for quality |
| **Perfect** | 1.0 | 100% coverage (ideal) |

## Implementation

```python
def compute_coverage(vm: VM) -> CoverageReport:
    """Compute coverage metrics for VM execution."""
    
    # Count visited blocks
    visited = set(vm.execution_trace.block_visits.keys())
    total = len(vm.cfg.blocks)
    
    # Compute metrics
    report = {
        "block_coverage": len(visited) / total if total > 0 else 0,
        "visited_blocks": list(visited),
        "total_blocks": total,
        "frontier_pc": vm.pc,
    }
    
    return report
```

## See Also

- CFA: [`spec/nsc/05_CFA_Flow_Automaton.md`](../../spec/nsc/05_CFA_Flow_Automaton.md)
- Implementation: [`src/cnsc/haai/nsc/cfa.py`](../../src/cnsc/haai/nsc/cfa.py)
