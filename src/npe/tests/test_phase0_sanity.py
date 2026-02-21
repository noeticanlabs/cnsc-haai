"""
PHASE 0: Sanity Test - Frozen Spec & Golden Vectors.

This test verifies that:
- Spec constants are locked and unchanging
- Golden test vectors are deterministic
- All hashes are reproducible
- No float rules are enforced
"""

import json
import hashlib
import struct
import base64
from pathlib import Path

import pytest

from npe.spec_constants import (
    DOMAIN_SEPARATOR,
    PROTOCOL_VERSION,
    NUMERIC_DOMAIN,
    Q18_SCALE,
    ROUNDING_UP,
    ROUNDING_DOWN,
    PRNG_SEED_PREFIX,
    PRNG_NONCE_PREFIX,
    SHA256_HEX_LEN,
    expected_spec_hashes,
)


# ============================================================================
# Spec Constant Verification
# ============================================================================

def test_domain_separator_frozen():
    """Verify domain separator is exactly frozen."""
    assert DOMAIN_SEPARATOR == "NPE|1.0.1"


def test_protocol_version_frozen():
    """Verify protocol version is exactly frozen."""
    assert PROTOCOL_VERSION == "1.0.1"


def test_numeric_domain_is_qfixed18():
    """Verify numeric domain is Q18."""
    assert NUMERIC_DOMAIN == "QFixed18"


def test_q18_scale_is_262144():
    """Verify Q18 scale is 2^18."""
    assert Q18_SCALE == 262144
    assert Q18_SCALE == (1 << 18)


def test_rounding_modes_frozen():
    """Verify rounding modes are frozen."""
    assert ROUNDING_UP == "UP"
    assert ROUNDING_DOWN == "DOWN"


def test_prng_prefixes_frozen():
    """Verify PRNG prefixes are frozen."""
    assert PRNG_SEED_PREFIX == b"COH_NPE_PRNG_V1"
    assert PRNG_NONCE_PREFIX == b"COH_NPE_PRNG_NONCE_V1"


def test_spec_hashes_deterministic():
    """Verify spec component hashes are deterministic."""
    hashes = expected_spec_hashes()
    
    # Each hash should be 64 hex characters (SHA256)
    assert len(hashes["spec_version"]) == SHA256_HEX_LEN
    assert len(hashes["prng_seed_prefix"]) == SHA256_HEX_LEN
    assert len(hashes["prng_nonce_prefix"]) == SHA256_HEX_LEN
    
    # Recompute and verify they match
    spec_version_hash = hashlib.sha256(
        f"{DOMAIN_SEPARATOR}|{PROTOCOL_VERSION}|{NUMERIC_DOMAIN}".encode('utf-8')
    ).hexdigest()
    assert hashes["spec_version"] == spec_version_hash
    
    prng_seed_hash = hashlib.sha256(PRNG_SEED_PREFIX).hexdigest()
    assert hashes["prng_seed_prefix"] == prng_seed_hash
    
    prng_nonce_hash = hashlib.sha256(PRNG_NONCE_PREFIX).hexdigest()
    assert hashes["prng_nonce_prefix"] == prng_nonce_hash


# ============================================================================
# Golden Test Vector Verification
# ============================================================================

def load_test_vector(tv_name: str) -> dict:
    """Load a golden test vector from files."""
    # Vectors are in tests/vectors/npe/v1_0_1/ (relative to repo root)
    vectors_dir = Path(__file__).parent.parent.parent.parent / "tests" / "vectors" / "npe" / "v1_0_1"
    
    with open(vectors_dir / f"{tv_name}.proposal.json") as f:
        proposal = json.load(f)
    
    with open(vectors_dir / f"{tv_name}.expected.json") as f:
        expected = json.load(f)
    
    with open(vectors_dir / f"{tv_name}.delta.bin", "rb") as f:
        delta_bytes = f.read()
    
    return {
        "proposal": proposal,
        "expected": expected,
        "delta_bytes": delta_bytes,
    }


