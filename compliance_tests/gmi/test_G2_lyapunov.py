"""
G2: Lyapunov Monotonicity Compliance Test

Verifies that accepted steps do not increase the Lyapunov functional.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cnsc_haai.gmi.step import gmi_step


def test_lyapunov_nonincreasing_on_accept(load_vector_fixture):
    """
    Test G2: Accepted steps must have dV <= 0.
    
    The Lyapunov functional must be non-increasing on accepted steps.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    # Process all actions
    for i, action in enumerate(actions):
        s1, r1 = gmi_step(s0, action, ctx, p, chain0)
        
        # If accepted, dV must be <= 0
        if r1.is_accepted():
            assert r1.dV_q <= 0, \
                f"Step {i}: Accepted step must have dV <= 0, got {r1.dV_q}"
        
        # Update for next iteration
        s0 = s1


def test_rejected_step_has_zero_dV(load_vector_fixture):
    """
    Test G2b: Rejected steps report dV = 0.
    
    When a step is rejected, no state change occurs, so dV is 0.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    for i, action in enumerate(actions):
        s1, r1 = gmi_step(s0, action, ctx, p, chain0)
        
        if not r1.is_accepted():
            # Rejected step should have dV = 0
            assert r1.dV_q == 0, \
                f"Step {i}: Rejected step must have dV = 0, got {r1.dV_q}"
        
        s0 = s1


def test_lyapunov_values_are_integers(load_vector_fixture):
    """
    Test G2c: Lyapunov values are integer (no floats).
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    s1, r1 = gmi_step(s0, actions[0], ctx, p, chain0)
    
    assert isinstance(r1.V_prev_q, int), "V_prev_q must be int"
    assert isinstance(r1.V_next_q, int), "V_next_q must be int"
    assert isinstance(r1.dV_q, int), "dV_q must be int"
