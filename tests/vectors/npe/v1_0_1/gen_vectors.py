#!/usr/bin/env python3
"""
Generate golden test vectors TV1 and TV2 for NPE v1.0.1.

This script generates deterministic test vectors with all derived hashes.
"""

import struct
import base64
import json
import hashlib
import sys

# Add src to path for imports
sys.path.insert(0, '/home/user/cnsc-haai/src')

from npe.spec_constants import PRNG_SEED_PREFIX, PRNG_NONCE_PREFIX


def create_delta_z(deltas: list) -> bytes:
    """Create a DELTA_Z envelope: uint32_be(d) || int64_be[d]"""
    data = struct.pack('>I', len(deltas))  # uint32_be(d)
    for delta in deltas:
        data += struct.pack('>q', delta)  # int64_be
    return data


def create_tv1() -> dict:
    """Create Test Vector 1 (RENORM_QUOTIENT with simple deltas)"""
    
    # Delta: 2 values (1, 2)
    delta_bytes = create_delta_z([1, 2])
    delta_b64 = base64.b64encode(delta_bytes).decode('ascii')
    delta_hash = hashlib.sha256(delta_bytes).hexdigest()
    
    # Cert: empty (SHA256 of empty bytes = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855)
    cert_bytes = b''
    cert_b64 = base64.b64encode(cert_bytes).decode('ascii')
    cert_hash = hashlib.sha256(cert_bytes).hexdigest()
    
    # Proposal envelope (before hashing)
    proposal = {
        "cert_hash": cert_hash,
        "certs_b64": cert_b64,
        "delta_bytes_b64": delta_b64,
        "delta_hash": delta_hash,
        "domain_separator": "NPE|1.0.1",
        "npe_state_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "parent_slab_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "proposal_id": "0000000000000001",
        "proposal_type": "RENORM_QUOTIENT",
        "timestamp_unix_sec": 1708516800,
        "version": "1.0.1",
        "budget_post": {
            "max_cost": 4294967296,
            "max_debits": 2147483648,
            "max_refunds": 1073741824,
            "max_steps": 8589934592
        }
    }
    
    # JCS canonicalization
    jcs_bytes = json.dumps(proposal, separators=(',', ':'), sort_keys=True, ensure_ascii=True).encode('utf-8')
    proposal_hash = hashlib.sha256(jcs_bytes).hexdigest()
    
    # PRNG seed/nonce
    parent_slab_hash_bytes = bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    npe_state_hash_bytes = bytes.fromhex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    proposal_id_bytes = struct.pack('>Q', 1)  # uint64_be(1)
    
    seed_preimage = PRNG_SEED_PREFIX + parent_slab_hash_bytes + npe_state_hash_bytes + proposal_id_bytes
    seed = hashlib.sha256(seed_preimage).hexdigest()
    
    nonce_preimage = PRNG_NONCE_PREFIX + seed_preimage
    nonce_hex = hashlib.sha256(nonce_preimage).hexdigest()[:32]  # First 16 bytes in hex
    
    expected = {
        "proposal_hash": proposal_hash,
        "delta_hash": delta_hash,
        "cert_hash": cert_hash,
        "seed_hash": seed,
        "nonce_hex": nonce_hex,
        "jcs_bytes_len": len(jcs_bytes),
        "delta_bytes_len": len(delta_bytes),
        "budget_post": proposal["budget_post"]
    }
    
    return {
        "proposal": proposal,
        "expected": expected,
        "delta_bin_hex": delta_bytes.hex(),
        "cert_bin_hex": cert_bytes.hex()
    }


