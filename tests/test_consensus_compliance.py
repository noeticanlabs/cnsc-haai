"""
Compliance Test Runner

Verifies consensus implementation against compliance vectors.
Run with: python -m pytest tests/test_consensus_compliance.py -v
"""

import json
import pytest
from pathlib import Path
from typing import List, Dict, Any

# Import consensus modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cnsc_haai.consensus.jcs import jcs_canonical_bytes
from cnsc_haai.consensus.hash import sha256, sha256_prefixed, decode_sha256_prefixed
from cnsc_haai.consensus.merkle import MerkleTree, verify_inclusion_proof_prefixed
from cnsc_haai.consensus.chain import chain_hash_v1, chain_hash_sequence
from cnsc_haai.consensus.codec import strip_to_core, encode_micro_leaf, MicroLeafCodec
from cnsc_haai.ats.verifier_state import SlabRegistry, SlabState, DisputeStatus


# Path to compliance vectors
VECTOR_DIR = Path(__file__).parent.parent / "compliance_tests" / "ats_slab" / "vector_bundle_v1"


class TestJCSCanonicalization:
    """Test JCS canonicalization."""
    
    def test_simple_object(self):
        """Test simple object canonicalization."""
        obj = {"b": 2, "a": 1}
        result = jcs_canonical_bytes(obj)
        # Keys should be sorted
        assert b'"a":1' in result
        assert b'"b":2' in result
    
    def test_deterministic(self):
        """Test encoding is deterministic."""
        obj = {"z": 1, "a": 2, "m": 3}
        
        first = jcs_canonical_bytes(obj)
        second = jcs_canonical_bytes(json.loads(first.decode("utf-8")))
        
        assert first == second
    
    def test_array_order_preserved(self):
        """Test array order is preserved."""
        obj = [3, 1, 2]
        result = jcs_canonical_bytes(obj)
        assert result == b"[3,1,2]"


class TestSHA256Hashing:
    """Test SHA256 hashing with prefix."""
    
    def test_sha256_prefixed(self):
        """Test prefixed hash."""
        result = sha256_prefixed(b"test")
        assert result.startswith("sha256:")
        assert len(result) == 7 + 64  # "sha256:" + 64 hex
    
    def test_decode_prefixed(self):
        """Test decoding prefixed hash."""
        original = b"test data"
        prefixed = sha256_prefixed(original)
        
        decoded = decode_sha256_prefixed(prefixed)
        assert decoded == sha256(original)
    
    def test_invalid_prefix_raises(self):
        """Test invalid prefix raises error."""
        with pytest.raises(ValueError, match="Invalid digest format"):
            decode_sha256_prefixed("abc123")


class TestMerkleTree:
    """Test Merkle tree construction."""
    
    def test_empty_tree(self):
        """Test empty tree returns zero hash."""
        tree = MerkleTree()
        root = tree.build([])
        assert root == bytes(32)
    
    def test_single_leaf(self):
        """Test single leaf tree."""
        tree = MerkleTree()
        leaf = b"test leaf"
        root = tree.build([leaf])
        assert len(root) == 32
    
    def test_three_leaves(self):
        """Test tree with 3 leaves."""
        leaves = [b"leaf1", b"leaf2", b"leaf3"]
        tree = MerkleTree()
        root = tree.build(leaves)
        assert len(root) == 32
    
    def test_merkle_proof(self):
        """Test merkle proof generation and verification."""
        leaves = [b"leaf0", b"leaf1", b"leaf2"]
        tree = MerkleTree()
        root = tree.build(leaves)
        
        proof = tree.get_proof(1)  # Get proof for leaf at index 1
        assert len(proof) > 0
        
        # Verify proof - use raw root bytes, NOT sha256_prefixed(root)
        # The root is already a hash from build(), no need to re-hash
        verified = verify_inclusion_proof_prefixed(
            leaves[1],
            [{"side": s, "hash": f"sha256:{h}"} for s, h in proof],
            root
        )
        assert verified


class TestChainHashing:
    """Test chain hashing v1."""
    
    def test_genesis_chain(self):
        """Test genesis receipt chain."""
        genesis = bytes(32)
        core = {"step_index": 1, "data": "test"}
        
        chain_hash = chain_hash_v1(genesis, core)
        assert len(chain_hash) == 32
    
    def test_chain_sequence(self):
        """Test chain hash sequence."""
        cores = [
            {"step_index": 1, "data": "a"},
            {"step_index": 2, "data": "b"},
            {"step_index": 3, "data": "c"},
        ]
        
        hashes = chain_hash_sequence(cores)
        assert len(hashes) == 3
        
        # Each should be unique
        assert hashes[0] != hashes[1]
        assert hashes[1] != hashes[2]


