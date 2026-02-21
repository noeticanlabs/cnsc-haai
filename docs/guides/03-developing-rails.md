# Guide 03: Developing Rails

**Version**: 1.0.0
**Status**: DRAFT

---

## Overview

Rails are execution pathways that constrain behavior within bounded limits. This guide explains how to implement custom rails.

---

## What are Rails?

Rails provide structured execution paths that ensure:
- Bounded behavior
- Safe transitions
- Coherence preservation
- Controlled flow execution

---

## Rail Implementation

### Basic Rail Structure

```python
from cnsc.haai.tgs.rails import CoherenceRails, RailResult

class CustomRail:
    """Custom execution rail."""
    
    def __init__(self, name: str, constraints: List[str]):
        self.name = name
        self.constraints = constraints
    
    def validate_path(self, from_state, to_state) -> RailResult:
        """Validate path through the rail."""
        # Implementation
        pass
    
    def execute(self, context) -> RailResult:
        """Execute within rail constraints."""
        # Implementation
        pass
```

### Using CoherenceRails

```python
from cnsc.haai.tgs.rails import CoherenceRails

rails = CoherenceRails()
rails.add_constraint("budget_limit", max_budget=1000)
rails.add_constraint("phase_sequence", allowed=["acquisition", "construction", "validation"])

result = rails.execute_proposal(proposal, context)
```

---

## Best Practices

1. Define clear entry/exit conditions
2. Implement rollback on failure
3. Log all rail transitions
4. Test edge cases

---

## Related Documents

- [Rail Theory](../spine/17-rail-theory.md)
- [Rail Implementation](../spine/18-rail-implementation.md)
