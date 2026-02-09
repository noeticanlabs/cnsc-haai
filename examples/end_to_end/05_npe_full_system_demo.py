#!/usr/bin/env python3
"""
NPE Full System Demonstration Script

This script demonstrates the complete NPE (Noetican Proposal Engine) integration
with CNSC (Coherent Neural Symbolic Computation) system, showing end-to-end
functionality including:

1. Setup Phase - Initialize NPE service mock and CNSC kernel
2. Proposal Workflow - Submit proposals to NPE
3. Gate Repair Demo - Demonstrate repair proposals for failed gates
4. Receipt Audit Demo - Create and audit receipts with NPE data
5. Performance Demo - Benchmark NPE operations
6. Cleanup Phase - Properly close connections

Run with: python examples/end_to_end/05_npe_full_system_demo.py
"""

import json
import time
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cnsc.haai.nsc.proposer_client import ProposerClient
from cnsc.haai.nsc.gates import (
    Gate, 
    GateCondition, 
    GateResult, 
    GateDecision, 
    GateType,
    EvidenceSufficiencyGate,
    CoherenceCheckGate
)
from cnsc.haai.nsc.vm import VM, VMState, VMStack
from cnsc.haai.gml.receipts import (
    Receipt, 
    ReceiptContent, 
    ReceiptSignature, 
    ReceiptProvenance,
    NPEReceipt,
    ReceiptStepType,
    ReceiptDecision,
    NPEResponseStatus,
    HashChain,
)
from cnsc.haai.nsc.proposer_client_errors import (
    ConnectionError,
    ValidationError,
)


# =============================================================================
# Demo Utilities
# =============================================================================

def print_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n▶ {title}")
    print("-" * 50)


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"  ✓ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"  ℹ {message}")


def print_data(data: Any, indent: int = 2) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=indent, default=str))


# =============================================================================
# NPE Service Mock
# =============================================================================

