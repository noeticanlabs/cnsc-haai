"""
Tests for D0 Determinism.

Verifies that same request produces same response across multiple runs.
"""

import pytest
import sys
sys.path.insert(0, '/workspaces/cnsc-haai/src')

from npe.core.types import NPERequest, Budgets, Goal, Context
from npe.core.hashing import hash_request


class TestDeterminismD0:
    """Tests for D0 determinism tier."""
    
    def test_same_request_same_request_id(self):
        """Same request data produces same request_id."""
        request_data = {
            "spec": "NPE-REQUEST-1.0",
            "request_type": "propose",
            "domain": "gr",
            "determinism_tier": "d0",
            "seed": 42,
            "budgets": {
                "max_wall_ms": 1000,
                "max_candidates": 16,
                "max_evidence_items": 100,
                "max_search_expansions": 50,
            },
            "inputs": {
                "state": {
                    "state_hash": "abc123",
                    "step": 1,
                },
            },
        }
        
        # Compute hash 3 times
        hash1 = hash_request(request_data)
        hash2 = hash_request(request_data)
        hash3 = hash_request(request_data)
        
        assert hash1 == hash2 == hash3
        assert len(hash1) == 64
    
    def test_same_request_object_same_hash(self):
        """Same NPERequest object produces same hash."""
        request = NPERequest(
            spec="NPE-REQUEST-1.0",
            request_type="propose",
            domain="gr",
            determinism_tier="d0",
            seed=42,
            budgets=Budgets(),
            inputs={
                "state": {"state_hash": "abc123", "step": 1},
                "goals": [{"goal_type": "repair"}],
            },
        )
        
        # Convert to dict and hash multiple times
        request_dict = {
            "spec": request.spec,
            "request_type": request.request_type,
            "request_id": "",
            "domain": request.domain,
            "determinism_tier": request.determinism_tier,
            "seed": request.seed,
            "budgets": {
                "max_wall_ms": request.budgets.max_wall_ms,
                "max_candidates": request.budgets.max_candidates,
                "max_evidence_items": request.budgets.max_evidence_items,
                "max_search_expansions": request.budgets.max_search_expansions,
            },
            "inputs": request.inputs,
        }
        
        hash1 = hash_request(request_dict)
        hash2 = hash_request(request_dict)
        
        assert hash1 == hash2
    
    def test_different_seed_different_hash(self):
        """Different seeds produce different hashes."""
        base_data = {
            "spec": "NPE-REQUEST-1.0",
            "request_type": "propose",
            "domain": "gr",
            "determinism_tier": "d0",
            "budgets": {"max_wall_ms": 1000, "max_candidates": 16},
            "inputs": {},
        }
        
        data1 = dict(base_data)
        data1["seed"] = 1
        
        data2 = dict(base_data)
        data2["seed"] = 2
        
        hash1 = hash_request(data1)
        hash2 = hash_request(data2)
        
        assert hash1 != hash2
    
    def test_goals_order_affects_hash(self):
        """Goals order affects hash (as it should for determinism)."""
        data1 = {
            "spec": "NPE-REQUEST-1.0",
            "request_type": "propose",
            "domain": "gr",
            "seed": 42,
            "budgets": {},
            "inputs": {
                "goals": [
                    {"goal_type": "repair"},
                    {"goal_type": "optimize"},
                ]
            },
        }
        
        data2 = {
            "spec": "NPE-REQUEST-1.0",
            "request_type": "propose",
            "domain": "gr",
            "seed": 42,
            "budgets": {},
            "inputs": {
                "goals": [
                    {"goal_type": "optimize"},
                    {"goal_type": "repair"},
                ]
            },
        }
        
        hash1 = hash_request(data1)
        hash2 = hash_request(data2)
        
        # Different order should produce different hash
        assert hash1 != hash2
    
    def test_request_parsing_deterministic(self):
        """Parsing request multiple times produces same result."""
        request_data = {
            "spec": "NPE-REQUEST-1.0",
            "request_type": "propose",
            "request_id": "",
            "domain": "gr",
            "determinism_tier": "d0",
            "seed": 12345,
            "budgets": {
                "max_wall_ms": 500,
                "max_candidates": 8,
            },
            "inputs": {
                "context": {
                    "risk_posture": "conservative",
                    "scenario_id": "scenario_001",
                }
            },
        }
        
        # Parse 3 times
        results = []
        for _ in range(3):
            # Reconstruct request to ensure fresh parsing
            request = NPERequest(
                spec=request_data["spec"],
                request_type=request_data["request_type"],
                request_id="",  # Will be computed
                domain=request_data["domain"],
                determinism_tier=request_data["determinism_tier"],
                seed=request_data["seed"],
                budgets=Budgets(
                    max_wall_ms=request_data["budgets"]["max_wall_ms"],
                    max_candidates=request_data["budgets"]["max_candidates"],
                ),
                inputs=request_data["inputs"],
            )
            results.append(request.request_id)
        
        # All request IDs should be identical
        assert results[0] == results[1] == results[2]


class TestCandidateDeterminism:
    """Tests for candidate generation determinism."""
    
    def test_same_candidate_structure_same_hash(self):
        """Same candidate structure produces same hash."""
        from npe.core.hashing import hash_candidate
        
        candidate1 = {
            "candidate_type": "repair",
            "domain": "gr",
            "input_state_hash": "abc",
            "constraints_hash": "def",
            "payload_hash": "ghi",
            "payload": {"action": "adjust"},
        }
        
        candidate2 = {
            "candidate_type": "repair",
            "domain": "gr",
            "input_state_hash": "abc",
            "constraints_hash": "def",
            "payload_hash": "ghi",
            "payload": {"action": "adjust"},
        }
        
        hash1 = hash_candidate(candidate1)
        hash2 = hash_candidate(candidate2)
        
        assert hash1 == hash2
    
    def test_different_payload_different_hash(self):
        """Different payload produces different hash."""
        from npe.core.hashing import hash_candidate
        
        candidate1 = {
            "candidate_type": "repair",
            "domain": "gr",
            "input_state_hash": "abc",
            "constraints_hash": "def",
            "payload_hash": "ghi",
            "payload": {"action": "adjust", "param": 1},
        }
        
        candidate2 = {
            "candidate_type": "repair",
            "domain": "gr",
            "input_state_hash": "abc",
            "constraints_hash": "def",
            "payload_hash": "ghi",
            "payload": {"action": "adjust", "param": 2},
        }
        
        hash1 = hash_candidate(candidate1)
        hash2 = hash_candidate(candidate2)
        
        assert hash1 != hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
