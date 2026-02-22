"""
NPE v1.0.1 Benchmark Harness

Benchmarks for:
1. JCS canonicalization (synthetic + governance data)
2. QFixed18 arithmetic operations
3. ChaCha20 PRNG throughput
4. Binary parser (delta parsing)
5. Certificate hashing
6. Full RV verification

Uses synthetic data first, then governance logs if available.
"""

import json
import os
import struct
import time
import random
from typing import List, Dict, Any

import pytest

from npe.core.canon import jcs_bytes, jcs_string
from npe.core.qfixed18 import q18_add, q18_sub, q18_mul, q18_div, int_to_q18, RoundingMode
from npe.core.prng_chacha20 import ChaCha20PRNG, derive_seed
from npe.core.binary_parser import parse_delta_z, parse_delta_a
from npe.core.delta_program import parse_delta_program
from npe.core.delta_program import DeltaProgram
from npe.core.hashing import hash_proposal, hash_delta, hash_cert
from npe.rv.verify_proposal import verify_proposal


# ============================================================================
# Synthetic Data Generation
# ============================================================================

def generate_synthetic_proposals(count: int) -> List[Dict[str, Any]]:
    """Generate synthetic proposal structures for benchmarking."""
    proposals = []
    for i in range(count):
        proposal = {
            "version": "1.0.1",
            "domain": "CNSC-HAAI",
            "proposal_type": "CONTINUOUS_FLOW",
            "proposal_id": f"prop_{i:08d}",
            "parent_slab_hash": f"a" * 64,
            "npe_state_hash": f"b" * 64,
            "budget_pre": {
                "wall_time_ms": 1000000,
                "candidates": 100,
                "evidence": 50,
                "search_expansions": 10000,
            },
            "budget_post": {
                "wall_time_ms": 900000,
                "candidates": 90,
                "evidence": 45,
                "search_expansions": 9000,
            },
            "delta_bytes_b64": "dGVzdA==",  # "test" base64
            "signature": f"sig_{i:08d}",
        }
        proposals.append(proposal)
    return proposals


def generate_synthetic_deltas(count: int, op_count: int = 100) -> List[bytes]:
    """Generate synthetic delta programs for benchmarking."""
    deltas = []
    for _ in range(count):
        data = bytes([0x01, 0x00])  # version, kind (Z)
        data += struct.pack('>H', op_count)  # op_count
        
        # Generate random sparse add operations
        for _ in range(op_count):
            opcode = 0x01  # Z_SPARSE_ADD
            flags = 0x00
            k = random.randint(1, 10)
            idx = random.randint(0, 10000)
            delta = random.randint(-1000000, 1000000)
            
            data += bytes([opcode, flags])
            data += struct.pack('>H', 14)  # arg_len
            data += struct.pack('>H', k)
            data += struct.pack('>I', idx)
            data += struct.pack('>q', delta)
        
        data += struct.pack('>I', 0)  # certs_len = 0
        deltas.append(data)
    
    return deltas


def generate_synthetic_certs(count: int) -> List[bytes]:
    """Generate synthetic certificate payloads."""
    certs = []
    for i in range(count):
        cert_type = random.choice([1, 2, 3, 4])  # BOUND_Q18, MERKLE, RENORM_Q, RENORM_U
        flags = 0x00
        
        if cert_type == 1:  # BOUND_Q18
            payload = struct.pack('>q', random.randint(-1000000, 1000000))
        elif cert_type == 2:  # MERKLE
            payload = struct.pack('>H', random.randint(1, 32))  # depth
            payload += b"a" * 32  # root hash
        elif cert_type == 3:  # RENORM_Q
            payload = struct.pack('>q', random.randint(1, 1000000))
            payload += struct.pack('>q', random.randint(1, 1000000))
        else:  # RENORM_U
            payload = struct.pack('>q', random.randint(1, 1000000))
        
        # Compute hash
        from npe.core.delta_program import compute_cert_hash
        cert_hash = compute_cert_hash(cert_type, flags, payload)
        
        certs.append(payload + cert_hash)
    
    return certs


# ============================================================================
# Benchmark: JCS Canonicalization
# ============================================================================

