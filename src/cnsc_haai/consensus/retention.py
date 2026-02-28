"""
Retention Policy Module

Provides retention policy ID hashing and window derivation for ATS slabs.
Per docs/ats/20_coh_kernel/retention_policy.md

Policy ID is computed by hashing the full document using JCS (RFC8785).
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from cnsc_haai.consensus.jcs import jcs_canonical_bytes
from cnsc_haai.consensus.hash import sha256, sha256_prefixed


@dataclass
class RetentionPolicy:
    """
    Retention policy for slab data.

    Fields:
        version: Policy version (e.g., "1.0.0")
        policy_id: Unique policy identifier (computed from content)
        retention_period_blocks: How long to retain after window_end
        dispute_window_blocks: Challenge window length
        deletion_authorization: Conditions for authorized deletion
    """

    version: str
    policy_id: str
    retention_period_blocks: int
    dispute_window_blocks: int
    deletion_authorization: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetentionPolicy":
        """
        Create a RetentionPolicy from a dictionary.

        Computes policy_id from the full document using JCS.
        """
        # Make a copy to avoid mutating original
        policy_data = dict(data)

        # Compute policy_id (single hash, no double-hash)
        policy_bytes = jcs_canonical_bytes(policy_data)
        computed_policy_id = sha256_prefixed(policy_bytes)

        return cls(
            version=policy_data.get("version", "1.0.0"),
            policy_id=computed_policy_id,
            retention_period_blocks=policy_data.get("retention_period_blocks", 0),
            dispute_window_blocks=policy_data.get("dispute_window_blocks", 0),
            deletion_authorization=policy_data.get("deletion_authorization", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "policy_id": self.policy_id,
            "retention_period_blocks": self.retention_period_blocks,
            "dispute_window_blocks": self.dispute_window_blocks,
            "deletion_authorization": self.deletion_authorization,
        }


# Policy ID computation constants
DOMAIN_BYTES = b"COH_RETENTION_V1\n"


def compute_policy_id(policy_json: Dict[str, Any]) -> str:
    """
    Compute retention policy ID by hashing the full document (JCS).

    Per spec: policy_id = sha256(JCS(policy_json))

    Args:
        policy_json: The full retention policy document

    Returns:
        Policy ID with sha256: prefix
    """
    # Serialize using JCS (RFC8785)
    jcs_bytes = jcs_canonical_bytes(policy_json)

    # Hash the canonical bytes
    policy_hash = sha256(jcs_bytes)

    # Return with prefix
    return sha256_prefixed(policy_hash)


def compute_window_end_height(slab_accept_height: int, challenge_window_len_blocks: int) -> int:
    """
    Compute the window end height for a slab.

    The window_end is the height at which the challenge window closes.
    After this height, no more fraud proofs can be submitted.

    Args:
        slab_accept_height: The height at which the slab was accepted
        challenge_window_len_blocks: Length of the challenge window

    Returns:
        window_end height
    """
    return slab_accept_height + challenge_window_len_blocks


def compute_finalize_height(window_end_height: int, retention_period_blocks: int) -> int:
    """
    Compute the height at which a slab becomes finalized (deletable).

    A slab can be deleted after:
    1. The challenge window has closed (window_end)
    2. The retention period has elapsed

    Args:
        window_end_height: The height at which the challenge window closes
        retention_period_blocks: How long to retain after window_end

    Returns:
        Height at which the slab becomes finalized/deletable
    """
    return window_end_height + retention_period_blocks


def is_finalized(current_height: int, window_end_height: int, retention_period_blocks: int) -> bool:
    """
    Check if a slab is finalized and eligible for deletion.

    Args:
        current_height: Current block height
        window_end_height: Height when challenge window closes
        retention_period_blocks: Retention period after window_end

    Returns:
        True if the slab is finalized
    """
    finalize_height = compute_finalize_height(window_end_height, retention_period_blocks)
    return current_height >= finalize_height


def validate_policy(policy: RetentionPolicy) -> tuple[bool, Optional[str]]:
    """
    Validate a retention policy.

    Args:
        policy: The policy to validate

    Returns:
        (is_valid, error_message)
    """
    # Check required fields
    if not policy.version:
        return False, "Missing version"

    if policy.retention_period_blocks < 0:
        return False, "retention_period_blocks must be non-negative"

    if policy.dispute_window_blocks < 0:
        return False, "dispute_window_blocks must be non-negative"

    # Check deletion authorization
    auth = policy.deletion_authorization
    required_auth_fields = ["min_budget", "no_disputes", "window_end_verified"]
    for field in required_auth_fields:
        if field not in auth:
            return False, f"Missing deletion_authorization.{field}"

    return True, None


# Policy storage (in production, this would be a database)
_policy_store: Dict[str, RetentionPolicy] = {}


def register_policy(policy: RetentionPolicy) -> None:
    """
    Register a retention policy.

    Args:
        policy: The policy to register
    """
    _policy_store[policy.policy_id] = policy


def get_policy(policy_id: str) -> Optional[RetentionPolicy]:
    """
    Retrieve a retention policy by ID.

    Args:
        policy_id: The policy ID

    Returns:
        The policy if found, None otherwise
    """
    return _policy_store.get(policy_id)


def load_policy_from_json(policy_json: Dict[str, Any]) -> RetentionPolicy:
    """
    Load and register a policy from JSON dict.

    Args:
        policy_json: Policy as dictionary

    Returns:
        The loaded policy
    """
    policy = RetentionPolicy.from_dict(policy_json)
    register_policy(policy)
    return policy
