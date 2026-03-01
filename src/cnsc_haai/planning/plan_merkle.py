"""
Plan Merkle - Merkle Tree for Plan Commitment

Builds a Merkle tree over plan hashes for efficient commitment
and membership verification.
"""

from __future__ import annotations
from typing import List, Tuple, Optional
import hashlib

from .planset_generator import Plan, PlanSet


def compute_leaf_hash(plan: Plan) -> str:
    """Compute hash of a single plan (leaf in Merkle tree)."""
    return plan.plan_hash


def compute_internal_hash(left: str, right: str) -> str:
    """Compute hash of internal node from children."""
    combined = left.encode() + right.encode()
    return hashlib.sha256(combined).hexdigest()


def build_merkle_tree(leaf_hashes: List[str]) -> Tuple[List[str], List[List[str]]]:
    """
    Build a Merkle tree from leaf hashes.
    
    Args:
        leaf_hashes: List of leaf hashes (plan hashes)
    
    Returns:
        (root, proof_layers) where:
        - root: Merkle root hash
        - proof_layers: All layers of the tree (for verification)
    """
    if not leaf_hashes:
        raise ValueError("Cannot build Merkle tree from empty leaf list")
    
    if len(leaf_hashes) == 1:
        # Single leaf - root is the leaf itself
        return leaf_hashes[0], [leaf_hashes]
    
    # Build tree bottom-up
    current_level = leaf_hashes
    all_levels = [current_level]
    
    while len(current_level) > 1:
        next_level: List[str] = []
        
        # Process pairs
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            if i + 1 < len(current_level):
                right = current_level[i + 1]
            else:
                # Odd number - duplicate last element
                right = left
            
            parent_hash = compute_internal_hash(left, right)
            next_level.append(parent_hash)
        
        current_level = next_level
        all_levels.append(current_level)
    
    # Root is the last level's only element
    root = current_level[0]
    return root, all_levels


def build_plan_merkle_root(planset: PlanSet) -> str:
    """
    Build Merkle root for a PlanSet.
    
    Args:
        planset: The PlanSet to build Merkle root for
    
    Returns:
        Merkle root hash
    """
    leaf_hashes = [compute_leaf_hash(plan) for plan in planset.plans]
    root, _ = build_merkle_tree(leaf_hashes)
    return root


def get_merkle_proof(
    planset: PlanSet,
    plan_index: int,
) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Get Merkle proof for a specific plan.
    
    Args:
        planset: The PlanSet
        plan_index: Index of the plan to prove membership for
    
    Returns:
        (leaf_hash, proof) where:
        - leaf_hash: The hash of the plan
        - proof: List of (sibling_hash, position) pairs
            - position is "left" or "right"
    """
    if plan_index < 0 or plan_index >= len(planset.plans):
        raise ValueError(f"Plan index {plan_index} out of range")
    
    # Build tree
    leaf_hashes = [compute_leaf_hash(plan) for plan in planset.plans]
    root, all_levels = build_merkle_tree(leaf_hashes)
    
    # Get leaf hash
    leaf_hash = leaf_hashes[plan_index]
    
    # Build proof
    proof: List[Tuple[str, str]] = []
    idx = plan_index
    
    for level_idx in range(len(all_levels) - 1):
        current_level = all_levels[level_idx]
        
        # Find sibling
        if idx % 2 == 0:
            # Left child - sibling is right
            if idx + 1 < len(current_level):
                sibling = current_level[idx + 1]
                position = "right"
            else:
                # No sibling (odd number), use self
                sibling = current_level[idx]
                position = "right"
        else:
            # Right child - sibling is left
            sibling = current_level[idx - 1]
            position = "left"
        
        proof.append((sibling, position))
        idx = idx // 2
    
    return leaf_hash, proof


def verify_merkle_proof(
    leaf_hash: str,
    proof: List[Tuple[str, str]],
    expected_root: str,
) -> bool:
    """
    Verify a Merkle proof.
    
    Args:
        leaf_hash: The hash of the leaf
        proof: The proof (sibling hashes and positions)
        expected_root: Expected Merkle root
    
    Returns:
        True if proof is valid
    """
    current_hash = leaf_hash
    
    for sibling, position in proof:
        if position == "left":
            current_hash = compute_internal_hash(sibling, current_hash)
        else:
            current_hash = compute_internal_hash(current_hash, sibling)
    
    return current_hash == expected_root


def verify_plan_membership(
    planset: PlanSet,
    plan_index: int,
    expected_root: Optional[str] = None,
) -> bool:
    """
    Verify a plan is a member of the PlanSet.
    
    Args:
        planset: The PlanSet
        plan_index: Index of the plan
        expected_root: Optional expected root (if None, computed from planset)
    
    Returns:
        True if plan is member
    """
    # Compute root if not provided
    if expected_root is None:
        expected_root = build_plan_merkle_root(planset)
    
    # Get proof
    leaf_hash, proof = get_merkle_proof(planset, plan_index)
    
    # Verify
    return verify_merkle_proof(leaf_hash, proof, expected_root)


# =============================================================================
# Utility Functions
# =============================================================================

def get_planset_root(planset: PlanSet) -> str:
    """
    Get the Merkle root for a PlanSet.
    
    This is the main entry point for getting a planset commitment.
    """
    return build_plan_merkle_root(planset)


def verify_plan_in_planset(
    plan: Plan,
    planset: PlanSet,
) -> bool:
    """
    Verify a specific plan is in a PlanSet.
    
    Args:
        plan: The plan to verify
        planset: The PlanSet
    
    Returns:
        True if plan is in the planset
    """
    # Check by hash
    for p in planset.plans:
        if p.plan_hash == plan.plan_hash:
            return True
    return False