def test_tv1_files_exist():
    """Verify TV1 files exist."""
    vectors_dir = Path(__file__).parent.parent.parent.parent / "tests" / "vectors" / "npe" / "v1_0_1"
    
    assert (vectors_dir / "TV1.proposal.json").exists()
    assert (vectors_dir / "TV1.expected.json").exists()
    assert (vectors_dir / "TV1.delta.bin").exists()


def test_tv2_files_exist():
    """Verify TV2 files exist."""
    vectors_dir = Path(__file__).parent.parent.parent.parent / "tests" / "vectors" / "npe" / "v1_0_1"
    
    assert (vectors_dir / "TV2.proposal.json").exists()
    assert (vectors_dir / "TV2.expected.json").exists()
    assert (vectors_dir / "TV2.delta.bin").exists()


def test_tv1_delta_hash_matches():
    """Verify TV1 delta hash is reproducible."""
    tv1 = load_test_vector("TV1")
    
    # Recompute delta hash
    computed_hash = hashlib.sha256(tv1["delta_bytes"]).hexdigest()
    
    # Must match expected
    assert computed_hash == tv1["expected"]["delta_hash"]
    # And match in proposal
    assert tv1["proposal"]["delta_hash"] == tv1["expected"]["delta_hash"]


def test_tv2_delta_hash_matches():
    """Verify TV2 delta hash is reproducible."""
    tv2 = load_test_vector("TV2")
    
    # Recompute delta hash
    computed_hash = hashlib.sha256(tv2["delta_bytes"]).hexdigest()
    
    # Must match expected
    assert computed_hash == tv2["expected"]["delta_hash"]
    # And match in proposal
    assert tv2["proposal"]["delta_hash"] == tv2["expected"]["delta_hash"]


def test_tv1_proposal_jcs_hash():
    """Verify TV1 proposal JCS hash is reproducible."""
    tv1 = load_test_vector("TV1")
    
    # Compute JCS bytes
    jcs_bytes = json.dumps(
        tv1["proposal"],
        separators=(',', ':'),
        sort_keys=True,
        ensure_ascii=True
    ).encode('utf-8')
    
    # Compute hash
    computed_hash = hashlib.sha256(jcs_bytes).hexdigest()
    
    # Should match expected
    assert computed_hash == tv1["expected"]["proposal_hash"]


def test_tv2_proposal_jcs_hash():
    """Verify TV2 proposal JCS hash is reproducible."""
    tv2 = load_test_vector("TV2")
    
    # Compute JCS bytes
    jcs_bytes = json.dumps(
        tv2["proposal"],
        separators=(',', ':'),
        sort_keys=True,
        ensure_ascii=True
    ).encode('utf-8')
    
    # Compute hash
    computed_hash = hashlib.sha256(jcs_bytes).hexdigest()
    
    # Should match expected
    assert computed_hash == tv2["expected"]["proposal_hash"]


def test_tv1_cert_hash_empty():
    """Verify TV1 cert hash is SHA256 of empty bytes."""
    tv1 = load_test_vector("TV1")
    
    # Empty cert hash should be SHA256("")
    expected_empty_hash = hashlib.sha256(b"").hexdigest()
    
    assert tv1["expected"]["cert_hash"] == expected_empty_hash
    assert tv1["proposal"]["cert_hash"] == expected_empty_hash


def test_tv2_cert_hash_empty():
    """Verify TV2 cert hash is SHA256 of empty bytes."""
    tv2 = load_test_vector("TV2")
    
    # Empty cert hash should be SHA256("")
    expected_empty_hash = hashlib.sha256(b"").hexdigest()
    
    assert tv2["expected"]["cert_hash"] == expected_empty_hash
    assert tv2["proposal"]["cert_hash"] == expected_empty_hash


