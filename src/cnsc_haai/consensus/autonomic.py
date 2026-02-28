"""
Autonomic Module

Provides μ (stiffness) and fatigue controller for ATS.
Per docs/ats/10_mathematical_core/autonomic_regulation.md

The autonomic system modulates:
- Repair operator stiffness
- Hysteresis thresholds (θ_up, θ_down)
- Tax rates
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

# QFixed scale
QFIXED_SCALE = 10**18


@dataclass
class AutonomicState:
    """
    State of the autonomic controller.
    """

    mu: int  # Stiffness parameter (QFixed, in (0, 1])
    fatigue: int  # Fatigue parameter (QFixed, ≥ 0)
    theta_up: int  # Upward threshold (QFixed)
    theta_down: int  # Downward threshold (QFixed)
    tax_rate: int  # Tax rate (QFixed)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mu": str(self.mu),
            "fatigue": str(self.fatigue),
            "theta_up": str(self.theta_up),
            "theta_down": str(self.theta_down),
            "tax_rate": str(self.tax_rate),
        }


# Default parameters
DEFAULT_MU = QFIXED_SCALE  # 1.0
DEFAULT_FATIGUE = 0
DEFAULT_THETA_BASE = QFIXED_SCALE // 10  # 0.1
DEFAULT_TAX_BASE = QFIXED_SCALE // 10  # 0.1

# ODE parameters
ALPHA_MU = QFIXED_SCALE // 1000  # 0.001 - adaptation rate
BETA_MU = QFIXED_SCALE // 10000  # 0.0001 - fatigue coupling
GAMMA_FATIGUE = QFIXED_SCALE // 1000  # 0.001 - risk accumulation
DELTA_FATIGUE = QFIXED_SCALE // 100  # 0.01 - recovery rate


class AutonomicController:
    """
    Autonomic controller for μ and fatigue.
    """

    def __init__(
        self,
        mu: int = DEFAULT_MU,
        fatigue: int = DEFAULT_FATIGUE,
        theta_base: int = DEFAULT_THETA_BASE,
        tax_base: int = DEFAULT_TAX_BASE,
    ):
        self._mu = mu
        self._fatigue = fatigue
        self._theta_base = theta_base
        self._tax_base = tax_base

        # Compute initial thresholds
        self._theta_up = self._compute_theta_up()
        self._theta_down = self._compute_theta_down()
        self._tax_rate = self._compute_tax_rate()

    def _compute_theta_up(self) -> int:
        """θ_up = θ_base * μ"""
        return (self._theta_base * self._mu) // QFIXED_SCALE

    def _compute_theta_down(self) -> int:
        """θ_down = θ_base / μ"""
        if self._mu == 0:
            return QFIXED_SCALE * 1000  # Large value
        return (self._theta_base * QFIXED_SCALE) // self._mu

    def _compute_tax_rate(self) -> int:
        """tax_rate = tax_base / μ"""
        if self._mu == 0:
            return QFIXED_SCALE * 1000
        return (self._tax_base * QFIXED_SCALE) // self._mu

    def update(self, risk_delta: int, dt_q: int) -> None:
        """
        Update μ and fatigue using ODE dynamics.

        Args:
            risk_delta: Change in risk (QFixed)
            dt_q: Time step (QFixed)
        """
        # Update fatigue first
        # df/dt = γ * max(0, ΔV) - δ * (1 - μ) * f
        if risk_delta > 0:
            fatigue_increase = (GAMMA_FATIGUE * risk_delta * dt_q) // QFIXED_SCALE
        else:
            fatigue_increase = 0

        fatigue_decrease = (DELTA_FATIGUE * (QFIXED_SCALE - self._mu) * self._fatigue * dt_q) // (
            QFIXED_SCALE * QFIXED_SCALE
        )

        self._fatigue = max(0, self._fatigue + fatigue_increase - fatigue_decrease)

        # Update μ
        # dμ/dt = α_μ * (μ_target - μ) - β_μ * f
        mu_target = QFIXED_SCALE  # 1.0
        mu_adapt = (ALPHA_MU * (mu_target - self._mu) * dt_q) // QFIXED_SCALE
        mu_fatigue = (BETA_MU * self._fatigue * dt_q) // QFIXED_SCALE

        self._mu = self._mu + mu_adapt - mu_fatigue

        # Project to valid range: μ ∈ (0, 1]
        self._mu = min(QFIXED_SCALE, max(QFIXED_SCALE // 100, self._mu))

        # Ensure fatigue ≥ 0
        self._fatigue = max(0, self._fatigue)

        # Recompute thresholds
        self._theta_up = self._compute_theta_up()
        self._theta_down = self._compute_theta_down()
        self._tax_rate = self._compute_tax_rate()

    def get_state(self) -> AutonomicState:
        """Get current autonomic state."""
        return AutonomicState(
            mu=self._mu,
            fatigue=self._fatigue,
            theta_up=self._theta_up,
            theta_down=self._theta_down,
            tax_rate=self._tax_rate,
        )

    def get_mu(self) -> int:
        """Get μ (stiffness)."""
        return self._mu

    def get_fatigue(self) -> int:
        """Get fatigue."""
        return self._fatigue

    def get_theta_up(self) -> int:
        """Get upward threshold."""
        return self._theta_up

    def get_theta_down(self) -> int:
        """Get downward threshold."""
        return self._theta_down

    def get_tax_rate(self) -> int:
        """Get tax rate."""
        return self._tax_rate

    def apply_repair(self, state: Dict[str, Any], repair_base: int) -> int:
        """
        Apply repair operator scaled by μ.

        Args:
            state: Current state
            repair_base: Base repair amount

        Returns:
            Scaled repair amount
        """
        # scaled_repair = base_repair * μ
        return (repair_base * self._mu) // QFIXED_SCALE

    def check_admissibility(self, risk_delta: int) -> Tuple[bool, Optional[str]]:
        """
        Check if step is admissible using modulated thresholds.

        Args:
            risk_delta: Risk change (QFixed)

        Returns:
            (allowed, reason)
        """
        if risk_delta > 0:
            # Risk increasing - check θ_up
            if risk_delta > self._theta_up:
                return False, f"Risk delta {risk_delta} exceeds θ_up {self._theta_up}"
        else:
            # Risk decreasing - check θ_down
            if abs(risk_delta) < self._theta_down:
                return False, f"Risk improvement {abs(risk_delta)} below θ_down {self._theta_down}"

        return True, None

    def compute_tax(self, budget_consumption: int) -> int:
        """
        Compute tax on budget consumption.

        Args:
            budget_consumption: Base budget consumed

        Returns:
            Tax amount
        """
        # tax = consumption * tax_rate
        return (budget_consumption * self._tax_rate) // QFIXED_SCALE

    def set_mu(self, mu: int) -> None:
        """Set μ directly (for testing)."""
        self._mu = min(QFIXED_SCALE, max(QFIXED_SCALE // 100, mu))
        self._theta_up = self._compute_theta_up()
        self._theta_down = self._compute_theta_down()
        self._tax_rate = self._compute_tax_rate()

    def set_fatigue(self, fatigue: int) -> None:
        """Set fatigue directly (for testing)."""
        self._fatigue = max(0, fatigue)


# Global controller instance
_autonomic_controller = AutonomicController()


def get_autonomic_controller() -> AutonomicController:
    """Get the global autonomic controller."""
    return _autonomic_controller


def update_autonomic(risk_delta: int, dt_q: int = QFIXED_SCALE) -> AutonomicState:
    """
    Update the global autonomic controller.

    Args:
        risk_delta: Risk change (QFixed)
        dt_q: Time step (QFixed)

    Returns:
        Updated autonomic state
    """
    controller = get_autonomic_controller()
    controller.update(risk_delta, dt_q)
    return controller.get_state()


def get_autonomic_state() -> AutonomicState:
    """Get current autonomic state."""
    return get_autonomic_controller().get_state()
