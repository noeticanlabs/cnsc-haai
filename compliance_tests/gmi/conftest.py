"""
GMI Compliance Test Configuration

Provides fixtures for loading golden vectors and testing GMI compliance.
"""

import json
from pathlib import Path
import pytest
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cnsc_haai.gmi.types import GMIState, GMIAction
from cnsc_haai.gmi.params import GMIParams


VEC_DIR = Path(__file__).parent / "vectors"


def load_vector(name: str):
    """
    Load a golden test vector.
    
    Args:
        name: Vector filename (e.g., "gmi_v1_5_case01.json")
        
    Returns:
        Tuple of (params, initial_state, actions, chain0)
    """
    data = json.loads((VEC_DIR / name).read_text(encoding="utf-8"))
    
    # Parse params
    p_raw = data["params"]
    p = GMIParams(
        version=data["version"],
        rho_max=p_raw["rho_max"],
        alpha_tau=p_raw["alpha_tau"],
        beta_C=p_raw["beta_C"],
        D_C=p_raw["D_C"],
        lambda_C=p_raw["lambda_C"],
        w_grad_theta_q=p_raw["w_grad_theta_q"],
        w_C_q=p_raw["w_C_q"],
        w_budget_barrier_q=p_raw["w_budget_barrier_q"],
        absorb_on_b0=p_raw["absorb_on_b0"],
    )
    
    # Parse initial state
    s0_raw = data["state0"]
    s0 = GMIState(
        rho=s0_raw["rho"],
        theta=s0_raw["theta"],
        C=s0_raw["C"],
        b=s0_raw["b"],
        t=s0_raw["t"],
    )
    
    # Parse actions
    actions = []
    for a in data["actions"]:
        actions.append(GMIAction(
            drho=a["drho"],
            dtheta=a["dtheta"],
            u_glyph=a["u_glyph"],
        ))
    
    # Parse initial chain
    chain0 = bytes.fromhex(data["chain0_hex"])
    
    return p, s0, actions, chain0


@pytest.fixture
def load_vector_fixture(request):
    """Pytest fixture for loading vectors."""
    def _load(name: str):
        return load_vector(name)
    return _load
