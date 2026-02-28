"""
G4: KKT Residual Compliance Test

Verifies KKT residual computations for stationary state claims.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cnsc_haai.gmi.kkt import kkt_residual_q
from cnsc_haai.gmi.step import gmi_step


def test_kkt_residual_feasibility(load_vector_fixture):
    """
    Test G4a: Initial state is KKT-feasible.
    
    The initial state should have zero feasibility residuals.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    
    r = kkt_residual_q(s0, p)
    
    assert r["feas_rho_q"] == 0, "rho feasibility must be zero"
    assert r["feas_C_q"] == 0, "C feasibility must be zero"
    assert r["feas_b_q"] == 0, "b feasibility must be zero"


def test_kkt_residual_after_step(load_vector_fixture):
    """
    Test G4b: After any step, state is KKT-feasible.
    
    Even after projection, the state should have zero feasibility residuals.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    s1, r1 = gmi_step(s0, actions[0], ctx, p, chain0)
    
    r = kkt_residual_q(s1, p)
    
    assert r["feas_rho_q"] == 0, "rho feasibility must be zero after step"
    assert r["feas_C_q"] == 0, "C feasibility must be zero after step"
    assert r["feas_b_q"] == 0, "b feasibility must be zero after step"


def test_kkt_residual_types(load_vector_fixture):
    """
    Test G4c: KKT residuals are integers.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    
    r = kkt_residual_q(s0, p)
    
    for key, value in r.items():
        assert isinstance(value, int), f"{key} must be int, got {type(value)}"


def test_stationarity_proxy_computed(load_vector_fixture):
    """
    Test G4d: Stationarity proxy (Laplacian norm) is computed.
    
    The stationarity proxy should be non-negative integer.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    
    r = kkt_residual_q(s0, p)
    
    assert "stationarity_theta_q" in r, "stationarity must be computed"
    assert r["stationarity_theta_q"] >= 0, "stationarity must be non-negative"
    assert isinstance(r["stationarity_theta_q"], int), "stationarity must be int"