class NPEServiceMock:
    """
    Mock NPE service for demonstration purposes.
    
    This simulates the NPE service responses without requiring
    an actual server to be running.
    """
    
    def __init__(self):
        self.request_count = 0
        self.repair_count = 0
        self.health_status = True
        
    def health_check(self) -> Dict[str, Any]:
        """Simulate health check response."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def propose(
        self, 
        domain: str, 
        candidate_type: str, 
        context: Dict[str, Any],
        budget: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate proposal request."""
        self.request_count += 1
        request_id = f"prop-{self.request_count:04d}"
        
        # Generate mock proposals
        proposals = []
        num_candidates = budget.get("max_candidates", 16)
        
        for i in range(min(num_candidates, 3)):  # Return max 3 for demo
            proposals.append({
                "proposal_id": f"{request_id}-c{i+1}",
                "candidate": {
                    "type": candidate_type,
                    "content": f"Sample {candidate_type} proposal {i+1} for domain {domain}",
                    "confidence": 0.7 + (i * 0.1)
                },
                "score": 0.8 - (i * 0.15),
                "evidence": [
                    {"source": "rulepack_1", "rule": f"rule_{i}"},
                    {"source": "template_lib", "template": f"template_{i}"}
                ],
                "explanation": f"This is a {candidate_type} proposal addressing the context.",
                "provenance": {
                    "source": "npe_mock",
                    "request_id": request_id,
                    "processing_time_ms": 50 + (i * 10)
                }
            })
        
        return {
            "request_id": request_id,
            "status": "success",
            "proposals": proposals,
            "metadata": {
                "domain": domain,
                "candidate_type": candidate_type,
                "total_candidates": len(proposals),
                "processing_time_ms": sum(p["provenance"]["processing_time_ms"] for p in proposals)
            }
        }
    
    def repair(
        self,
        gate_name: str,
        failure_reasons: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate repair request."""
        self.repair_count += 1
        request_id = f"repair-{self.repair_count:04d}"
        
        # Generate mock repair proposals
        proposals = []
        for i, reason in enumerate(failure_reasons[:2]):  # Max 2 repairs
            proposals.append({
                "proposal_id": f"{request_id}-r{i+1}",
                "candidate": {
                    "type": "repair",
                    "repair_type": "condition_adjustment",
                    "description": f"Repair for '{reason}'",
                    "suggested_threshold": 0.5 - (i * 0.1)
                },
                "score": 0.85 - (i * 0.1),
                "evidence": [
                    {"source": "repair_map", "rule": f"repair_for_{reason}"},
                    {"source": "gate_logic", "condition": f"adjust_{gate_name}"}
                ],
                "explanation": f"Adjust gate conditions to address: {reason}",
                "provenance": {
                    "source": "npe_mock",
                    "request_id": request_id,
                    "processing_time_ms": 30 + (i * 15)
                }
            })
        
        return {
            "request_id": request_id,
            "status": "success",
            "proposals": proposals,
            "metadata": {
                "gate_name": gate_name,
                "failure_reasons": failure_reasons,
                "total_repairs": len(proposals),
                "processing_time_ms": sum(p["provenance"]["processing_time_ms"] for p in proposals)
            }
        }


class MockProposerClient(ProposerClient):
    """
    Mock ProposerClient that uses NPEServiceMock instead of HTTP.
    
    This allows demonstration of NPE workflows without requiring
    an actual NPE server.
    """
    
    def __init__(self):
        # Don't call parent __init__ to avoid HTTP setup
        self._mock = NPEServiceMock()
        self._request_count = 0
        
    def health(self) -> bool:
        """Check mock service health."""
        try:
            result = self._mock.health_check()
            return result.get("status") == "healthy"
        except Exception:
            return False
    
    def get_health_details(self) -> Optional[Dict[str, Any]]:
        """Get mock health details."""
        return self._mock.health_check()
    
    def propose(
        self,
        domain: str,
        candidate_type: str,
        context: Dict[str, Any],
        budget: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Submit mock proposal request."""
        self._request_count += 1
        # Validate inputs (mimic parent behavior)
        self._validate_domain(domain)
        self._validate_candidate_type(candidate_type)
        self._validate_budget(budget)
        
        return self._mock.propose(domain, candidate_type, context, budget)
    
    def repair(
        self,
        gate_name: str,
        failure_reasons: List[str],
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Submit mock repair request."""
        # Validate inputs
        if not isinstance(gate_name, str) or len(gate_name) == 0:
            raise ValidationError(field="gate_name", message="Gate name must be a non-empty string")
        
        if not isinstance(failure_reasons, list) or len(failure_reasons) == 0:
            raise ValidationError(field="failure_reasons", message="Failure reasons must be a non-empty list")
        
        if budget is not None:
            self._validate_budget(budget)
        
        return self._mock.repair(gate_name, failure_reasons, context)
    
    def close(self) -> None:
        """Close mock client (no-op)."""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# =============================================================================
# Demo Classes
# =============================================================================

class NPEDemoSystem:
    """
    Demonstration system for NPE + CNSC integration.
    """
    
    def __init__(self):
        self.client: Optional[MockProposerClient] = None
        self.receipts: List[Receipt] = []
        self.chain: Optional[HashChain] = None
        self.performance_metrics: Dict[str, List[float]] = {}
        
    def setup(self) -> None:
        """Initialize the demonstration system."""
        print_header("PHASE 1: SETUP")
        
        print_subheader("Importing Modules")
        print_info("All required modules imported successfully")
        
        print_subheader("Creating NPE Service Mock")
        self.client = MockProposerClient()
        print_success("Mock NPE service created")
        
        print_subheader("Initializing CNSC Kernel")
        print_info(f"Client version: {self.client._request_count} requests processed")
        print_success("CNSC kernel initialized with ProposerClient")
        
        # Initialize hash chain
        self.chain = HashChain()
        print_success(f"Hash chain initialized (genesis: {self.chain.get_root()[:16]}...)")
        
    def demo_proposal_workflow(self) -> None:
        """Demonstrate proposal workflow."""
        print_header("PHASE 2: PROPOSAL WORKFLOW DEMO")
        
        print_subheader("Submitting Proposal Request")
        budget = {
            "max_wall_ms": 1000,
            "max_candidates": 5,
            "max_input_tokens": 10000,
            "max_output_tokens": 4000,
        }
        context = {
            "task_type": "reasoning",
            "complexity": "medium",
        }
        
        start_time = time.perf_counter()
        response = self.client.propose(
            domain="gr",
            candidate_type="proposal",
            context=context,
            budget=budget,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Record metric
        self.performance_metrics.setdefault("proposal_latency", []).append(elapsed_ms)
        
        print_success(f"Proposal request submitted")
        print_info(f"Request ID: {response['request_id']}")
        print_info(f"Status: {response['status']}")
        print_info(f"Candidates returned: {len(response['proposals'])}")
        print_info(f"Latency: {elapsed_ms:.2f}ms")
        
        print_subheader("Proposal Response Details")
        print_data(response["metadata"])
        
        print_subheader("Creating Proposal Receipt")
        receipt = self._create_proposal_receipt(response, budget)
        self.receipts.append(receipt)
        self.chain.append(receipt)
        print_success(f"Receipt created: {receipt.receipt_id[:16]}...")
        
    def demo_gate_repair(self) -> None:
        """Demonstrate gate repair workflow."""
        print_header("PHASE 3: GATE REPAIR DEMO")
        
        print_subheader("Creating Failing Gate")
        
        # Create a gate with conditions that will fail
        gate = EvidenceSufficiencyGate(
            gate_id="demo_affordability",
            name="Affordability Gate",
            min_evidence_count=5,  # High threshold
            min_coherence=0.8,      # High threshold
        )
        
        # Attach proposer client for repairs
        gate.proposer_client = self.client
        
        print_info(f"Gate: {gate.name}")
        print_info(f"Required evidence: {gate.min_evidence_count}")
        print_info(f"Required coherence: {gate.min_coherence}")
        
        # Evaluate with insufficient context (will fail)
        insufficient_context = {
            "evidence_count": 2,  # Less than required 5
            "coherence_level": 0.6,  # Less than required 0.8
        }
        
        print_subheader("Evaluating Gate (Expected to Fail)")
        result = gate.evaluate(insufficient_context)
        
        print_info(f"Decision: {result.decision.name}")
        print_info(f"Message: {result.message}")
        print_info(f"Conditions passed: {result.conditions_passed}")
        print_info(f"Conditions failed: {result.conditions_failed}")
        
        if result.is_fail():
            print_success("Gate failed as expected - demonstrating repair workflow")
            
            print_subheader("Requesting Repair Proposals")
            failure_reasons = [
                "insufficient_evidence",
                "coherence_below_threshold",
            ]
            
            start_time = time.perf_counter()
            proposals = gate.request_repair(gate.name, failure_reasons)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            self.performance_metrics.setdefault("repair_latency", []).append(elapsed_ms)
            
            print_success(f"Repair proposals received: {len(proposals)}")
            print_info(f"Latency: {elapsed_ms:.2f}ms")
            
            if proposals:
                print_subheader("Repair Proposals")
                for i, proposal in enumerate(proposals):
                    print(f"  Proposal {i+1}:")
                    print_data(proposal, indent=4)
        
        # Create repair receipt
        print_subheader("Creating Repair Receipt")
        repair_receipt = self._create_repair_receipt(gate, result, proposals)
        self.receipts.append(repair_receipt)
        self.chain.append(repair_receipt)
        print_success(f"Repair receipt created: {repair_receipt.receipt_id[:16]}...")
        
    def demo_receipt_audit(self) -> None:
        """Demonstrate receipt audit functionality."""
        print_header("PHASE 4: RECEIPT AUDIT DEMO")
        
        print_subheader("Creating NPE-Enhanced Receipt")
        
        # Create receipt using NPEReceipt factory
        npe_receipt = NPEReceipt.create_npe_receipt(
            receipt_id="audit-demo-001",
            request_id="prop-demo-001",
            domain="gr",
            candidate_type="explanation",
            proposals=[
                {
                    "proposal_id": "exp-001",
                    "explanation": "Detailed reasoning explanation"
                }
            ],
            response_status=NPEResponseStatus.SUCCESS.value,
        )
        
        print_success("NPEReceipt created using factory method")
        
        print_subheader("Recording NPE Request Details")
        npe_receipt.record_npe_request(
            request_id="recorded-req-001",
            domain="gr",
            candidate_type="proposal",
            seed=42,
            budgets={"max_wall_ms": 1000, "max_candidates": 8},
            inputs={"query": "sample query"},
        )
        print_success("NPE request recorded on receipt")
        
        print_subheader("Recording NPE Response Details")
        npe_receipt.record_npe_response(
            status=NPEResponseStatus.SUCCESS.value,
            proposals=[{"id": "p1", "content": "test"}],
            budget_used={"max_wall_ms": 1000},
        )
        print_success("NPE response recorded on receipt")
        
        print_subheader("Getting NPE Metadata")
        metadata = npe_receipt.get_npe_metadata()
        print_info("NPE Metadata retrieved:")
        print_data(metadata)
        
        print_subheader("Receipt Serialization")
        receipt_dict = npe_receipt.to_dict()
        print_info("Receipt as dictionary:")
        print_data(receipt_dict)
        
        # Verify we can deserialize
        print_subheader("Receipt Deserialization")
        restored = Receipt.from_dict(receipt_dict)
        print_success(f"Receipt restored: {restored.receipt_id}")
        
        # Add to our collection
        self.receipts.append(npe_receipt)
        self.chain.append(npe_receipt)
        
    def demo_performance(self) -> None:
        """Demonstrate performance metrics."""
        print_header("PHASE 5: PERFORMANCE DEMO")
        
        print_subheader("Running Benchmarks")
        
        iterations = 5
        
        # Benchmark proposals
        print_info(f"Running {iterations} proposal iterations...")
        for i in range(iterations):
            start = time.perf_counter()
            self.client.propose(
                domain="gr",
                candidate_type="benchmark",
                context={"iteration": i},
                budget={"max_wall_ms": 100, "max_candidates": 2},
            )
            elapsed = (time.perf_counter() - start) * 1000
            self.performance_metrics.setdefault("proposal_latency", []).append(elapsed)
        
        # Benchmark repairs
        print_info(f"Running {iterations} repair iterations...")
        for i in range(iterations):
            start = time.perf_counter()
            self.client.repair(
                gate_name="benchmark_gate",
                failure_reasons=[f"reason_{i}"],
                context={},
            )
            elapsed = (time.perf_counter() - start) * 1000
            self.performance_metrics.setdefault("repair_latency", []).append(elapsed)
        
        print_subheader("Performance Results")
        
        for metric, values in self.performance_metrics.items():
            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            print(f"\n  {metric}:")
            print(f"    Average: {avg:.2f}ms")
            print(f"    Min: {min_val:.2f}ms")
            print(f"    Max: {max_val:.2f}ms")
            print(f"    Samples: {len(values)}")
        
        print_subheader("Receipt Chain Statistics")
        print_info(f"Total receipts created: {len(self.receipts)}")
        print_info(f"Chain length: {self.chain.get_length()}")
        print_info(f"Chain tip: {self.chain.get_tip()[:32]}...")
        
    def demo_verification(self) -> None:
        """Demonstrate receipt verification."""
        print_header("PHASE 6: RECEIPT VERIFICATION")
        
        print_subheader("Verifying Hash Chain")
        
        if self.chain and len(self.chain.chain) > 1:
            all_valid = True
            for i, (chain_hash, timestamp) in enumerate(self.chain.chain):
                is_valid = self.chain.verify(i, chain_hash)
                status = "✓" if is_valid else "✗"
                print(f"  {status} Index {i}: {chain_hash[:16]}... [{timestamp.isoformat()}]")
                if not is_valid:
                    all_valid = False
            
            print_success(f"Chain verification: {'PASSED' if all_valid else 'FAILED'}")
        else:
            print_info("No chain to verify")
        
        print_subheader("Receipt Content Verification")
        for i, receipt in enumerate(self.receipts):
            content_hash = receipt.compute_hash()
            chain_hash = receipt.chain_hash
            print(f"  Receipt {i+1}:")
            print(f"    ID: {receipt.receipt_id[:24]}...")
            print(f"    Content hash: {content_hash[:16]}...")
            print(f"    Chain hash: {chain_hash[:16] if chain_hash else 'None'}...")
        
    def cleanup(self) -> None:
        """Clean up resources."""
        print_header("PHASE 7: CLEANUP")
        
        print_subheader("Closing Connections")
        if self.client:
            self.client.close()
            print_success("ProposerClient closed")
        
        print_subheader("Cleaning Up Resources")
        self.receipts.clear()
        self.chain = None
        self.performance_metrics.clear()
        print_success("All resources cleaned up")
        
        print_success("Demo cleanup complete")
    
    def _create_proposal_receipt(
        self, 
        response: Dict[str, Any], 
        budget: Dict[str, Any]
    ) -> Receipt:
        """Create a receipt for a proposal."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
            details={
                "npe_operation": "propose",
                "domain": "gr",
                "candidate_type": "proposal",
                "candidates_returned": len(response["proposals"]),
                "budget_used": budget,
            },
            coherence_before=0.5,
            coherence_after=0.7,
        )
        
        signature = ReceiptSignature(signer="cnsc_demo")
        
        provenance = ReceiptProvenance(
            source="npe_demo",
            episode_id="proposal_workflow",
            phase="demonstration",
        )
        
        receipt = Receipt(
            receipt_id=f"receipt-prop-{response['request_id']}",
            content=content,
            signature=signature,
            provenance=provenance,
            npe_request_id=response["request_id"],
            npe_response_status=response["status"],
            npe_proposals=response["proposals"],
            npe_provenance=response.get("metadata", {}),
        )
        
        # Compute chain hash
        previous_hash = self.chain.get_tip() if self.chain else None
        receipt.previous_receipt_hash = previous_hash
        receipt.chain_hash = receipt.compute_chain_hash(previous_hash)
        
        return receipt
    
    def _create_repair_receipt(
        self, 
        gate: Gate, 
        result: GateResult,
        proposals: List[Dict[str, Any]]
    ) -> Receipt:
        """Create a receipt for a repair."""
        content = ReceiptContent(
            step_type=ReceiptStepType.GATE_EVAL,
            decision=ReceiptDecision.FAIL,
            details={
                "gate_id": gate.gate_id,
                "gate_name": gate.name,
                "gate_type": gate.gate_type.name,
                "evaluation_message": result.message,
                "conditions_passed": result.conditions_passed,
                "conditions_failed": result.conditions_failed,
                "repairs_requested": len(proposals),
            },
            coherence_before=result.coherence_level,
            coherence_after=result.coherence_level,
        )
        
        signature = ReceiptSignature(signer="cnsc_demo")
        
        provenance = ReceiptProvenance(
            source="npe_demo",
            episode_id="gate_repair",
            phase="demonstration",
        )
        
        receipt = Receipt(
            receipt_id=f"receipt-repair-{gate.gate_id}",
            content=content,
            signature=signature,
            provenance=provenance,
            npe_proposals=proposals,
            npe_provenance={"gate_name": gate.name, "repair_count": len(proposals)},
        )
        
        # Compute chain hash
        previous_hash = self.chain.get_tip() if self.chain else None
        receipt.previous_receipt_hash = previous_hash
        receipt.chain_hash = receipt.compute_chain_hash(previous_hash)
        
        return receipt


# =============================================================================
# Main Demo Entry Point
# =============================================================================

def main():
    """Run the full NPE system demonstration."""
    
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "NPE FULL SYSTEM DEMO" + " " * 24 + "║")
    print("║" + " " * 15 + "CNSC + NPE Integration Demonstration" + " " * 14 + "║")
    print("╚" + "=" * 68 + "╝")
    
    demo = NPEDemoSystem()
    
    try:
        # Run all demo phases
        demo.setup()
        demo.demo_proposal_workflow()
        demo.demo_gate_repair()
        demo.demo_receipt_audit()
        demo.demo_performance()
        demo.demo_verification()
        
        # Final summary
        print_header("DEMO COMPLETE")
        print_success("All NPE integration demonstrations completed successfully!")
        print_info("The CNSC kernel successfully interfaces with NPE for:")
        print("  • Proposal generation")
        print("  • Gate repair recommendations")
        print("  • Receipt tracking and auditing")
        print("  • Performance monitoring")
        print("\n" + "=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        raise
    finally:
        # Always cleanup
        demo.cleanup()


if __name__ == "__main__":
    main()
