"""
G0: Determinism Compliance Test

Verifies that GMI kernel produces identical results on repeated runs.
This is a fundamental requirement for consensus.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cnsc_haai.gmi.step import gmi_step


def test_repeat_run_determinism(load_vector_fixture):
    """
    Test G0: Running the same step twice produces identical results.
    
    This ensures:
    - No RNG influences output
    - No time-dependent behavior
    - Hash outputs are stable
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    # Run step twice with same inputs
    sA, rA = gmi_step(s0, actions[0], ctx, p, chain0)
    sB, rB = gmi_step(s0, actions[0], ctx, p, chain0)
    
    # All outputs must be identical
    assert rA.next_state_hash == rB.next_state_hash, "State hash must be deterministic"
    assert rA.chain_next == rB.chain_next, "Chain tip must be deterministic"
    assert rA.V_next_q == rB.V_next_q, "Lyapunov value must be deterministic"
    assert rA.b_next_q == rB.b_next_q, "Budget must be deterministic"
    assert rA.dV_q == rB.dV_q, "Delta V must be deterministic"


def test_different_inputs_produce_different_hashes(load_vector_fixture):
    """
    Test that different inputs produce different hashes.
    
    This ensures the hash function is not degenerate.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    # Run with first action
    s1, r1 = gmi_step(s0, actions[0], ctx, p, chain0)
    
    # Run with different action (if available)
    if len(actions) > 1:
        s2, r2 = gmi_step(s0, actions[1], ctx, p, chain0)
        
        # Different actions should generally produce different hashes
        # (not guaranteed, but highly probable)
        if r1.next_state_hash != r2.next_state_hash:
            pass  # Expected
        else:
            # If same, verify it's not due to bug - check states are same
            assert s1.rho == s2.rho and s1.theta == s2.theta, \
                "Same hash implies same state"


def test_no_floats_in_output(load_vector_fixture):
    """
    Test that no floats appear in any output.
    
    This is a core requirement: all numeric computation is integer-only.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    s1, r1 = gmi_step(s0, actions[0], ctx, p, chain0)
    
    # Check all numeric fields are int
    assert isinstance(r1.V_prev_q, int), "V_prev_q must be int"
    assert isinstance(r1.V_next_q, int), "V_next_q must be int"
    assert isinstance(r1.dV_q, int), "dV_q must be int"
    assert isinstance(r1.b_prev_q, int), "b_prev_q must be int"
    assert isinstance(r1.b_next_q, int), "b_next_q must be int"
    assert isinstance(r1.db_q, int), "db_q must be int"
    
    # Check state fields are int
    for row in s1.rho:
        for v in row:
            assert isinstance(v, int), f"rho value {v} must be int"
    for row in s1.theta:
        for v in row:
            assert isinstance(v, int), f"theta value {v} must be int"
    for row in s1.C:
        for v in row:
            assert isinstance(v, int), f"C value {v} must be int"
    assert isinstance(s1.b, int), "state b must be int"
    assert isinstance(s1.t, int), "state t must be int"
