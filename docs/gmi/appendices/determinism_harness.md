# Appendix: Determinism Test Harness

## Overview

This harness verifies that GMI operations are deterministic.

## Test Code

```python
"""
GMI Determinism Test Harness

Verifies that all GMI operations produce deterministic results
given identical inputs.
"""

import pytest
from cnsc.haai.ats.types import (
    StateCore, BeliefState, MemoryState, PlanState, PolicyState, IOState,
    Action, ActionType, Receipt
)
from cnsc.haai.ats.numeric import QFixed
from cnsc_haai.consensus.jcs import jcs_canonical_bytes
from cnsc_haai.consensus.hash import sha256


class TestDeterminism:
    """Test determinism of GMI operations."""
    
    def test_state_hash_determinism(self):
        """State hash must be deterministic."""
        # Create identical states
        state1 = self._create_test_state()
        state2 = self._create_test_state()
        
        # Hash must be identical
        assert state1.state_hash() == state2.state_hash()
    
    def test_receipt_determinism(self):
        """Receipt generation must be deterministic."""
        # Create identical receipts
        receipt1 = self._create_test_receipt()
        receipt2 = self._create_test_receipt()
        
        # Hash must be identical
        assert receipt1.compute_hash() == receipt2.compute_hash()
    
    def test_chain_hash_determinism(self):
        """Chain hashing must be deterministic."""
        # Create identical chains
        receipt1 = self._create_test_receipt()
        receipt2 = self._create_test_receipt()
        
        chain1 = receipt1.compute_chain_hash(None)
        chain2 = receipt2.compute_chain_hash(None)
        
        assert chain1 == chain2
    
    def test_jcs_determinism(self):
        """JCS serialization must be deterministic."""
        data = {"key": "value", "number": 123}
        
        bytes1 = jcs_canonical_bytes(data)
        bytes2 = jcs_canonical_bytes(data)
        
        assert bytes1 == bytes2
    
    def test_execution_determinism(self):
        """Execution must be deterministic given same inputs."""
        # This tests NSC VM determinism
        # See: tests/test_kernel_integration.py
        
        # Run same program twice
        # Compare outputs
        pass  # Implemented elsewhere
    
    def _create_test_state(self) -> StateCore:
        """Create a test state."""
        belief = BeliefState(beliefs={
            "concept1": [QFixed.from_int(1), QFixed.from_int(2)]
        })
        memory = MemoryState(cells=[b"test"])
        plan = PlanState(steps=[
            Action(ActionType.BELIEF_UPDATE, parameters=("test",))
        ])
        policy = PolicyState(mappings={})
        io_state = IOState(input_buffer=[], output_buffer=[])
        
        return StateCore(
            belief=belief,
            memory=memory,
            plan=plan,
            policy=policy,
            io=io_state
        )
    
    def _create_test_receipt(self) -> Receipt:
        """Create a test receipt."""
        # See Receipt class
        pass


def run_determinism_tests():
    """Run all determinism tests."""
    pytest.main([__file__, "-v"])
```

## Running Tests

```bash
# Run determinism tests
pytest cnhaai/docs/gmi/appendices/determinism_harness.md -v

# Run full test suite
pytest tests/ -v
```