def create_tv2() -> dict:
    """Create Test Vector 2 (CONTINUOUS_FLOW with different deltas)"""
    
    # Delta: 3 values (10, 20, 30)
    delta_bytes = create_delta_z([10, 20, 30])
    delta_b64 = base64.b64encode(delta_bytes).decode('ascii')
    delta_hash = hashlib.sha256(delta_bytes).hexdigest()
    
    # Cert: empty
    cert_bytes = b''
    cert_b64 = base64.b64encode(cert_bytes).decode('ascii')
    cert_hash = hashlib.sha256(cert_bytes).hexdigest()
    
    # Proposal envelope
    proposal = {
        "cert_hash": cert_hash,
        "certs_b64": cert_b64,
        "delta_bytes_b64": delta_b64,
        "delta_hash": delta_hash,
        "domain_separator": "NPE|1.0.1",
        "npe_state_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "parent_slab_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "proposal_id": "0000000000000002",
        "proposal_type": "CONTINUOUS_FLOW",
        "timestamp_unix_sec": 1708516900,
        "version": "1.0.1",
        "budget_post": {
            "max_cost": 8589934592,
            "max_debits": 4294967296,
            "max_refunds": 2147483648,
            "max_steps": 17179869184
        }
    }
    
    # JCS canonicalization
    jcs_bytes = json.dumps(proposal, separators=(',', ':'), sort_keys=True, ensure_ascii=True).encode('utf-8')
    proposal_hash = hashlib.sha256(jcs_bytes).hexdigest()
    
    # PRNG seed/nonce
    parent_slab_hash_bytes = bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    npe_state_hash_bytes = bytes.fromhex("cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")
    proposal_id_bytes = struct.pack('>Q', 2)  # uint64_be(2)
    
    seed_preimage = PRNG_SEED_PREFIX + parent_slab_hash_bytes + npe_state_hash_bytes + proposal_id_bytes
    seed = hashlib.sha256(seed_preimage).hexdigest()
    
    nonce_preimage = PRNG_NONCE_PREFIX + seed_preimage
    nonce_hex = hashlib.sha256(nonce_preimage).hexdigest()[:32]  # First 16 bytes in hex
    
    expected = {
        "proposal_hash": proposal_hash,
        "delta_hash": delta_hash,
        "cert_hash": cert_hash,
        "seed_hash": seed,
        "nonce_hex": nonce_hex,
        "jcs_bytes_len": len(jcs_bytes),
        "delta_bytes_len": len(delta_bytes),
        "budget_post": proposal["budget_post"]
    }
    
    return {
        "proposal": proposal,
        "expected": expected,
        "delta_bin_hex": delta_bytes.hex(),
        "cert_bin_hex": cert_bytes.hex()
    }


if __name__ == "__main__":
    tv1 = create_tv1()
    tv2 = create_tv2()
    
    # Write TV1
    with open('/home/user/cnsc-haai/tests/vectors/npe/v1_0_1/TV1.proposal.json', 'w') as f:
        json.dump(tv1['proposal'], f, indent=2)
    
    with open('/home/user/cnsc-haai/tests/vectors/npe/v1_0_1/TV1.expected.json', 'w') as f:
        json.dump(tv1['expected'], f, indent=2)
    
    with open('/home/user/cnsc-haai/tests/vectors/npe/v1_0_1/TV1.delta.bin', 'wb') as f:
        f.write(bytes.fromhex(tv1['delta_bin_hex']))
    
    # Write TV2
    with open('/home/user/cnsc-haai/tests/vectors/npe/v1_0_1/TV2.proposal.json', 'w') as f:
        json.dump(tv2['proposal'], f, indent=2)
    
    with open('/home/user/cnsc-haai/tests/vectors/npe/v1_0_1/TV2.expected.json', 'w') as f:
        json.dump(tv2['expected'], f, indent=2)
    
    with open('/home/user/cnsc-haai/tests/vectors/npe/v1_0_1/TV2.delta.bin', 'wb') as f:
        f.write(bytes.fromhex(tv2['delta_bin_hex']))
    
    print("✓ TV1.proposal.json")
    print("✓ TV1.expected.json")
    print("✓ TV1.delta.bin")
    print("✓ TV2.proposal.json")
    print("✓ TV2.expected.json")
    print("✓ TV2.delta.bin")
    print()
    print("TV1 Hashes:")
    print(f"  proposal_hash: {tv1['expected']['proposal_hash']}")
    print(f"  delta_hash: {tv1['expected']['delta_hash']}")
    print(f"  cert_hash: {tv1['expected']['cert_hash']}")
    print(f"  seed_hash: {tv1['expected']['seed_hash']}")
    print()
    print("TV2 Hashes:")
    print(f"  proposal_hash: {tv2['expected']['proposal_hash']}")
    print(f"  delta_hash: {tv2['expected']['delta_hash']}")
    print(f"  cert_hash: {tv2['expected']['cert_hash']}")
    print(f"  seed_hash: {tv2['expected']['seed_hash']}")