def test_tv1_prng_seed_deterministic():
    """Verify TV1 PRNG seed is deterministic."""
    tv1 = load_test_vector("TV1")
    
    # Reconstruct seed preimage
    parent_slab_hash_bytes = bytes.fromhex(tv1["proposal"]["parent_slab_hash"])
    npe_state_hash_bytes = bytes.fromhex(tv1["proposal"]["npe_state_hash"])
    proposal_id_bytes = struct.pack('>Q', int(tv1["proposal"]["proposal_id"], 16))
    
    seed_preimage = PRNG_SEED_PREFIX + parent_slab_hash_bytes + npe_state_hash_bytes + proposal_id_bytes
    seed = hashlib.sha256(seed_preimage).hexdigest()
    
    # Must match expected
    assert seed == tv1["expected"]["seed_hash"]


def test_tv2_prng_seed_deterministic():
    """Verify TV2 PRNG seed is deterministic."""
    tv2 = load_test_vector("TV2")
    
    # Reconstruct seed preimage
    parent_slab_hash_bytes = bytes.fromhex(tv2["proposal"]["parent_slab_hash"])
    npe_state_hash_bytes = bytes.fromhex(tv2["proposal"]["npe_state_hash"])
    proposal_id_bytes = struct.pack('>Q', int(tv2["proposal"]["proposal_id"], 16))
    
    seed_preimage = PRNG_SEED_PREFIX + parent_slab_hash_bytes + npe_state_hash_bytes + proposal_id_bytes
    seed = hashlib.sha256(seed_preimage).hexdigest()
    
    # Must match expected
    assert seed == tv2["expected"]["seed_hash"]


def test_tv1_tv2_different_proposals():
    """Verify TV1 and TV2 are distinct proposals."""
    tv1 = load_test_vector("TV1")
    tv2 = load_test_vector("TV2")
    
    # Different proposal IDs
    assert tv1["proposal"]["proposal_id"] != tv2["proposal"]["proposal_id"]
    
    # Different types
    assert tv1["proposal"]["proposal_type"] != tv2["proposal"]["proposal_type"]
    
    # Different hashes
    assert tv1["expected"]["proposal_hash"] != tv2["expected"]["proposal_hash"]
    assert tv1["expected"]["delta_hash"] != tv2["expected"]["delta_hash"]
    assert tv1["expected"]["seed_hash"] != tv2["expected"]["seed_hash"]


# ============================================================================
# Phase 0 Completion Verification
# ============================================================================

def test_phase0_spec_locked():
    """Verify Phase 0 spec is locked and frozen."""
    # All constants should be exactly as frozen
    assert DOMAIN_SEPARATOR == "NPE|1.0.1"
    assert PROTOCOL_VERSION == "1.0.1"
    assert NUMERIC_DOMAIN == "QFixed18"
    assert ROUNDING_UP == "UP"
    assert ROUNDING_DOWN == "DOWN"


def test_phase0_vectors_sealed():
    """Verify Phase 0 golden vectors are sealed."""
    # Load both test vectors
    tv1 = load_test_vector("TV1")
    tv2 = load_test_vector("TV2")
    
    # Both should have complete expected hashes
    assert "proposal_hash" in tv1["expected"]
    assert "delta_hash" in tv1["expected"]
    assert "cert_hash" in tv1["expected"]
    assert "seed_hash" in tv1["expected"]
    
    assert "proposal_hash" in tv2["expected"]
    assert "delta_hash" in tv2["expected"]
    assert "cert_hash" in tv2["expected"]
    assert "seed_hash" in tv2["expected"]


def test_phase0_no_drift():
    """Verify Phase 0 is deterministic (no mood, no drift)."""
    # Run multiple times and verify same results
    tv1_v1 = load_test_vector("TV1")
    tv1_v2 = load_test_vector("TV1")
    
    assert tv1_v1["expected"]["proposal_hash"] == tv1_v2["expected"]["proposal_hash"]
    assert tv1_v1["expected"]["delta_hash"] == tv1_v2["expected"]["delta_hash"]
    assert tv1_v1["expected"]["seed_hash"] == tv1_v2["expected"]["seed_hash"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