class TestMicroLeafCodec:
    """Test micro leaf codec."""
    
    def test_strip_non_consensus(self):
        """Test stripping non-consensus fields."""
        receipt = {
            "schema_id": "receipt.ats.v3",
            "timestamp": "2026-01-01T00:00:00Z",  # Should be stripped
            "episode_id": "ep_001",  # Should be stripped
            "receipt_body": {
                "risk_before": {"raw": 1000},
            }
        }
        
        core = strip_to_core(receipt)
        
        assert "timestamp" not in core
        assert "episode_id" not in core
        assert "schema_id" in core
        assert "receipt_body" in core
    
    def test_codec_id(self):
        """Test codec ID is correct."""
        codec = MicroLeafCodec()
        assert codec.codec_id == "coh.micro.codec.ats_receipt_core.v1"


class TestSlabFSM:
    """Test slab FSM state machine."""
    
    def test_slab_lifecycle(self):
        """Test complete slab lifecycle."""
        registry = SlabRegistry()
        
        # Register slab
        state = registry.register_slab(
            slab_receipt_hash="sha256:abc123",
            slab_id="slab_001",
            window_start=1000,
            window_end=2000,
            current_height=1000
        )
        
        assert state.state == SlabState.ACTIVE
        
        # Try to finalize too early
        can_finalize = state.check_finalizable(current_height=1500, retention_period=100)
        assert not can_finalize
        
        # Advance to finalizable
        can_finalize = state.check_finalizable(current_height=2100, retention_period=100)
        assert can_finalize
        
        # Finalize
        authorized, reason = state.step_finalize(
            claimed_window_end=2000,
            current_height=2100,
            min_budget=1000,
            current_budget=2000
        )
        assert authorized
        assert state.can_delete()
    
    def test_fraud_proof_blocks_finalize(self):
        """Test fraud proof blocks finalization."""
        registry = SlabRegistry()
        
        state = registry.register_slab(
            slab_receipt_hash="sha256:abc123",
            slab_id="slab_001",
            window_start=1000,
            window_end=2000,
            current_height=1000
        )
        
        # Add fraud proof
        state.step_fraud_proof("sha256:fraud123", current_height=1500)
        
        assert state.dispute_status == DisputeStatus.DISPUTED
        assert state.state == SlabState.DISPUTED
        
        # Try to finalize - should fail
        authorized, reason = state.step_finalize(
            claimed_window_end=2000,
            current_height=2100,
            min_budget=1000,
            current_budget=2000
        )
        
        assert not authorized
        assert "dispute" in reason.lower()


class TestComplianceVectors:
    """Test against actual compliance vectors."""
    
    @pytest.fixture
    def vectors(self):
        """Load compliance vectors."""
        vectors_dir = VECTOR_DIR
        
        with open(vectors_dir / "policy.json") as f:
            policy = json.load(f)
        
        micro_receipts = []
        with open(vectors_dir / "micro_receipts.jsonl") as f:
            for line in f:
                micro_receipts.append(json.loads(line))
        
        with open(vectors_dir / "expected_micro_merkle_root.txt") as f:
            expected_root = f.read().strip()
        
        chain_hashes = []
        with open(vectors_dir / "expected_chain_hash_sequence.txt") as f:
            for line in f:
                chain_hashes.append(line.strip())
        
        return {
            "policy": policy,
            "micro_receipts": micro_receipts,
            "expected_root": expected_root,
            "chain_hashes": chain_hashes,
        }
    
    def test_policy_schema(self, vectors):
        """Test policy loads correctly."""
        policy = vectors["policy"]
        assert policy["version"] == "1.0.0"
        assert "retention_period_blocks" in policy
    
    def test_micro_receipts_count(self, vectors):
        """Test we have expected number of micro receipts."""
        assert len(vectors["micro_receipts"]) == 3
    
    def test_chain_hash_sequence_length(self, vectors):
        """Test chain hash sequence includes genesis."""
        # Should have genesis + 3 receipts = 4
        assert len(vectors["chain_hashes"]) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
