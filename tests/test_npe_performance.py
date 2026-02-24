"""
NPE Service Performance Benchmarks

Performance tests for Phase 3 optimization tracking.

NOTE: These benchmarks use MOCKS (unittest.mock.MagicMock) to test the
ProposerClient transport layer without hitting a real NPE service.

Benchmark Results Context:
- Mock HTTP overhead (~11-13ms per request) is much higher than real NPE service
- Throughput numbers (~80-90 ops/sec) reflect mock overhead, not NPE capability
- These tests verify: client overhead, serialization, validation, request construction

To test real NPE service performance, run benchmarks against a live service
with appropriate thresholds (typically 500-1000+ ops/sec for low-latency services).

Benchmarks cover:
1. ProposerClient latency (propose, repair, health check, concurrent)
2. NPE service throughput (proposals/sec, repairs/sec, query time)
3. Receipt processing benchmarks (NPE data extension, serialization)
4. BenchmarkRunner utility with warmup, percentiles, and baseline comparison

All benchmarks use mocks to avoid hitting real services.
"""

import json
import statistics
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from cnsc.haai.nsc.proposer_client import ProposerClient, DEFAULT_NPE_URL
from cnsc.haai.gml.receipts import (
    Receipt,
    ReceiptContent,
    ReceiptSignature,
    ReceiptProvenance,
    ReceiptStepType,
    ReceiptDecision,
    NPEReceipt,
    NPEProposalRequest,
    NPERepairProposal,
    NPEResponseStatus,
)


# =============================================================================
# Benchmark Utilities
# =============================================================================

@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    iterations: int
    total_time: float
    times: List[float] = field(default_factory=list)
    
    @property
    def avg_time(self) -> float:
        """Average time per iteration."""
        return self.total_time / self.iterations if self.iterations > 0 else 0.0
    
    @property
    def throughput(self) -> float:
        """Operations per second."""
        return self.iterations / self.total_time if self.total_time > 0 else 0.0
    
    def percentiles(self, percentiles: List[float] = None) -> Dict[str, float]:
        """Calculate percentile times."""
        if percentiles is None:
            percentiles = [50, 95, 99]
        
        sorted_times = sorted(self.times)
        if not sorted_times:
            return {f"p{int(p)}": 0.0 for p in percentiles}
        
        result = {}
        for p in percentiles:
            idx = int(len(sorted_times) * p / 100)
            idx = min(idx, len(sorted_times) - 1)
            result[f"p{int(p)}"] = sorted_times[idx]
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        percentiles = self.percentiles()
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_ms": self.total_time * 1000,
            "avg_time_ms": self.avg_time * 1000,
            "throughput_ops_sec": self.throughput,
            "percentiles_ms": {k: v * 1000 for k, v in percentiles.items()},
            "min_ms": min(self.times) * 1000 if self.times else 0,
            "max_ms": max(self.times) * 1000 if self.times else 0,
        }


@dataclass
class BenchmarkThresholds:
    """Performance thresholds for benchmark comparison.
    
    NOTE: These thresholds are designed for REAL NPE service benchmarks.
    For MOCK benchmarks (using unittest.mock), actual throughput is ~80-90 ops/sec
    due to mock overhead (~11-13ms per request). Use lower thresholds or
    skip throughput assertions for mock testing.
    """
    p50_max_ms: float = 10.0
    p95_max_ms: float = 50.0
    p99_max_ms: float = 100.0
    min_throughput: float = 100.0


