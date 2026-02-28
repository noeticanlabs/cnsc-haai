"""
G1: Viability Compliance Test

Verifies that after any step (accepted or rejected), state remains in admissibility set K.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cnsc_haai.gmi.admissible import in_K
from cnsc_haai.gmi.step import gmi_step


def test_viability_after_accept(load_vector_fixture):
    """
    Test G1a: Accepted step ends in K.
    
    If a step is accepted, the resulting state must be in K.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    s1, r1 = gmi_step(s0, actions[0], ctx, p, chain0)
    
    # Even if projection occurred, accepted step must end in K
    assert in_K(s1, p), "Accepted state must be in K"


def test_viability_after_reject(load_vector_fixture):
    """
    Test G1b: Rejected step returns original state (in K).
    
    If a step is rejected, the state should remain unchanged (and thus in K).
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    # Find an action that causes rejection (Lyapunov increase)
    # For this test, we just verify rejected states are in K
    for i, action in enumerate(actions):
        s1, r1 = gmi_step(s0, action, ctx, p, chain0)
        
        # State must be in K (either accepted or rejected)
        assert in_K(s1, p), f"State after step {i} must be in K"


def test_projection_clamping(load_vector_fixture):
    """
    Test G1c: Projection properly clamps values.
    
    When rho exceeds rho_max, it should be clamped.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    s1, r1 = gmi_step(s0, actions[0], ctx, p, chain0)
    
    # All rho values must be in [0, rho_max]
    for row in s1.rho:
        for v in row:
            assert 0 <= v <= p.rho_max, f"rho {v} outside bounds [0, {p.rho_max}]"
    
    # All C values must be >= 0
    for row in s1.C:
        for v in row:
            assert v >= 0, f"C value {v} must be >= 0"
    
    # Budget must be >= 0
    assert s1.b >= 0, f"Budget {s1.b} must be >= 0"
