# Guide 01: Creating Abstraction Ladders

**Version**: 1.0.0
**Status**: DRAFT

---

## Overview

This guide explains how to create abstraction ladders in CNHAAI. Abstraction ladders provide a structured way to organize knowledge across multiple levels of abstraction.

---

## What is an Abstraction Ladder?

An abstraction ladder is a hierarchical structure that connects concepts at different levels of abstraction:

```
Level 4: High-level concepts (e.g., "medical diagnosis")
    ↓
Level 3: Domain models (e.g., "disease classification")
    ↓
Level 2: Causal mechanisms (e.g., "symptom-disease relationships")
    ↓
Level 1: Observational data (e.g., "patient symptoms")
```

---

## Creating a Ladder

### Step 1: Define the Abstraction Types

```python
from cnhaai.core.abstraction import AbstractionType

# Four types of abstractions:
# - DESCRIPTIVE: What is (observational)
# - MECHANISTIC: How it works (causal)
# - NORMATIVE: What should be (prescriptive)
# - COMPARATIVE: Relationships between entities
```

### Step 2: Build the Hierarchy

```python
from cnhaai.core.abstraction import Abstraction, AbstractionLayer, AbstractionType

# Create an abstraction layer
layer = AbstractionLayer(max_levels=4)

# Create root abstraction (Level 4)
root = Abstraction(
    type=AbstractionType.DESCRIPTIVE,
    evidence={"source1", "source2"},
    scope={"medical", "diagnosis"},
    validity={"confidence": 0.9},
    content={"name": "medical_diagnosis", "description": "..."}
)

# Create child abstraction (Level 3)
child = Abstraction(
    type=AbstractionType.MECHANISTIC,
    evidence={"evidence1"},
    scope={"medical"},
    validity={"confidence": 0.85},
    content={"name": "disease_classification"},
    parent_id=root.id
)

layer.add(root)
layer.add(child)
```

### Step 3: Validate the Ladder

```python
# Check hierarchy is valid
is_valid = layer.validate_hierarchy()
print(f"Ladder valid: {is_valid}")
```

---

## Best Practices

1. **Max depth**: Keep ladders to 3-5 levels
2. **Evidence**: Each abstraction needs supporting evidence
3. **Scope**: Define clear contexts where abstractions apply
4. **Validity**: Set validity constraints for each level

---

## Related Documents

- [Abstraction Theory](../spine/05-abstraction-theory.md)
- [Abstraction Types](../spine/06-abstraction-types.md)
- [Hierarchy Construction](../spine/08-hierarchy-construction.md)