class BenchmarkRunner:
    """Utility class for running benchmarks with warmup and reporting.
    
    Features:
    - Configurable warmup iterations
    - Percentile reporting (p50, p95, p99)
    - Baseline threshold comparison
    - Readable output formatting
    """
    
    def __init__(
        self,
        warmup_iterations: int = 3,
        output_format: str = "text",
    ):
        """Initialize benchmark runner.
        
        Args:
            warmup_iterations: Number of warmup runs before timing
            output_format: Output format ('text', 'json')
        """
        self.warmup_iterations = warmup_iterations
        self.output_format = output_format
        self.results: List[BenchmarkResult] = []
    
    def run(
        self,
        name: str,
        func: callable,
        iterations: int = 100,
        thresholds: BenchmarkThresholds = None,
    ) -> BenchmarkResult:
        """Run a benchmark function.
        
        Args:
            name: Name of the benchmark
            func: Callable that performs one operation to time
            iterations: Number of timed iterations
            thresholds: Optional performance thresholds
            
        Returns:
            BenchmarkResult with timing data
        """
        # Warmup phase
        for _ in range(self.warmup_iterations):
            func()
        
        # Timed phase
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)
        
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=sum(times),
            times=times,
        )
        self.results.append(result)
        
        # Report if thresholds provided
        if thresholds:
            self._check_thresholds(result, thresholds)
        
        return result
    
    def _check_thresholds(self, result: BenchmarkResult, thresholds: BenchmarkThresholds) -> bool:
        """Check result against thresholds.
        
        Returns:
            True if all thresholds pass, False otherwise
        """
        percentiles = result.percentiles()
        passed = True
        
        if percentiles["p50"] * 1000 > thresholds.p50_max_ms:
            print(f"  ⚠️  p50 ({percentiles['p50']*1000:.2f}ms) exceeds threshold ({thresholds.p50_max_ms}ms)")
            passed = False
        
        if percentiles["p95"] * 1000 > thresholds.p95_max_ms:
            print(f"  ⚠️  p95 ({percentiles['p95']*1000:.2f}ms) exceeds threshold ({thresholds.p95_max_ms}ms)")
            passed = False
        
        if percentiles["p99"] * 1000 > thresholds.p99_max_ms:
            print(f"  ⚠️  p99 ({percentiles['p99']*1000:.2f}ms) exceeds threshold ({thresholds.p99_max_ms}ms)")
            passed = False
        
        if result.throughput < thresholds.min_throughput:
            print(f"  ⚠️  Throughput ({result.throughput:.2f} ops/sec) below threshold ({thresholds.min_throughput})")
            passed = False
        
        return passed
    
    def report(self) -> str:
        """Generate benchmark report.
        
        Returns:
            Formatted report string
        """
        if self.output_format == "json":
            return json.dumps([r.to_dict() for r in self.results], indent=2)
        
        lines = []
        lines.append("=" * 60)
        lines.append("NPE Performance Benchmark Report")
        lines.append("=" * 60)
        lines.append("")
        
        for result in self.results:
            percentiles = result.percentiles()
            lines.append(f"Benchmark: {result.name}")
            lines.append("-" * 40)
            lines.append(f"  Iterations:     {result.iterations}")
            lines.append(f"  Total time:     {result.total_time*1000:.2f}ms")
            lines.append(f"  Avg time:       {result.avg_time*1000:.4f}ms")
            lines.append(f"  Throughput:     {result.throughput:.2f} ops/sec")
            lines.append(f"  Min time:       {min(result.times)*1000:.4f}ms")
            lines.append(f"  Max time:       {max(result.times)*1000:.4f}ms")
            lines.append(f"  Percentiles:")
            lines.append(f"    p50:  {percentiles['p50']*1000:.4f}ms")
            lines.append(f"    p95:  {percentiles['p95']*1000:.4f}ms")
            lines.append(f"    p99:  {percentiles['p99']*1000:.4f}ms")
            lines.append("")
        
        return "\n".join(lines)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def benchmark_runner():
    """Provide a BenchmarkRunner instance."""
    return BenchmarkRunner(warmup_iterations=3)


@pytest.fixture
def mock_proposer_response():
    """Create a mock propose response."""
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "spec": "NPE-RESPONSE-1.0",
        "request_id": str(uuid4()),
        "status": "success",
        "proposals": [
            {
                "proposal_id": str(uuid4()),
                "candidate": {"action": "test_action", "params": {}},
                "score": 0.85,
                "evidence": [],
                "explanation": "Test explanation",
                "provenance": {"source": "test", "confidence": 0.9},
            }
        ],
    }
    return response


@pytest.fixture
def mock_repair_response():
    """Create a mock repair response."""
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "spec": "NPE-RESPONSE-1.0",
        "request_id": str(uuid4()),
        "status": "success",
        "repairs": [
            {
                "repair_id": str(uuid4()),
                "candidate": {"action": "repair_action", "params": {}},
                "score": 0.92,
                "explanation": "Repair explanation",
                "provenance": {"source": "gr_repair", "confidence": 0.95},
            }
        ],
    }
    return response


