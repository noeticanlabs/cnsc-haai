# Appendix D: Minimal Kernel Specification

**The Minimal Working Implementation of CNHAAI**

## Overview

The Minimal Kernel is the simplest complete CNHAAI implementation. It contains only the essential components needed to demonstrate the architecture.

## Architecture

```
┌─────────────────────────────────────────┐
│              Minimal Kernel             │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Abstraction │  │ Gate Manager    │  │
│  │ Layer       │  │                 │  │
│  └─────────────┘  └─────────────────┘  │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Phase       │  │ Receipt System  │  │
│  │ Manager     │  │                 │  │
│  └─────────────┘  └─────────────────┘  │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Coherence   │  │ Recovery        │  │
│  │ Budget      │  │ Protocol        │  │
│  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────┘
```

## Components

### 1. Abstraction Layer (Minimal)

```yaml
abstraction_layer:
  levels: 3
  types:
    - "descriptive"
    - "mechanistic"
    - "normative"
  storage: "in_memory"
```

### 2. Gate Manager (Minimal)

```yaml
gate_manager:
  gates:
    - "evidence_sufficiency"
    - "coherence_check"
  enforcement: "strict"
```

### 3. Phase Manager (Minimal)

```yaml
phase_manager:
  phases:
    - "acquisition"
    - "construction"
    - "reasoning"
    - "validation"
```

### 4. Receipt System (Minimal)

```yaml
receipt_system:
  storage: "in_memory"
  signing: "hmac"  # Simplified for minimal kernel
  retention: "session_only"
```

## Configuration

```yaml
minimal_kernel:
  version: "1.0.0"
  settings:
    coherence_budget: 0.5
    max_abstraction_levels: 3
    evidence_threshold: 0.8
    receipt_retention: "session"
```

## Usage Example

```python
from cnhaai.kernel import MinimalKernel

# Initialize kernel
kernel = MinimalKernel()

# Create abstraction
abstraction = kernel.create_abstraction(
    type="descriptive",
    evidence=[...],
    scope="medical_diagnosis"
)

# Execute reasoning episode
episode = kernel.execute_episode(
    goal="diagnose_condition",
    evidence=[...]
)

# Get receipts
receipts = kernel.get_receipts(episode.id)
```

---

## Version Information

| Component | Version |
|-----------|---------|
| Appendix | D-minimal-kernel |
| Version | 1.0.0 |
| Updated | 2024-01-01 |
| Status | Canonical |
