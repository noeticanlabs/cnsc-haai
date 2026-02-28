"""
Deterministic Step Kernel (Governed Prediction)

This module implements the core GMI transition function:
- gmi_step: (state, action, ctx) -> (state', receipt)

Enforces:
- Determinism (no floats, no RNG)
- Admissibility (project or reject)
- Lyapunov monotonicity (reject if V increases)
- Absorption at b=0 (reject any V increase when budget=0)
- Chain hashing + receipt generation
"""

from __future__ import annotations
from typing import Tuple, Dict, Any, List
from .types import GMIState, GMIAction, GMIStepReceipt
from .params import GMIParams
from .admissible import in_K, project_K
from .lyapunov import V_extended_q
from .jcs import jcs_dumps
from .hash import sha256_tagged


def _hash_state(s: GMIState, p: GMIParams) -> bytes:
    """
    Compute deterministic state hash.

    Args:
        s: GMI state
        p: GMI parameters

    Returns:
        32-byte SHA256 hash
    """
    obj = {
        "rho": s.rho,
        "theta": s.theta,
        "C": s.C,
        "b": s.b,
        "t": s.t,
        "v": p.version,
    }
    return sha256_tagged(p.hash_tag_state, jcs_dumps(obj))


def _hash_chain(chain_prev: bytes, receipt_obj: Dict[str, Any], p: GMIParams) -> bytes:
    """
    Compute chain hash from previous tip and receipt.

    Args:
        chain_prev: Previous chain tip
        receipt_obj: Receipt as dict
        p: GMI parameters

    Returns:
        New chain tip
    """
    return sha256_tagged(p.hash_tag_chain, chain_prev + jcs_dumps(receipt_obj))


def _laplacian_2d(grid: List[List[int]]) -> List[List[int]]:
    """
    Compute discrete Laplacian on 2D grid.

    Laplacian[i][j] = sum(neighbors) - cnt * grid[i][j]

    Args:
        grid: 2D integer array

    Returns:
        2D Laplacian array
    """
    n = len(grid)
    m = len(grid[0]) if n > 0 else 0
    out: List[List[int]] = [[0] * m for _ in range(n)]

    for i in range(n):
        for j in range(m):
            c = grid[i][j]
            acc = 0
            cnt = 0

            if i > 0:
                acc += grid[i - 1][j]
                cnt += 1
            if i + 1 < n:
                acc += grid[i + 1][j]
                cnt += 1
            if j > 0:
                acc += grid[i][j - 1]
                cnt += 1
            if j + 1 < m:
                acc += grid[i][j + 1]
                cnt += 1

            out[i][j] = acc - cnt * c

    return out