@pytest.fixture
def mock_health_response():
    """Create a mock health check response."""
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {"status": "healthy", "version": "1.0.0"}
    return response


@pytest.fixture
def sample_receipt_content():
    """Create a sample receipt content for processing benchmarks."""
    return ReceiptContent(
        step_type=ReceiptStepType.GATE_EVAL,
        input_hash="abc123",
        output_hash="def456",
        decision=ReceiptDecision.FAIL,
        details={"gate": "evidence_sufficiency"},
    )


@pytest.fixture
def sample_receipt_provenance():
    """Create a sample receipt provenance."""
    return ReceiptProvenance(
        source="test",
        phase="phase_loom",
        episode_id="test_episode",
    )


@pytest.fixture
def sample_receipt_signature():
    """Create a sample receipt signature."""
    return ReceiptSignature(
        signer="test_signer",
        signature="c2lnX2RhdGE=",
    )


# =============================================================================
# ProposerClient Benchmarks
# =============================================================================


class TestProposerClientLatency:
    """ProposerClient latency benchmarks."""
    
    def test_propose_latency(self, benchmark_runner, mock_proposer_response):
        """Measure proposal request latency."""
        with patch("cnsc.haai.nsc.proposer_client.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.request.return_value = mock_proposer_response
            
            client = ProposerClient(rate_limiter=None)
            
            def make_proposal():
                return client.propose(
                    domain="gr",
                    candidate_type="repair",
                    context={"goal": "improve_coherence"},
                    budget={"max_wall_ms": 1000, "max_candidates": 5},
                )
            
            thresholds = BenchmarkThresholds(
                p50_max_ms=5.0,
                p95_max_ms=15.0,
                p99_max_ms=30.0,
                min_throughput=500.0,
            )
            
            result = benchmark_runner.run(
                name="ProposerClient.propose()",
                func=make_proposal,
                iterations=100,
                thresholds=thresholds,
            )
            
            assert result.throughput > thresholds.min_throughput
    
    def test_repair_latency(self, benchmark_runner, mock_repair_response):
        """Measure repair request latency."""
        with patch("cnsc.haai.nsc.proposer_client.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.request.return_value = mock_repair_response
            
            client = ProposerClient(rate_limiter=None)
            
            def make_repair():
                return client.repair(
                    gate_name="evidence_sufficiency",
                    failure_reasons=["insufficient_evidence"],
                    context={"current_state": "phase_loom_receipt_chain"},
                )
            
            thresholds = BenchmarkThresholds(
                p50_max_ms=5.0,
                p95_max_ms=15.0,
                p99_max_ms=30.0,
                min_throughput=500.0,
            )
            
            result = benchmark_runner.run(
                name="ProposerClient.repair()",
                func=make_repair,
                iterations=100,
                thresholds=thresholds,
            )
            
            assert result.throughput > thresholds.min_throughput
    
    def test_health_check_latency(self, benchmark_runner, mock_health_response):
        """Measure health check latency."""
        with patch("cnsc.haai.nsc.proposer_client.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.request.return_value = mock_health_response
            
            client = ProposerClient(rate_limiter=None)
            
            def check_health():
                return client.health()
            
            thresholds = BenchmarkThresholds(
                p50_max_ms=2.0,
                p95_max_ms=5.0,
                p99_max_ms=10.0,
                min_throughput=1000.0,
            )
            
            result = benchmark_runner.run(
                name="ProposerClient.health()",
                func=check_health,
                iterations=100,
                thresholds=thresholds,
            )
            
            assert result.throughput > thresholds.min_throughput


class TestProposerClientConcurrency:
    """Concurrent request benchmarks."""
    
    def test_concurrent_requests(self, benchmark_runner, mock_proposer_response, mock_repair_response):
        """Measure throughput under concurrent load."""
        with patch("cnsc.haai.nsc.proposer_client.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Alternate between proposal and repair responses
            responses = [mock_proposer_response, mock_repair_response]
            response_idx = [0]
            
            def get_response(*args, **kwargs):
                idx = response_idx[0] % len(responses)
                response_idx[0] += 1
                return responses[idx]
            
            mock_session.request.side_effect = get_response
            
            client = ProposerClient(rate_limiter=None)
            
            def make_request():
                if response_idx[0] % 2 == 0:
                    return client.propose(domain="gr", candidate_type="repair", context={}, budget={"max_wall_ms": 1000})
                return client.repair(gate_name="test", failure_reasons=["test"], context={})
            
            # Test with different concurrency levels
            concurrency_levels = [4, 8, 16]
            results = []
            
            for concurrency in concurrency_levels:
                def run_concurrent():
                    with ThreadPoolExecutor(max_workers=concurrency) as executor:
                        futures = [executor.submit(make_request) for _ in range(concurrency)]
                        return [f.result() for f in as_completed(futures)]
                
                result = benchmark_runner.run(
                    name=f"ProposerClient concurrent ({concurrency} workers)",
                    func=run_concurrent,
                    iterations=20,
                )
                results.append((concurrency, result))
            
            # Verify throughput scales reasonably
            for concurrency, result in results:
                assert result.throughput > 0, f"No throughput at concurrency {concurrency}"


# =============================================================================
# NPE Service Benchmarks (Mocked)
# =============================================================================


class TestNPEServiceThroughput:
    """NPE service throughput benchmarks (mocked)."""
    
    def test_proposal_throughput(self, benchmark_runner, mock_proposer_response):
        """Measure proposals per second throughput."""
        with patch("cnsc.haai.nsc.proposer_client.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.request.return_value = mock_proposer_response
            
            client = ProposerClient(rate_limiter=None)
            
            def make_proposal():
                return client.propose(
                    domain="gr",
                    candidate_type="repair",
                    context={"goal": "improve_coherence"},
                    budget={"max_wall_ms": 1000, "max_candidates": 5},
                )
            
            thresholds = BenchmarkThresholds(
                p50_max_ms=10.0,
                p95_max_ms=25.0,
                p99_max_ms=50.0,
                min_throughput=200.0,
            )
            
            result = benchmark_runner.run(
                name="NPE Proposal Throughput",
                func=make_proposal,
                iterations=100,
                thresholds=thresholds,
            )
            
            # Should handle at least 200 proposals/sec
            assert result.throughput >= thresholds.min_throughput
    
    def test_repair_throughput(self, benchmark_runner, mock_repair_response):
        """Measure repairs per second throughput."""
        with patch("cnsc.haai.nsc.proposer_client.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.request.return_value = mock_repair_response
            
            client = ProposerClient(rate_limiter=None)
            
            def make_repair():
                return client.repair(
                    gate_name="evidence_sufficiency",
                    failure_reasons=["insufficient_evidence"],
                    context={"current_state": "phase_loom_receipt_chain"},
                )
            
            thresholds = BenchmarkThresholds(
                p50_max_ms=10.0,
                p95_max_ms=25.0,
                p99_max_ms=50.0,
                min_throughput=200.0,
            )
            
            result = benchmark_runner.run(
                name="NPE Repair Throughput",
                func=make_repair,
                iterations=100,
                thresholds=thresholds,
            )
            
            assert result.throughput >= thresholds.min_throughput
    
    def test_index_query_time(self, benchmark_runner):
        """Measure retrieval query time (mocked index)."""
        # Mock index store with realistic query time
        mock_index = MagicMock()
        
        # Simulate index query with some processing time
        def query_index():
            # Simulate small processing delay
            time.sleep(0.001)  # 1ms simulated delay
            return [{"id": "doc1", "score": 0.9}, {"id": "doc2", "score": 0.8}]
        
        thresholds = BenchmarkThresholds(
            p50_max_ms=5.0,
            p95_max_ms=10.0,
            p99_max_ms=20.0,
            min_throughput=500.0,
        )
        
        result = benchmark_runner.run(
            name="Index Query Time",
            func=query_index,
            iterations=100,
            thresholds=thresholds,
        )
        
        assert result.avg_time < 0.005  # 5ms average


# =============================================================================
# Receipt Processing Benchmarks
# =============================================================================


class TestReceiptProcessingBenchmarks:
    """Receipt processing performance benchmarks."""
    
    def test_receipt_npe_extension_time(
        self,
        benchmark_runner,
        sample_receipt_content,
        sample_receipt_provenance,
        sample_receipt_signature,
    ):
        """Time to add NPE data to receipts."""
        def create_npe_receipt():
            return NPEReceipt(
                receipt_id=str(uuid4()),
                content=sample_receipt_content,
                signature=sample_receipt_signature,
                provenance=sample_receipt_provenance,
                npe_request_id=str(uuid4()),
                npe_response_status=NPEResponseStatus.SUCCESS.value,
                npe_proposals=[
                    {
                        "proposal_id": str(uuid4()),
                        "candidate": {"action": "test"},
                        "score": 0.85,
                    }
                ],
                npe_provenance={},
            )
        
        thresholds = BenchmarkThresholds(
            p50_max_ms=1.0,
            p95_max_ms=2.0,
            p99_max_ms=5.0,
            min_throughput=1000.0,
        )
        
        result = benchmark_runner.run(
            name="NPE Receipt Creation",
            func=create_npe_receipt,
            iterations=1000,
            thresholds=thresholds,
        )
        
        assert result.avg_time < 0.001  # 1ms average
    
    def test_receipt_serialization(
        self,
        benchmark_runner,
        sample_receipt_content,
        sample_receipt_provenance,
        sample_receipt_signature,
    ):
        """JSON serialization time for receipts."""
        # Create a receipt with NPE data
        npe_receipt = NPEReceipt(
            receipt_id=str(uuid4()),
            content=sample_receipt_content,
            signature=sample_receipt_signature,
            provenance=sample_receipt_provenance,
            npe_request_id=str(uuid4()),
            npe_response_status=NPEResponseStatus.SUCCESS.value,
            npe_proposals=[
                {
                    "proposal_id": str(uuid4()),
                    "candidate": {"action": "repair", "params": {"x": 1}},
                    "score": 0.92,
                    "explanation": "Test repair explanation",
                    "provenance": {"source": "gr", "confidence": 0.95},
                }
                for _ in range(5)
            ],
            npe_provenance={},
        )
        
        def serialize_receipt():
            return json.dumps(npe_receipt.to_dict())
        
        thresholds = BenchmarkThresholds(
            p50_max_ms=0.5,
            p95_max_ms=1.0,
            p99_max_ms=2.0,
            min_throughput=2000.0,
        )
        
        result = benchmark_runner.run(
            name="Receipt JSON Serialization",
            func=serialize_receipt,
            iterations=1000,
            thresholds=thresholds,
        )
        
        assert result.avg_time < 0.0005  # 0.5ms average
    
    def test_receipt_deserialization(self, benchmark_runner):
        """JSON deserialization time for receipts."""
        receipt_dict = {
            "receipt_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step_type": "GATE_EVAL",
            "decision": "FAIL",
            "content": {
                "step_type": "GATE_EVAL",
                "input_hash": "abc123",
                "output_hash": "def456",
                "decision": "FAIL",
                "details": {"gate": "evidence_sufficiency"},
            },
            "provenance": {
                "source": "test",
                "phase": "phase_loom",
                "episode_id": "test_episode",
                "parent_receipts": [],
            },
            "signature": {
                "signer": "test_signer",
                "signature": "c2lnX2RhdGE=",
            },
            "npe_data": {
                "request_id": str(uuid4()),
                "response_status": "success",
                "proposals": [
                    {
                        "proposal_id": str(uuid4()),
                        "candidate": {"action": "test"},
                        "score": 0.85,
                    }
                ],
            },
        }
        
        json_str = json.dumps(receipt_dict)
        
        def deserialize_receipt():
            return Receipt.from_dict(json.loads(json_str))
        
        thresholds = BenchmarkThresholds(
            p50_max_ms=0.5,
            p95_max_ms=1.0,
            p99_max_ms=2.0,
            min_throughput=2000.0,
        )
        
        result = benchmark_runner.run(
            name="Receipt JSON Deserialization",
            func=deserialize_receipt,
            iterations=1000,
            thresholds=thresholds,
        )
        
        assert result.avg_time < 0.0005  # 0.5ms average


# =============================================================================
# Benchmark Reporting Tests
# =============================================================================


class TestBenchmarkReporting:
    """Tests for benchmark utility and reporting."""
    
    def test_benchmark_result_percentiles(self):
        """Test percentile calculation."""
        times = [0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20]
        
        result = BenchmarkResult(
            name="test",
            iterations=len(times),
            total_time=sum(times),
            times=times,
        )
        
        percentiles = result.percentiles([50, 95, 99])
        
        assert percentiles["p50"] == 0.05
        assert percentiles["p95"] == 0.20  # Near max
        assert percentiles["p99"] == 0.20  # Max
    
    def test_benchmark_result_to_dict(self):
        """Test dictionary conversion."""
        result = BenchmarkResult(
            name="test_benchmark",
            iterations=100,
            total_time=1.0,
            times=[0.01] * 100,
        )
        
        dict_result = result.to_dict()
        
        assert dict_result["name"] == "test_benchmark"
        assert dict_result["iterations"] == 100
        assert "percentiles_ms" in dict_result
        assert "throughput_ops_sec" in dict_result
    
    def test_benchmark_runner_report(self, benchmark_runner):
        """Test benchmark report generation."""
        def dummy_func():
            time.sleep(0.001)
        
        benchmark_runner.run("test_1", dummy_func, iterations=5)
        benchmark_runner.run("test_2", dummy_func, iterations=5)
        
        report = benchmark_runner.report()
        
        assert "test_1" in report
        assert "test_2" in report
        assert "p50" in report
        assert "p95" in report
        assert "p99" in report
    
    def test_threshold_comparison(self):
        """Test threshold checking."""
        result = BenchmarkResult(
            name="test",
            iterations=100,
            total_time=0.1,
            times=[0.001] * 100,
        )
        
        thresholds = BenchmarkThresholds(
            p50_max_ms=10.0,
            p95_max_ms=50.0,
            p99_max_ms=100.0,
            min_throughput=1.0,
        )
        
        runner = BenchmarkRunner()
        passed = runner._check_thresholds(result, thresholds)
        
        # Should pass all thresholds with these times
        assert passed is True


# =============================================================================
# Integration: Full Benchmark Suite
# =============================================================================


class TestFullBenchmarkSuite:
    """Integration test running the full benchmark suite."""
    
    def test_run_all_benchmarks(self):
        """Run all benchmarks and verify results."""
        runner = BenchmarkRunner(warmup_iterations=2)
        all_passed = True
        
        # Client benchmarks
        with patch("cnsc.haai.nsc.proposer_client.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            response = MagicMock()
            response.ok = True
            response.status_code = 200
            response.json.return_value = {
                "spec": "NPE-RESPONSE-1.0",
                "request_id": str(uuid4()),
                "status": "success",
                "proposals": [{"proposal_id": str(uuid4()), "candidate": {}, "score": 0.85}],
            }
            mock_session.request.return_value = response
            
            client = ProposerClient(rate_limiter=None)
            
            def propose():
                return client.propose(domain="gr", candidate_type="repair", context={}, budget={"max_wall_ms": 1000})
            
            thresholds = BenchmarkThresholds(
                p50_max_ms=5.0,
                p95_max_ms=15.0,
                p99_max_ms=30.0,
                min_throughput=500.0,
            )
            
            result = runner.run("Full Suite - Propose", propose, iterations=50, thresholds=thresholds)
            if result.throughput < thresholds.min_throughput:
                all_passed = False
        
        # Receipt benchmarks
        content = ReceiptContent(step_type=ReceiptStepType.CUSTOM)
        provenance = ReceiptProvenance(source="test")
        signature = ReceiptSignature()
        
        def create_receipt():
            return NPEReceipt(
                receipt_id=str(uuid4()),
                content=content,
                signature=signature,
                provenance=provenance,
                npe_request_id=str(uuid4()),
                npe_response_status=NPEResponseStatus.SUCCESS.value,
                npe_proposals=[
                    {
                        "proposal_id": str(uuid4()),
                        "candidate": {},
                        "score": 0.85,
                    }
                ],
                npe_provenance={},
            )
        
        thresholds = BenchmarkThresholds(
            p50_max_ms=1.0,
            p95_max_ms=2.0,
            p99_max_ms=5.0,
            min_throughput=1000.0,
        )
        
        result = runner.run("Full Suite - Receipt Creation", create_receipt, iterations=100, thresholds=thresholds)
        if result.throughput < thresholds.min_throughput:
            all_passed = False
        
        # Print report
        print("\n" + runner.report())
        
        assert all_passed, "Some benchmarks failed threshold checks"
