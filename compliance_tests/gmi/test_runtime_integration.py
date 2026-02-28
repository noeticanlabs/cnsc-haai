"""
GMI v1.6 Runtime Integration Tests

Tests the full NPE → TGS → Consensus loop.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cnsc_haai.gmi import (
    GMIState, GMIAction, GMIStepReceipt,
    Proposal, GateDecision, WorkUnits, GMIRuntimeReceipt,
    GMIParams, gmi_tick, GMIRuntime,
)


def test_runtime_tick_with_proposals():
    """Test runtime tick with proposals."""
    # Create initial state
    state = GMIState(
        rho=[[5, 5], [5, 5]],
        theta=[[0, 0], [0, 0]],
        C=[[0, 0], [0, 0]],
        b=3000000,
        t=0,
    )
    
    # Create proposals
    proposals = [
        Proposal(
            proposal_id="prop_1",
            action=GMIAction(
                drho=[[1, 1], [1, 1]],
                dtheta=[[1, 1], [1, 1]],
            ),
            score=100,
            metadata={},
        ),
    ]
    
    ctx = {}
    chain_prev = b'\x00' * 32
    params = GMIParams()
    
    # Execute tick
    new_state, receipt = gmi_tick(state, b'', proposals, ctx, chain_prev, params)
    
    # Verify receipt
    assert isinstance(receipt, GMIRuntimeReceipt)
    assert receipt.proposal_count == 1
    assert receipt.selected_proposal_id == "prop_1"
    assert receipt.step_receipt is not None


def test_runtime_tick_no_proposals():
    """Test runtime tick with no proposals."""
    state = GMIState(
        rho=[[5, 5], [5, 5]],
        theta=[[0, 0], [0, 0]],
        C=[[0, 0], [0, 0]],
        b=3000000,
        t=0,
    )
    
    proposals = []
    ctx = {}
    chain_prev = b'\x00' * 32
    params = GMIParams()
    
    new_state, receipt = gmi_tick(state, b'', proposals, ctx, chain_prev, params)
    
    assert receipt.proposal_count == 0
    assert receipt.selected_proposal_id is None


def test_runtime_class():
    """Test GMIRuntime class."""
    runtime = GMIRuntime()
    
    state = GMIState(
        rho=[[5, 5], [5, 5]],
        theta=[[0, 0], [0, 0]],
        C=[[0, 0], [0, 0]],
        b=3000000,
        t=0,
    )
    
    runtime.reset(state)
    
    assert runtime.state is not None
    assert runtime.get_receipt_count() == 0
    
    # Execute tick
    proposals = [
        Proposal(
            proposal_id="test_1",
            action=GMIAction(
                drho=[[1, 1], [1, 1]],
                dtheta=[[1, 1], [1, 1]],
            ),
            score=50,
            metadata={},
        ),
    ]
    
    receipt = runtime.tick(proposals)
    
    assert runtime.get_receipt_count() == 1
    assert receipt.step_receipt is not None


def test_proposal_selection_deterministic():
    """Test that proposal selection is deterministic."""
    state = GMIState(
        rho=[[5, 5], [5, 5]],
        theta=[[0, 0], [0, 0]],
        C=[[0, 0], [0, 0]],
        b=3000000,
        t=0,
    )
    
    proposals = [
        Proposal(proposal_id="low", action=GMIAction(drho=[[0, 0], [0, 0]], dtheta=[[0, 0], [0, 0]]), score=10, metadata={}),
        Proposal(proposal_id="high", action=GMIAction(drho=[[1, 1], [1, 1]], dtheta=[[1, 1], [1, 1]]), score=100, metadata={}),
    ]
    
    chain_prev = b'\x00' * 32
    params = GMIParams()
    
    # Run twice
    _, r1 = gmi_tick(state, b'', proposals, {}, chain_prev, params)
    _, r2 = gmi_tick(state, b'', proposals, {}, chain_prev, params)
    
    # Same proposal selected (deterministic)
    assert r1.selected_proposal_id == r2.selected_proposal_id == "high"


def test_work_units_tracked():
    """Test that work units are tracked."""
    state = GMIState(
        rho=[[5, 5], [5, 5]],
        theta=[[0, 0], [0, 0]],
        C=[[0, 0], [0, 0]],
        b=3000000,
        t=0,
    )
    
    proposals = [
        Proposal(
            proposal_id="work_test",
            action=GMIAction(drho=[[1, 1], [1, 1]], dtheta=[[1, 1], [1, 1]]),
            score=100,
            metadata={},
        ),
    ]
    
    _, receipt = gmi_tick(state, b'', proposals, {}, b'\x00' * 32, GMIParams())
    
    # Work units should be tracked
    assert receipt.work_units is not None
    assert receipt.work_units.total() > 0
    assert receipt.total_work_q > 0


def test_chain_advances():
    """Test that chain advances on each tick."""
    runtime = GMIRuntime()
    
    state = GMIState(
        rho=[[5, 5], [5, 5]],
        theta=[[0, 0], [0, 0]],
        C=[[0, 0], [0, 0]],
        b=3000000,
        t=0,
    )
    
    runtime.reset(state)
    
    initial_chain = runtime.get_chain_tip()
    
    # Execute tick
    proposals = [
        Proposal(
            proposal_id="chain_test",
            action=GMIAction(drho=[[1, 1], [1, 1]], dtheta=[[1, 1], [1, 1]]),
            score=100,
            metadata={},
        ),
    ]
    
    receipt = runtime.tick(proposals)
    
    new_chain = runtime.get_chain_tip()
    
    # Chain should have advanced
    assert new_chain != initial_chain
    assert receipt.step_receipt.chain_next == new_chain
