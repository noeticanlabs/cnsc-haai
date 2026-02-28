"""
GMI Parameters

Immutable configuration for GMI kernel.
All values are integers for determinism.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GMIParams:
    """
    GMI kernel parameters.
    
    All values are frozen integers for deterministic execution.
    """
    version: str = "1.5.0"

    # === Bounds ===
    rho_max: int = 1000  # Maximum density value

    # === Discrete time step ===
    dt_num: int = 1  # dt = dt_num / dt_den
    dt_den: int = 1

    # === Curvature dynamics ===
    alpha_tau: int = 10    # coupling tension -> C
    beta_C: int = 1        # curvature decay
    D_C: int = 1          # diffusion strength (Laplacian)
    lambda_C: int = 5      # coupling C -> theta (repulsion)

    # === Lyapunov weights (QFixed scaled integers) ===
    w_grad_theta_q: int = 1_000_000
    w_C_q: int = 1_000_000
    w_budget_barrier_q: int = 1_000_000

    # === Absorption rule ===
    absorb_on_b0: bool = True  # If True, reject V increase when b=0

    # === Determinism - domain separation tags ===
    hash_tag_state: str = "GMI_STATE_V1_5"
    hash_tag_chain: str = "GMI_CHAIN_V1_5"
    hash_tag_receipt: str = "GMI_RECEIPT_V1_5"

    # === Budget spending ===
    budget_spend_per_step: int = 1_000_000  # QFixed scaled (1.0)

    def __post_init__(self):
        """Validate parameters."""
        if self.rho_max <= 0:
            raise ValueError("rho_max must be positive")
        if self.dt_den == 0:
            raise ValueError("dt_den cannot be zero")
        if self.beta_C < 0:
            raise ValueError("beta_C cannot be negative")
        if self.w_grad_theta_q < 0 or self.w_C_q < 0:
            raise ValueError("Lyapunov weights cannot be negative")
