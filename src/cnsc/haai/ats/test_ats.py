"""
ATS Kernel Tests - Standalone Runner

Tests based on docs/ats/60_test_vectors/
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ats import (
    QFixed,
    State,
    Action,
    ActionType,
    Receipt,
    ReceiptContent,
    ReceiptVerifier,
    BudgetManager,
)
from ats.types import BeliefState, MemoryState, PlanState, PolicyState, IOState


# Test constants
Q = QFixed  # Shorthand


def test_qfixed_basic():
    """Test QFixed basic operations."""
    print("Testing QFixed basic operations...")
    
    a = Q(1000000000000000000)  # 1.0
    b = Q(500000000000000000)   # 0.5
    
    assert (a + b).value == 1500000000000000000
    assert (a - b).value == 500000000000000000
    assert (a * b).value == 500000000000000000
    
    print("  ✓ QFixed basic operations pass")


def test_qfixed_division():
    """Test QFixed division."""
    print("Testing QFixed division...")
    
    a = Q(1000000000000000000)  # 1.0
    b = Q(2000000000000000000)  # 2.0
    
    result = a / b
    assert result.value == 500000000000000000
    
    print("  ✓ QFixed division pass")


def test_qfixed_zero():
    """Test QFixed zero."""
    print("Testing QFixed zero...")
    
    assert Q.ZERO.value == 0
    assert Q.ZERO.is_zero()
    
    print("  ✓ QFixed zero pass")


def test_qfixed_comparison():
    """Test QFixed comparison."""
    print("Testing QFixed comparison...")
    
    a = Q(1000000000000000000)
    b = Q(500000000000000000)
    
    assert a > b
    assert b < a
    assert a == Q(1000000000000000000)
    
    print("  ✓ QFixed comparison pass")


def test_descent_trace():
    """Test minimal descent trace - budget preserved."""
    print("Testing minimal descent trace...")
    
    B0 = Q.from_int(1)  # 1.0
    kappa = Q.ONE
    
    # Create states - each belief entry sums to 1, weight 0.2 gives risk 0.2
    state0 = State(
        belief=BeliefState(beliefs={"concept_a": [Q.from_int(1), Q.ZERO]}),
        memory=MemoryState(),
        plan=PlanState(),
        policy=PolicyState(),
        io=IOState(),
    )
    
    # Same state for descent (risk decreases from 0.2 to 0)
    # Actually let's make it decrease by making one belief less
    state1 = State(
        belief=BeliefState(beliefs={"concept_a": [Q.ZERO, Q.ZERO]}),
        memory=MemoryState(),
        plan=PlanState(),
        policy=PolicyState(),
        io=IOState(),
    )
    
    # Compute hashes
    hash0 = state0.state_hash()
    hash1 = state1.state_hash()
    
    # Risk values - state0 has 1 belief sum, state1 has 0
    # risk = belief_sum * weight (0.2) = 0.2 and 0.0
    risk_before = QFixed(200000000000000000)  # 0.2
    risk_after = Q.ZERO  # 0.0
    
    # Delta (negative = descent: 0 - 0.2 = -0.2)
    delta = risk_after - risk_before  # -0.2
    delta_plus = Q.ZERO  # max(0, -0.2) = 0
    
    # Budget unchanged (descent)
    budget_before = B0
    budget_after = B0
    
    # Create receipt
    content = ReceiptContent(
        step_type="VM_EXECUTION",
        risk_before_q=risk_before,
        risk_after_q=risk_after,
        delta_plus_q=delta_plus,
        budget_before_q=budget_before,
        budget_after_q=budget_after,
        kappa_q=kappa,
        state_hash_before=hash0,
        state_hash_after=hash1,
        decision="PASS",
    )
    
    receipt = Receipt(
        version="1.0.0",
        receipt_id="",  # Will be computed
        content=content,
        previous_receipt_id="00000000",
        chain_hash="",  # Will be computed
    )
    # Compute receipt_id and chain_hash properly
    receipt.receipt_id = receipt.compute_receipt_id()
    receipt.chain_hash = receipt.compute_chain_hash(receipt.previous_receipt_id)
    
    # Verify
    verifier = ReceiptVerifier(initial_budget=B0, kappa=kappa)
    accepted, error = verifier.verify_step(
        state_before=state0,
        state_after=state1,
        action=Action(ActionType.BELIEF_UPDATE),
        receipt=receipt,
        budget_before=budget_before,
        budget_after=budget_after,
        kappa=kappa,
    )
    
    assert accepted is True, f"Expected ACCEPT, got error: {error}"
    print("  ✓ Minimal descent trace pass")


def test_amplification():
    """Test paid amplification trace."""
    print("Testing paid amplification trace...")
    
    B0 = Q.from_int(1)
    kappa = Q.ONE
    
    # Create states with increasing risk: 0 → 1.5 (0 → 0.3)
    # For risk_before = 0: empty beliefs
    state_before = State(
        belief=BeliefState(beliefs={}),
        memory=MemoryState(),
        plan=PlanState(),
        policy=PolicyState(),
        io=IOState(),
    )
    
    # For risk_after = 3 (0.3): beliefs summing to 1.5
    # risk = belief_sum * weight = 1.5 * 0.2 = 0.3 = 3e17
    # concept_a: 0.5+0.5=1.0, concept_b: 0.5+0=0.5 -> total 1.5
    state_after = State(
        belief=BeliefState(beliefs={
            "concept_a": [Q.from_int(5) / Q.from_int(10), Q.from_int(5) / Q.from_int(10)],
            "concept_b": [Q.from_int(5) / Q.from_int(10), Q.ZERO],
        }),
        memory=MemoryState(),
        plan=PlanState(),
        policy=PolicyState(),
        io=IOState(),
    )
    
    state_hash_before = state_before.state_hash()
    state_hash_after = state_after.state_hash()
    
    # Step: Risk increase 0 → 0.3
    risk_before = Q.ZERO
    risk_after = Q.from_int(3) / Q.from_int(10)  # 0.3
    delta = risk_after - risk_before  # 0.3
    delta_plus = delta  # max(0, 0.3) = 0.3
    
    budget_before = B0
    budget_after = B0 - kappa * delta  # 1.0 - 0.3 = 0.7
    
    content = ReceiptContent(
        step_type="VM_EXECUTION",
        risk_before_q=risk_before,
        risk_after_q=risk_after,
        delta_plus_q=delta_plus,
        budget_before_q=budget_before,
        budget_after_q=budget_after,
        kappa_q=kappa,
        state_hash_before=state_hash_before,
        state_hash_after=state_hash_after,
        decision="PASS",
    )
    
    receipt = Receipt(
        version="1.0.0",
        receipt_id="",  # Will be computed
        content=content,
        previous_receipt_id="00000000",
        chain_hash="",  # Will be computed
    )
    # Compute receipt_id and chain_hash properly
    receipt.receipt_id = receipt.compute_receipt_id()
    receipt.chain_hash = receipt.compute_chain_hash(receipt.previous_receipt_id)
    
    verifier = ReceiptVerifier(initial_budget=B0, kappa=kappa)
    accepted, error = verifier.verify_step(
        state_before=state_before,
        state_after=state_after,
        action=Action(ActionType.BELIEF_UPDATE),
        receipt=receipt,
        budget_before=budget_before,
        budget_after=budget_after,
        kappa=kappa,
    )
    
    assert accepted is True, f"Expected ACCEPT, got error: {error}"
    print("  ✓ Paid amplification trace pass")


def test_budget_preserved_on_descent():
    """When ΔV ≤ 0, budget preserved."""
    print("Testing budget preserved on descent...")
    
    manager = BudgetManager(Q.from_int(1), Q.ONE)
    
    # Negative delta
    new_budget, accepted = manager.compute_transition(Q.from_int(-5))
    
    assert accepted is True
    assert new_budget == Q.from_int(1)
    print("  ✓ Budget preserved on descent pass")


def test_budget_consumed_on_ascent():
    """When ΔV > 0, budget consumed."""
    print("Testing budget consumed on ascent...")
    
    manager = BudgetManager(Q.from_int(1), Q.ONE)
    
    # Positive delta = 0.3 (3 tenths = 3e17)
    new_budget, accepted = manager.compute_transition(Q.from_int(3) / Q.from_int(10))  # 0.3
    
    assert accepted is True
    assert new_budget == Q.from_int(7) / Q.from_int(10)  # 1.0 - 0.3 = 0.7
    print("  ✓ Budget consumed on ascent pass")


def test_insufficient_budget():
    """When B < κ × ΔV, reject."""
    print("Testing insufficient budget rejection...")
    
    manager = BudgetManager(Q.from_int(1), Q.ONE)
    
    # Try to consume more than available
    new_budget, accepted = manager.compute_transition(Q.from_int(5))  # 0.5
    
    assert accepted is False
    assert new_budget == Q.ZERO
    print("  ✓ Insufficient budget rejection pass")


def test_budget_invariant():
    """Test budget invariant: total_consumed ≤ initial."""
    print("Testing budget invariant...")
    
    manager = BudgetManager(Q.from_int(1), Q.ONE)
    
    # Multiple steps
    manager.compute_transition(Q.from_int(2))  # 0.2
    manager.compute_transition(Q.from_int(3))  # 0.3
    manager.compute_transition(Q.from_int(-1))  # 0 (descent)
    
    assert manager.check_invariant() is True
    print("  ✓ Budget invariant pass")


def test_chain_verification():
    """Test receipt chain linking."""
    print("Testing receipt chain verification...")
    
    B0 = Q.from_int(1)
    kappa = Q.ONE
    
    state = State(
        belief=BeliefState(),
        memory=MemoryState(),
        plan=PlanState(),
        policy=PolicyState(),
        io=IOState(),
    )
    
    state_hash = state.state_hash()
    
    # Create receipt
    content = ReceiptContent(
        step_type="VM_EXECUTION",
        risk_before_q=Q.ZERO,
        risk_after_q=Q.ZERO,
        delta_plus_q=Q.ZERO,
        budget_before_q=B0,
        budget_after_q=B0,
        kappa_q=kappa,
        state_hash_before=state_hash,
        state_hash_after=state_hash,
        decision="PASS",
    )
    
    receipt = Receipt(
        version="1.0.0",
        receipt_id="",  # Will be computed
        content=content,
        previous_receipt_id="00000000",
        chain_hash="",  # Will be computed
    )
    # Compute receipt_id and chain_hash properly
    receipt.receipt_id = receipt.compute_receipt_id()
    receipt.chain_hash = receipt.compute_chain_hash(receipt.previous_receipt_id)
    
    # Verify
    verifier = ReceiptVerifier(initial_budget=B0, kappa=kappa)
    accepted, error = verifier.verify_step(
        state, state, Action(ActionType.CUSTOM),
        receipt, B0, B0, kappa
    )
    
    assert accepted is True
    print("  ✓ Receipt chain verification pass")


def main():
    """Run all tests."""
    print("=" * 60)
    print("ATS Kernel Tests")
    print("=" * 60)
    
    tests = [
        test_qfixed_basic,
        test_qfixed_division,
        test_qfixed_zero,
        test_qfixed_comparison,
        test_descent_trace,
        test_amplification,
        test_budget_preserved_on_descent,
        test_budget_consumed_on_ascent,
        test_insufficient_budget,
        test_budget_invariant,
        test_chain_verification,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
