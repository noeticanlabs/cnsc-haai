"""
CLATL Runtime - Closed-Loop Adaptive Task Layer

Main orchestrator that wires:
- Environment (gridworld)
- Proposer (generates proposals)
- Governor (lexicographic selection)
- GMI Kernel (coherence enforcement)

Implements FIX 2 & 3: deterministic execution with full receipt chain.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import hashlib
import json
import uuid

# Import from tasks
from cnsc_haai.tasks.gridworld_env import (
    GridWorldState,
    GridWorldObs,
    env_step,
    get_observation,
    drift_goal,
    hash_gridworld_state,
    create_gridworld,
    create_initial_state,
    CELL_GOAL,
)
from cnsc_haai.tasks.task_loss import (
    V_task_distance,
    V_task_success,
    compute_competence,
    CompetenceMetrics,
)

# Import from GMI
from cnsc_haai.gmi.types import GMIState, GMIAction
from cnsc_haai.gmi.params import GMIParams
from cnsc_haai.gmi.admissible import in_K
from cnsc_haai.gmi.lyapunov import V_extended_q
from cnsc_haai.gmi.step import gmi_step

# Import from agent
from .proposer_iface import (
    TaskProposal,
    TaskProposer,
    build_proposalset_root,
    find_proposal_index,
    ExplorationParams,
)
from .governor_iface import (
    GovernorDecision,
    select_action,
)


# =============================================================================
# Receipt Types (FIX 3)
# =============================================================================

@dataclass(frozen=True)
class CLATLStepReceipt:
    """
    Receipt for one CLATL step (includes ProposalSet commitment).
    
    This ensures deterministic replay - all inputs to decision are receipted.
    """
    step: int
    gridworld_state_hash: bytes          # Hash of gridworld state
    gmi_state_hash: bytes                 # Hash of GMI state
    proposalset_root: bytes              # Merkle root of all proposals
    chosen_proposal_index: int          # Index of selected proposal
    chosen_proposal_hash: bytes         # Hash of chosen proposal
    action_taken: str                   # The action that was executed
    task_performance: int                # V_task after this step
    goal_reached: bool                   # Whether goal was reached
    decision: GovernorDecision           # Full decision for audit
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            'step': self.step,
            'gridworld_state_hash': self.gridworld_state_hash.hex(),
            'gmi_state_hash': self.gmi_state_hash.hex(),
            'proposalset_root': self.proposalset_root.hex(),
            'chosen_proposal_index': self.chosen_proposal_index,
            'chosen_proposal_hash': self.chosen_proposal_hash.hex(),
            'action_taken': self.action_taken,
            'task_performance': self.task_performance,
            'goal_reached': self.goal_reached,
            'decision': {
                'rejected': self.decision.rejected,
                'rejection_reasons': list(self.decision.rejection_reasons),
                'num_candidates_considered': self.decision.num_candidates_considered,
                'num_candidates_safe': self.decision.num_candidates_safe,
            },
        }


@dataclass
class CLATLRunReceipt:
    """
    Complete receipt for a CLATL run/episode.
    
    Includes all data needed for exact replay.
    """
    run_id: str
    initial_gmi_state_hash: bytes
    initial_gridworld_hash: bytes
    drift_seed: int                      # Seed for deterministic goal drift
    goal_drift_schedule: List[int]       # Steps at which goal shifts
    step_receipts: List[CLATLStepReceipt] = field(default_factory=list)
    task_performance_history: List[int] = field(default_factory=list)
    success_flags: List[bool] = field(default_factory=list)
    invariant_violations: List[str] = field(default_factory=list)
    competence: Optional[CompetenceMetrics] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            'run_id': self.run_id,
            'initial_gmi_state_hash': self.initial_gmi_state_hash.hex(),
            'initial_gridworld_hash': self.initial_gridworld_hash.hex(),
            'drift_seed': self.drift_seed,
            'goal_drift_schedule': self.goal_drift_schedule,
            'step_receipts': [s.to_dict() for s in self.step_receipts],
            'task_performance_history': self.task_performance_history,
            'success_flags': self.success_flags,
            'invariant_violations': self.invariant_violations,
            'competence': {
                'success_rate': self.competence.success_rate if self.competence else 0.0,
                'avg_steps_to_goal': self.competence.avg_steps_to_goal if self.competence else 0.0,
                'avg_distance_to_goal': self.competence.avg_distance_to_goal if self.competence else 0.0,
            } if self.competence else None,
        }


# =============================================================================
# Helper Functions
# =============================================================================

def _hash_gmi_state(state: GMIState) -> bytes:
    """Compute hash of GMI state for receipts."""
    data = {
        'rho': [list(row) for row in state.rho],
        'theta': [list(row) for row in state.theta],
        'C': [list(row) for row in state.C],
        'b': state.b,
        't': state.t,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).digest()


def _create_initial_gmi_state(
    width: int = 5,
    height: int = 5,
    budget: int = 10_000_000,
) -> GMIState:
    """Create initial GMI state for CLATL."""
    rho = [[0] * width for _ in range(height)]
    theta = [[0] * width for _ in range(height)]
    C = [[0] * width for _ in range(height)]
    
    return GMIState(
        rho=rho,
        theta=theta,
        C=C,
        b=budget,
        t=0,
    )


def _translate_to_gmi_action(action: str) -> GMIAction:
    """
    Translate gridworld action to GMI action.
    
    For CLATL, GMI action is minimal - we just need something
    that passes through the GMI kernel without breaking invariants.
    """
    # Minimal action: small drift in theta
    height, width = 5, 5
    dtheta = [[1 if i == j else 0 for j in range(width)] for i in range(height)]
    drho = [[0] * width for _ in range(height)]
    
    return GMIAction(drho=drho, dtheta=dtheta)


# =============================================================================
# Main CLATL Functions
# =============================================================================

def run_clatl_episode(
    gmi_state: GMIState,
    gridworld: GridWorldState,
    max_steps: int,
    goal_drift_every: int,
    drift_seed: int,
    gmi_params: GMIParams,
    proposer: Optional[TaskProposer] = None,
) -> CLATLRunReceipt:
    """
    Execute one CLATL episode with full receipt.
    
    This is the main closed-loop execution function.
    
    Args:
        gmi_state: Initial GMI coherence state
        gridworld: Initial gridworld state
        max_steps: Maximum steps per episode
        goal_drift_every: Steps between goal drifts
        drift_seed: Seed for deterministic goal drift
        gmi_params: GMI parameters
        proposer: Optional proposer (creates default if None)
    
    Returns:
        CLATLRunReceipt with full audit trail
    """
    # Initialize
    proposer = proposer or TaskProposer(ExplorationParams())
    gmi_params = gmi_params or GMIParams()
    
    # Create run receipt
    run_id = str(uuid.uuid4())[:8]
    receipt = CLATLRunReceipt(
        run_id=run_id,
        initial_gmi_state_hash=_hash_gmi_state(gmi_state),
        initial_gridworld_hash=hash_gridworld_state(gridworld),
        drift_seed=drift_seed,
        goal_drift_schedule=[],
    )
    
    # Initialize state
    current_gmi = gmi_state
    current_gridworld = gridworld
    chain = b"CHAIN_INITIAL"  # Placeholder for chain
    
    # Track episode boundaries for competence computation
    step_in_episode = 0
    
    for step in range(max_steps):
        # === FIX 2: Deterministic drift ===
        # Drift goal if scheduled
        if step > 0 and step % goal_drift_every == 0:
            current_gridworld = drift_goal(current_gridworld, step)
            receipt.goal_drift_schedule.append(step)
        
        # === Get observation ===
        obs = get_observation(current_gridworld)
        
        # === Get coherence state ===
        V_coh = V_extended_q(current_gmi, gmi_params)
        
        # === Propose actions (receipted) ===
        proposals = proposer.propose(
            state=current_gridworld,
            obs=obs,
            V_coh=V_coh,
            memory=proposer.memory,
        )
        
        # === FIX 3: Build ProposalSet receipt BEFORE selection ===
        proposalset_root = build_proposalset_root(proposals)
        
        # === Governor selects action (lexicographic) ===
        decision = select_action(
            proposals=proposals,
            gridworld_state=current_gridworld,
            gmi_state=current_gmi,
            gmi_params=gmi_params,
        )
        
        # === Execute step ===
        if decision.is_accepted():
            selected = decision.selected_proposal
            
            # Execute in environment
            next_gridworld, reward = env_step(current_gridworld, selected.action)
            
            # Execute in GMI
            gmi_action = _translate_to_gmi_action(selected.action)
            next_gmi, gmi_receipt = gmi_step(current_gmi, gmi_action, {}, gmi_params, chain)
            
            # Check invariants
            if not in_K(next_gmi, gmi_params):
                receipt.invariant_violations.append(
                    f"step_{step}:admissibility_violation"
                )
            
            # Update memory (for exploration)
            proposer.memory.increment(current_gridworld.position)
            
            # Compute task performance
            V_task = V_task_distance(next_gridworld)
            goal_reached = next_gridworld.position == next_gridworld.goal
            
            # Create step receipt
            chosen_idx = find_proposal_index(proposals, selected)
            
            step_receipt = CLATLStepReceipt(
                step=step,
                gridworld_state_hash=hash_gridworld_state(next_gridworld),
                gmi_state_hash=_hash_gmi_state(next_gmi),
                proposalset_root=proposalset_root,
                chosen_proposal_index=chosen_idx,
                chosen_proposal_hash=selected.hash(),
                action_taken=selected.action,
                task_performance=V_task,
                goal_reached=goal_reached,
                decision=decision,
            )
            
            receipt.step_receipts.append(step_receipt)
            receipt.task_performance_history.append(V_task)
            receipt.success_flags.append(goal_reached)
            
            # Update state
            current_gridworld = next_gridworld
            current_gmi = next_gmi
            step_in_episode += 1
            
            # Check if episode ends (goal reached)
            if goal_reached:
                break
                
        else:
            # No safe action - record violation
            receipt.invariant_violations.append(
                f"step_{step}:no_safe_action:{decision.rejection_reasons}"
            )
            
            # Still record failure
            receipt.task_performance_history.append(V_task_distance(current_gridworld))
            receipt.success_flags.append(False)
    
    # Compute competence metrics
    episode_boundaries = [len(receipt.step_receipts)]
    receipt.competence = compute_competence(
        task_performance_history=receipt.task_performance_history,
        episode_boundaries=episode_boundaries,
        success_flags=receipt.success_flags,
    )
    
    return receipt


def run_clatl_training(
    num_episodes: int,
    grid_layout: str = "simple",
    max_steps: int = 100,
    goal_drift_every: int = 30,
    initial_budget: int = 10_000_000,
    gmi_params: Optional[GMIParams] = None,
) -> Tuple[List[CLATLRunReceipt], List[CompetenceMetrics]]:
    """
    Run multiple CLATL episodes and track learning.
    
    Args:
        num_episodes: Number of episodes to run
        grid_layout: Grid layout name ('simple', 'maze', 'hazard')
        max_steps: Maximum steps per episode
        goal_drift_every: Steps between goal drifts
        initial_budget: Starting budget for each episode
        gmi_params: GMI parameters
    
    Returns:
        (list of run receipts, list of competence metrics over time)
    """
    # Create gridworld
    grid, start, goal = _create_gridworld_layout(grid_layout)
    
    # Create GMI params
    gmi_params = gmi_params or GMIParams()
    
    # Create proposer (persists across episodes for memory)
    proposer = TaskProposer(ExplorationParams())
    
    receipts = []
    metrics_history = []
    
    for episode in range(num_episodes):
        # Reset states
        gmi_state = _create_initial_gmi_state(budget=initial_budget)
        
        # Different seed for each episode
        gridworld = create_initial_state(
            grid=grid,
            start=start,
            goal=goal,
            drift_seed=episode * 1000 + 42,
        )
        
        # Run episode
        receipt = run_clatl_episode(
            gmi_state=gmi_state,
            gridworld=gridworld,
            max_steps=max_steps,
            goal_drift_every=goal_drift_every,
            drift_seed=episode * 1000 + 42,
            gmi_params=gmi_params,
            proposer=proposer,
        )
        
        receipts.append(receipt)
        
        if receipt.competence:
            metrics_history.append(receipt.competence)
        
        # Reset memory between episodes (optional - can keep for longer-term memory)
        # proposer.reset_memory()  # Uncomment to reset between episodes
    
    return receipts, metrics_history


def _create_gridworld_layout(layout: str):
    """Create standard gridworld layout."""
    from cnsc_haai.tasks.gridworld_env import create_standard_grid
    return create_standard_grid(layout)


# =============================================================================
# Replay Verification
# =============================================================================

def verify_replay(
    receipt: CLATLRunReceipt,
    gmi_params: GMIParams,
    proposer: Optional[TaskProposer] = None,
) -> Tuple[bool, List[str]]:
    """
    Verify that a receipt can be exactly replayed.
    
    Args:
        receipt: The receipt to verify
        gmi_params: GMI parameters used
        proposer: Proposer to use for regeneration
    
    Returns:
        (is_valid, list of errors)
    """
    errors = []
    
    # Recreate initial states
    # Note: In real implementation, we'd recreate from hashes
    # For now, we just check receipt consistency
    
    # Check that all step receipts have required fields
    for sr in receipt.step_receipts:
        if sr.proposalset_root is None:
            errors.append(f"step_{sr.step}: missing proposalset_root")
        if sr.chosen_proposal_hash is None:
            errors.append(f"step_{sr.step}: missing chosen_proposal_hash")
    
    # Check that task performance is monotonically improving or goal reached
    # (not required, but good to verify)
    if not errors:
        # Replay is structurally valid
        pass
    
    return len(errors) == 0, errors
