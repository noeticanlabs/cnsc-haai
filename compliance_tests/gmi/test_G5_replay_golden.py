"""
G5: Replay + Golden Chain Compliance Test

Verifies that replay produces deterministic chain and state hashes.
This is critical for consensus verification.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cnsc_haai.gmi.replay import replay_episode


def test_replay_chain_is_deterministic(load_vector_fixture):
    """
    Test G5a: Running replay twice produces identical chain.
    
    This is essential for consensus - all nodes must agree on chain.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    # Run replay twice
    s_end1, chain1, receipts1 = replay_episode(s0, actions, ctx, p, chain0)
    s_end2, chain2, receipts2 = replay_episode(s0, actions, ctx, p, chain0)
    
    # Chain tips must match
    assert chain1 == chain2, "Chain must be deterministic"
    
    # Final receipts must match
    assert receipts1[-1].chain_next == receipts2[-1].chain_next, \
        "Final chain tip must match"
    assert receipts1[-1].next_state_hash == receipts2[-1].next_state_hash, \
        "Final state hash must match"


def test_replay_produces_valid_chain_sequence(load_vector_fixture):
    """
    Test G5b: Chain forms valid sequence.
    
    Each receipt's chain_prev should match previous receipt's chain_next.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    s_end, chain, receipts = replay_episode(s0, actions, ctx, p, chain0)
    
    # Check chain linkage
    prev_chain = chain0
    for i, r in enumerate(receipts):
        assert r.chain_prev == prev_chain, \
            f"Receipt {i}: chain_prev must match previous chain_next"
        prev_chain = r.chain_next
    
    # Final chain must match last receipt
    assert chain == receipts[-1].chain_next, "Final chain must match last receipt"


def test_replay_state_evolves(load_vector_fixture):
    """
    Test G5c: State evolves over replay.
    
    After multiple steps, state should have changed (unless all rejected).
    Time should advance by at least 1.
    """
    p, s0, actions, chain0 = load_vector_fixture("gmi_v1_5_case01.json")
    ctx = {}
    
    s_end, chain, receipts = replay_episode(s0, actions, ctx, p, chain0)
    
    # Time should advance by at least 1 (accepted steps only)
    assert s_end.t >= 1, "Time should advance by at least 1"


def test_multiple_vectors_deterministic(load_vector_fixture):
    """
    Test G5d: Both golden vectors produce deterministic results.
    """
    for vector_name in ["gmi_v1_5_case01.json", "gmi_v1_5_case02.json"]:
        p, s0, actions, chain0 = load_vector_fixture(vector_name)
        ctx = {}
        
        # Run twice
        s1, c1, r1 = replay_episode(s0, actions, ctx, p, chain0)
        s2, c2, r2 = replay_episode(s0, actions, ctx, p, chain0)
        
        assert c1 == c2, f"{vector_name}: chain must be deterministic"
        assert r1[-1].chain_next == r2[-1].chain_next, \
            f"{vector_name}: final tip must match"