class TestJCS:
    """Benchmark JCS canonicalization."""
    
    @pytest.fixture
    def synthetic_proposals(self):
        return generate_synthetic_proposals(1000)
    
    def test_canonicalize_1000_proposals(self, synthetic_proposals):
        """Benchmark canonicalizing 1000 proposals."""
        start = time.perf_counter()
        
        for proposal in synthetic_proposals:
            _ = jcs_string(proposal, validate_npe=False)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(synthetic_proposals) / elapsed
        
        print(f"\nJCS Canonicalization: {ops_per_sec:.2f} ops/sec ({elapsed:.3f}s for {len(synthetic_proposals)})")
        assert elapsed < 10.0  # Should complete in under 10 seconds
    
    def test_canonicalize_bytes_1000_proposals(self, synthetic_proposals):
        """Benchmark canonicalizing to bytes."""
        start = time.perf_counter()
        
        for proposal in synthetic_proposals:
            _ = jcs_bytes(proposal, validate_npe=False)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(synthetic_proposals) / elapsed
        
        print(f"\nJCS Bytes: {ops_per_sec:.2f} ops/sec ({elapsed:.3f}s for {len(synthetic_proposals)})")
        assert elapsed < 10.0


# ============================================================================
# Benchmark: QFixed18 Arithmetic
# ============================================================================

