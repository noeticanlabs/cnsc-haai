# Guide 00: Quick Start

**Getting Started with CNHAAI**

## Installation

```bash
pip install cnhaai
```

## Basic Usage

```python
from cnhaai import MinimalKernel

# Initialize
kernel = MinimalKernel()

# Create abstraction
abstraction = kernel.create_abstraction(
    type="descriptive",
    evidence=[...],
    scope="example"
)

# Execute episode
episode = kernel.execute_episode(
    goal="example_task",
    evidence=[...]
)

# Get receipts
receipts = kernel.get_receipts(episode.id)
```

## Next Steps

1. Review [Module 03: Core Definition](../spine/03-core-definition.md)
2. Try [Appendix H: Exercises](../appendices/appendix-h-exercises.md)
3. Explore the [Examples](../appendices/appendix-g-examples.md)