def gmi_step(
    s: GMIState,
    a: GMIAction,
    ctx: Dict[str, Any],
    p: GMIParams,
    chain_prev: bytes,
) -> Tuple[GMIState, GMIStepReceipt]:
    """
    Execute deterministic GMI step.

    Process:
    1. Compute proposed state from action
    2. Project to admissibility set K (captures constraint impact)
    3. Build tau field from active set (normal cone witness)
    4. Update curvature C with tension-diffusion dynamics
    5. Update budget (spend per step)
    6. Check Lyapunov monotonicity
    7. Accept or reject based on governance rules

    Args:
        s: Current state
        a: Action to apply
        ctx: Execution context (unused, for extensibility)
        p: GMI parameters
        chain_prev: Previous chain tip

    Returns:
        Tuple of (new state, receipt)
    """
    # === Pre-step values ===
    V_prev = V_extended_q(s, p)
    b_prev = s.b
    prev_hash = _hash_state(s, p)

    n = len(s.theta)
    m = len(s.theta[0]) if n > 0 else 0

    # === 1) Propose theta and rho ===
    theta_prop: List[List[int]] = [[0] * m for _ in range(n)]
    rho_prop: List[List[int]] = [[0] * m for _ in range(n)]

    for i in range(n):
        for j in range(m):
            # theta' = theta + dtheta - lambda_C * C (repulsion from curvature)
            theta_prop[i][j] = s.theta[i][j] + a.dtheta[i][j] - (p.lambda_C * s.C[i][j])
            # rho' = rho + drho
            rho_prop[i][j] = s.rho[i][j] + a.drho[i][j]

    # Start with current C (will update in step 4)
    C_prop = [row[:] for row in s.C]

    s_prop = GMIState(
        rho=rho_prop,
        theta=theta_prop,
        C=C_prop,
        b=s.b,
        t=s.t + 1,
    )

    # === 2) Project to K (captures constraint impact) ===
    projected = False
    witness: Dict[str, Any] = {}

    if not in_K(s_prop, p):
        s_proj, w_proj = project_K(s_prop, p)
        projected = True
        witness.update(w_proj)
        s1 = s_proj
    else:
        s1 = s_prop

    # === 3) Build tau field from clamped upper active set ===
    # tau = indicator of rho clamped at upper bound (proxy for normal cone impulse)
    tau: List[List[int]] = [[0] * m for _ in range(n)]
    rho_high = witness.get("rho_active_high", [])
    for i, j in rho_high:
        tau[i][j] = 1

    # === 4) Update curvature C ===
    # C' = max(0, C + alpha*tau - beta*C + D*Lap(C))
    Lc = _laplacian_2d(s1.C)
    C2: List[List[int]] = [[0] * m for _ in range(n)]

    for i in range(n):
        for j in range(m):
            c = s1.C[i][j]
            val = c + p.alpha_tau * tau[i][j] - p.beta_C * c + p.D_C * Lc[i][j]
            C2[i][j] = val if val > 0 else 0

    s2 = GMIState(
        rho=s1.rho,
        theta=s1.theta,
        C=C2,
        b=s1.b,
        t=s1.t,
    )

    # === 5) Budget update ===
    # Spend fixed budget per accepted step
    spend = p.budget_spend_per_step
    b_next = b_prev - spend
    if b_next < 0:
        b_next = 0

    s3 = GMIState(
        rho=s2.rho,
        theta=s2.theta,
        C=s2.C,
        b=b_next,
        t=s2.t,
    )

    # === 6) Lyapunov check ===
    V_next = V_extended_q(s3, p)
    dV = V_next - V_prev

    # === 7) Governance: Accept or Reject ===
    reject_code = None

    # Rule 1: Reject if V increased (Lyapunov monotonicity)
    if dV > 0:
        reject_code = "REJECT_VIOLATION_INCREASE"

    # Rule 2: Absorption at b=0
    if p.absorb_on_b0 and b_prev == 0 and dV > 0:
        reject_code = "REJECT_ABSORB_B0_DV_POS"

    # === Build receipt ===
    if reject_code is not None:
        # === REJECTED: Return original state, no chain advance ===
        receipt_obj = {
            "version": p.version,
            "prev_state_hash": prev_hash.hex(),
            "next_state_hash": prev_hash.hex(),
            "V_prev_q": int(V_prev),
            "V_next_q": int(V_prev),
            "dV_q": 0,
            "b_prev_q": int(b_prev),
            "b_next_q": int(b_prev),
            "db_q": 0,
            "projected": bool(projected),
            "reject_code": reject_code,
            "witness": witness,
        }
        chain_next = _hash_chain(chain_prev, receipt_obj, p)

        return s, GMIStepReceipt(
            version=p.version,
            prev_state_hash=prev_hash,
            next_state_hash=prev_hash,
            chain_prev=chain_prev,
            chain_next=chain_next,
            V_prev_q=int(V_prev),
            V_next_q=int(V_prev),
            dV_q=0,
            b_prev_q=int(b_prev),
            b_next_q=int(b_prev),
            db_q=0,
            projected=bool(projected),
            reject_code=reject_code,
            witness=witness,
        )

    # === ACCEPTED ===
    next_hash = _hash_state(s3, p)
    receipt_obj = {
        "version": p.version,
        "prev_state_hash": prev_hash.hex(),
        "next_state_hash": next_hash.hex(),
        "V_prev_q": int(V_prev),
        "V_next_q": int(V_next),
        "dV_q": int(dV),
        "b_prev_q": int(b_prev),
        "b_next_q": int(b_next),
        "db_q": int(b_next - b_prev),
        "projected": bool(projected),
        "reject_code": None,
        "witness": {**witness, "tau_support_count": len(rho_high)},
    }
    chain_next = _hash_chain(chain_prev, receipt_obj, p)

    return s3, GMIStepReceipt(
        version=p.version,
        prev_state_hash=prev_hash,
        next_state_hash=next_hash,
        chain_prev=chain_prev,
        chain_next=chain_next,
        V_prev_q=int(V_prev),
        V_next_q=int(V_next),
        dV_q=int(dV),
        b_prev_q=int(b_prev),
        b_next_q=int(b_next),
        db_q=int(b_next - b_prev),
        projected=bool(projected),
        reject_code=None,
        witness={**witness, "tau_support_count": len(rho_high)},
    )