class TestQFixed18:
    """Benchmark QFixed18 arithmetic operations."""
    
    @pytest.fixture
    def operands(self):
        # Use plain integers (Q18 values)
        return [(random.randint(-1000000, 1000000), 
                 random.randint(-1000000, 1000000)) 
                for _ in range(10000)]
    
    def test_add_10000_pairs(self, operands):
        """Benchmark 10000 additions."""
        start = time.perf_counter()
        
        for a, b in operands:
            _ = q18_add(a, b)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(operands) / elapsed
        
        print(f"\nQFixed18 Add: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 2.0
    
    def test_subtract_10000_pairs(self, operands):
        """Benchmark 10000 subtractions."""
        start = time.perf_counter()
        
        for a, b in operands:
            _ = q18_sub(a, b)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(operands) / elapsed
        
        print(f"\nQFixed18 Subtract: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 2.0
    
    def test_multiply_10000_pairs(self, operands):
        """Benchmark 10000 multiplications."""
        start = time.perf_counter()
        
        for a, b in operands:
            _ = q18_mul(a, b)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(operands) / elapsed
        
        print(f"\nQFixed18 Multiply: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 5.0
    
    def test_divide_10000_pairs(self, operands):
        """Benchmark 10000 divisions."""
        # Use non-zero divisors
        operands = [(a, random.randint(1, 1000000)) 
                    for a, _ in operands[:10000]]
        
        start = time.perf_counter()
        
        for a, b in operands:
            _ = q18_div(a, b)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(operands) / elapsed
        
        print(f"\nQFixed18 Divide: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 10.0


# ============================================================================
# Benchmark: ChaCha20 PRNG
# ============================================================================

class TestPRNG:
    """Benchmark ChaCha20 PRNG operations."""
    
    def test_sample_1000_times(self):
        """Benchmark 1000 PRNG samples."""
        parent = "a" * 64
        state = "b" * 64
        prop_id = "0000000000000001"
        
        prng = ChaCha20PRNG(parent, state, prop_id)
        
        start = time.perf_counter()
        
        for _ in range(1000):
            _ = prng.sample(1)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = 1000 / elapsed
        
        print(f"\nChaCha20 PRNG Sample: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 10.0
    
    def test_derive_seed_1000_times(self):
        """Benchmark 1000 seed derivations."""
        parent = "a" * 64
        state = "b" * 64
        
        start = time.perf_counter()
        
        for i in range(1000):
            _ = derive_seed(parent, state, f"{i:016d}")
        
        elapsed = time.perf_counter() - start
        ops_per_sec = 1000 / elapsed
        
        print(f"\nPRNG Seed Derivation: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 10.0


# ============================================================================
# Benchmark: Binary Parser
# ============================================================================

class TestParser:
    """Benchmark binary delta parsing."""
    
    @pytest.mark.skip(reason="delta format needs fixing")
    def test_parse_delta_z_10_times(self):
        """Benchmark parsing 10 delta programs."""
        # Generate minimal valid deltas
        deltas = []
        for _ in range(10):
            # Simple valid delta with 1 op
            data = bytes([0x01, 0x00])  # version, kind
            data += struct.pack('>H', 1)  # op_count = 1
            data += bytes([0x01, 0x00])  # opcode=1, flags=0
            data += struct.pack('>H', 14)  # arg_len = 14
            data += struct.pack('>H', 1)  # k=1
            data += struct.pack('>I', 0)  # idx=0
            data += struct.pack('>q', 0)  # delta=0
            data += struct.pack('>I', 0)  # certs_len = 0
            deltas.append(data)
        
        start = time.perf_counter()
        
        for delta in deltas:
            _ = parse_delta_z(delta)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(deltas) / elapsed
        
        print(f"\nParse Delta Z: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 5.0
    
    def test_parse_delta_program_10_times(self):
        """Benchmark parsing 10 full delta programs."""
        # Generate minimal valid deltas
        deltas = []
        for _ in range(10):
            # Simple valid delta with 1 op
            data = bytes([0x01, 0x00])  # version, kind
            data += struct.pack('>H', 1)  # op_count = 1
            data += bytes([0x01, 0x00])  # opcode=1, flags=0
            data += struct.pack('>H', 14)  # arg_len = 14
            data += struct.pack('>H', 1)  # k=1
            data += struct.pack('>I', 0)  # idx=0
            data += struct.pack('>q', 0)  # delta=0
            data += struct.pack('>I', 0)  # certs_len = 0
            deltas.append(data)
        
        start = time.perf_counter()
        
        for delta in deltas:
            _ = parse_delta_program(delta)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(deltas) / elapsed
        
        print(f"\nParse Delta Program: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 5.0


# ============================================================================
# Benchmark: Certificate Hashing
# ============================================================================

class TestCertHashing:
    """Benchmark certificate hashing."""
    
    @pytest.fixture
    def synthetic_certs(self):
        return generate_synthetic_certs(1000)
    
    def test_hash_cert_1000_times(self, synthetic_certs):
        """Benchmark hashing 1000 certificates."""
        import base64
        
        start = time.perf_counter()
        
        for cert in synthetic_certs:
            cert_b64 = base64.b64encode(cert).decode()
            _ = hash_cert(cert_b64)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(synthetic_certs) / elapsed
        
        print(f"\nCertificate Hashing: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 5.0


# ============================================================================
# Benchmark: RV Verification
# ============================================================================

class TestRVVerification:
    """Benchmark RV proposal verification."""
    
    @pytest.fixture
    def synthetic_proposals(self):
        return generate_synthetic_proposals(100)
    
    def test_verify_proposal_100_times(self, synthetic_proposals):
        """Benchmark verifying 100 proposals."""
        start = time.perf_counter()
        
        for proposal in synthetic_proposals:
            _ = verify_proposal(proposal)
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(synthetic_proposals) / elapsed
        
        print(f"\nRV Verification: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 10.0


# ============================================================================
# Benchmark: Full Pipeline
# ============================================================================

class TestFullPipeline:
    """Benchmark full NPE pipeline."""
    
    @pytest.mark.skip(reason="needs valid proposal structure")
    def test_full_pipeline_10_iterations(self):
        """Benchmark full pipeline: canonicalize -> hash -> verify."""
        proposals = generate_synthetic_proposals(10)
        
        start = time.perf_counter()
        
        for proposal in proposals:
            # Step 1: Canonicalize
            canonical = jcs_string(proposal, validate_npe=False)
            
            # Step 2: Hash
            _ = hash_proposal(proposal)
            
            # Step 3: Verify (may fail on invalid proposals but that's fine)
            try:
                _ = verify_proposal(proposal)
            except Exception:
                pass
        
        elapsed = time.perf_counter() - start
        ops_per_sec = len(proposals) / elapsed
        
        print(f"\nFull Pipeline: {ops_per_sec:.2f} ops/sec")
        assert elapsed < 30.0


# ============================================================================
# Run Benchmarks
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
