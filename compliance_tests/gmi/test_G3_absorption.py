"""
G3: Absorption at b=0 Compliance Test

Verifies that when budget b=0, no step that increases V is accepted.
This enforces the absorption rule.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cnsc_haai.gmi.types import GMIState
from cnsc_haai.gmi.step import gmi_step


def test_absorption_b0(load_vector_fixture):
    """
    Test G3a: When b=0, cannot accept positive dV.
    
    The absorption rule states: when b=0 (budget exhausted),
    any step that would increase V must be rejected.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    # Create state with b=0
    sZ = GMIState(
        rho=s0.rho,
        theta=s0.theta,
        C=s0.C,
        b=0,
        t=s0.t,
    )
    
    # Try action - should reject if dV would be positive
    s1, r1 = gmi_step(sZ, actions[0], ctx, p, chain0)
    
    # Cannot accept a positive dV under absorption policy
    if r1.is_accepted():
        assert r1.dV_q <= 0, \
            f"When b=0, cannot accept positive dV, got {r1.dV_q}"


def test_absorption_reject_code(load_vector_fixture):
    """
    Test G3b: Verify correct rejection code for absorption.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    # Create state with b=0
    sZ = GMIState(
        rho=s0.rho,
        theta=s0.theta,
        C=s0.C,
        b=0,
        t=s0.t,
    )
    
    s1, r1 = gmi_step(sZ, actions[0], ctx, p, chain0)
    
    # If rejected at b=0 with positive dV, should have absorption code
    if not r1.is_accepted() and r1.dV_q > 0:
        assert r1.reject_code == "REJECT_ABSORB_B0_DV_POS", \
            f"Expected absorption rejection code, got {r1.reject_code}"


def test_budget_decreases_over_time(load_vector_fixture):
    """
    Test G3c: Budget monotonically decreases (when not at 0).
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    initial_budget = s0.b
    
    # Run a few steps
    for i, action in enumerate(actions[:3]):
        s1, r1 = gmi_step(s0, action, ctx, p, chain0)
        
        # Budget should never increase
        assert s1.b <= initial_budget, \
            f"Step {i}: Budget should not increase"
        
        initial_budget = s1.b
        s0 = s1
