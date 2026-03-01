"""
Planner Proposer - Integrates MPC Planner into CLATL Runtime

This proposer wraps the Phase 3 MPC planner and produces proposals
that are compatible with the existing CLATL governor interface.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import hashlib

# Import from planning
from cnsc_haai.planning import (
    PlannerConfig,
    plan_and_select,
    is_planning_enabled,
)

# Import from tasks
from cnsc_haai.tasks.gridworld_env import GridWorldState
from cnsc_haai.tasks.task_loss import V_task_distance

# Import from GMI types
from cnsc_haai.gmi.types import GMIState, GMIAction

# Import from agent interfaces
from cnsc_haai.agent.proposer_iface import TaskProposal, ExplorationParams


# =============================================================================
# Planner Proposer
# =============================================================================

@dataclass
class PlannerProposer:
    """
    A TaskProposer that uses MPC planning for action selection.
    
    This proposer:
    1. Uses the planner to select actions (multi-step lookahead)
    2. Produces proposals compatible with CLATL governor
    3. Tracks planning costs and receipts
    """
    planner_config: PlannerConfig
    exploration_params: ExplorationParams
    use_planning: bool = True
    min_budget_for_planning: int = 10
    
    def __post_init__(self):
        """Initialize proposer."""
        self._current_goal: Optional[Tuple[int, int]] = None
        self._hazards: List[Tuple[int, int]] = []
        self._grid_bounds: Tuple[int, int] = (10, 10)
    
    def set_goal(self, goal: Tuple[int, int]) -> None:
        """Set the current goal position."""
        self._current_goal = goal
    
    def set_hazards(self, hazards: List[Tuple[int, int]]) -> None:
        """Set hazard positions."""
        self._hazards = hazards
    
    def set_grid_bounds(self, bounds: Tuple[int, int]) -> None:
        """Set grid bounds."""
        self._grid_bounds = bounds
    
    def propose(
        self,
        state: GridWorldState,
        gmi_state: GMIState,
    ) -> List[TaskProposal]:
        """
        Generate proposals using MPC planning.
        
        This wraps the planner to produce proposals compatible with the governor.
        
        Args:
            state: Current gridworld state
            gmi_state: Current GMI state
        
        Returns:
            List of TaskProposal (typically just the planned action)
        """
        # Determine if we should use planning
        should_plan = (
            self.use_planning and 
            is_planning_enabled(gmi_state, self.min_budget_for_planning)
        )
        
        if not should_plan or self._current_goal is None:
            # Fall back to default proposal
            return self._create_default_proposals(gmi_state)
        
        # Run planner
        result = plan_and_select(
            state=gmi_state,
            planner_config=self.planner_config,
            goal_position=self._current_goal,
            hazard_mask=self._create_hazard_mask(),
        )
        
        # Convert planner result to proposals
        proposals = self._create_proposals_from_result(result, gmi_state)
        
        return proposals
    
    def _create_default_proposals(self, gmi_state: GMIState) -> List[TaskProposal]:
        """Create default proposals when planning is disabled."""
        # Simple default: stay in place
        proposals = []
        
        # Add Stay proposal
        proposals.append(TaskProposal(
            action="Stay",
            drift_score=0,
            V_task_predicted=0,
            risk_score=0,
            coherence_score=0,
            exploration_bonus=0,
            hash=b"default",
        ))
        
        return proposals
    
    def _create_proposals_from_result(
        self,
        result,
        gmi_state: GMIState,
    ) -> List[TaskProposal]:
        """Convert planner result to proposals."""
        proposals = []
        
        # Create proposal from planned action
        action = result.action_name
        budget_after = result.budget_after_planning
        
        # Compute predicted task value (simplified)
        V_task = 0
        if self._current_goal and gmi_state.theta:
            pos = (gmi_state.theta[0][0], gmi_state.theta[0][1] if len(gmi_state.theta[0]) > 1 else 0)
            V_task = abs(pos[0] - self._current_goal[0]) + abs(pos[1] - self._current_goal[1])
        
        # Create proposal
        proposal = TaskProposal(
            action=action,
            drift_score=0,
            V_task_predicted=V_task,
            risk_score=0,
            coherence_score=gmi_state.b,  # Use budget as proxy
            exploration_bonus=0,
            hash=result.receipts.decision_receipt.chosen_plan_hash.encode() if result.receipts else b"planner",
        )
        
        proposals.append(proposal)
        
        # Also add Stay as backup
        proposals.append(TaskProposal(
            action="Stay",
            drift_score=0,
            V_task_predicted=V_task,
            risk_score=0,
            coherence_score=budget_after,
            exploration_bonus=0,
            hash=b"stay",
        ))
        
        return proposals
    
    def _create_hazard_mask(self):
        """Create hazard mask for planner."""
        if not self._hazards:
            return None
        
        # Create a simple 2D grid
        rows, cols = self._grid_bounds
        mask = [[0] * cols for _ in range(rows)]
        
        for (r, c) in self._hazards:
            if 0 <= r < rows and 0 <= c < cols:
                mask[r][c] = 1
        
        return mask


# =============================================================================
# Factory Functions
# =============================================================================

def create_planner_proposer(
    m_max: int = 10,
    H_max: int = 5,
    hazard_positions: List[Tuple[int, int]] = None,
    grid_bounds: Tuple[int, int] = (10, 10),
    min_budget: int = 10,
) -> PlannerProposer:
    """Create a planner proposer with default configuration."""
    config = PlannerConfig(
        m_max=m_max,
        H_max=H_max,
        hazard_positions=tuple(hazard_positions) if hazard_positions else (),
        grid_bounds=grid_bounds,
    )
    
    return PlannerProposer(
        planner_config=config,
        exploration_params=ExplorationParams(),
        use_planning=True,
        min_budget_for_planning=min_budget,
    )


# =============================================================================
# Integration Helper
# =============================================================================

def create_hybrid_proposer(
    reactive_proposer,  # TaskProposer
    planner_proposer: PlannerProposer,
    switch_to_planning_budget: int = 100,
) -> "HybridProposer":
    """
    Create a hybrid proposer that uses reactive proposals until
    budget is high enough, then switches to planning.
    
    Args:
        reactive_proposer: Existing TaskProposer for Phase 2
        planner_proposer: PlannerProposer for Phase 3
        switch_to_planning_budget: Budget threshold to enable planning
    
    Returns:
        Hybrid proposer that switches between reactive and planning
    """
    return HybridProposer(
        reactive=reactive_proposer,
        planner=planner_proposer,
        switch_threshold=switch_to_planning_budget,
    )


@dataclass
class HybridProposer:
    """
    Hybrid proposer that switches between reactive and planning based on budget.
    """
    reactive: "TaskProposer"  # Forward reference
    planner: PlannerProposer
    switch_threshold: int
    
    def propose(
        self,
        state: GridWorldState,
        gmi_state: GMIState,
    ) -> List[TaskProposal]:
        """Propose using either reactive or planner based on budget."""
        if gmi_state.b >= self.switch_threshold:
            return self.planner.propose(state, gmi_state)
        else:
            return self.reactive.propose(state, gmi_state)
    
    def set_goal(self, goal: Tuple[int, int]) -> None:
        """Set goal for both proposers."""
        self.planner.set_goal(goal)
    
    def set_hazards(self, hazards: List[Tuple[int, int]]) -> None:
        """Set hazards for planner."""
        self.planner.set_hazards(hazards)
