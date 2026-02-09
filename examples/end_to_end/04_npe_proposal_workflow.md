# NPE Proposal Workflow (End-to-End)

**Layer:** CNSC-NPE Integration  
**Purpose:** Demonstrates NPE service integration with CNSC for proposal generation and gate repair

This walkthrough shows how to:
1. Start and configure the NPE service
2. Submit proposal requests using CLI and Python API
3. Handle gate failures with repair workflows
4. Track and audit NPE interactions via receipts

---

## 1. Prerequisites

### 1.1 NPE Service Setup

The NPE (Noetican Proposal Engine) service requires:

```bash
# Install NPE dependencies
pip install -e npe/

# Verify installation
python -c "from npe.api.routes import NPEService; print('NPE installed successfully')"
```

### 1.2 Required Assets

The NPE service requires indexed assets for proposal generation:

| Asset | Location | Purpose |
|-------|----------|---------|
| Corpus | `npe_assets/corpus/` | Knowledge base for proposals |
| Codebook | `npe_assets/codebook.json` | GLLL encoding reference |
| Receipts Index | `npe_assets/receipts/` | Historical receipt data |

```bash
# Build NPE index from corpus and receipts
cnsc-haai npe index \
    --corpus npe_assets/corpus \
    --receipts npe_assets/receipts \
    --out npe_assets/index
```

### 1.3 Configuration

Create a configuration file for NPE settings:

```yaml
# config/npe.yaml
npe:
  host: "localhost"
  port: 8000
  assets_path: "npe_assets/index"
  budgets:
    max_wall_ms: 1000
    max_candidates: 16
    max_evidence_items: 100
    max_search_expansions: 50
  domains:
    - "gr"  # General reasoning
```

---

## 2. Starting the NPE Service

### 2.1 Using CLI

```bash
# Start NPE service in foreground (development)
cnsc-haai npe start --host localhost --port 8000

# Start in background (production)
cnsc-haai npe start --host 0.0.0.0 --port 8000 --daemon

# Start with custom assets
cnsc-haai npe start --assets npe_assets/index
```

**Output:**
```
✓ NPE service starting on http://localhost:8000
✓ Loaded registry with 3 proposers
✓ Corpus index loaded (1,234 chunks)
✓ Receipts index loaded (567 receipts)
✓ Service ready for requests
```

### 2.2 Using Python API

```python
from npe.api.server import create_app
from npe.api.routes import NPEService, setup_routes
from npe.registry.loader import load_registry

async def start_npe_service():
    """Start NPE service programmatically."""
    
    # Load registry and create service
    registry = load_registry()
    service = NPEService(registry)
    
    # Create aiohttp app
    app = create_app()
    router = NPEServiceRouter(service)
    setup_routes(app, router)
    
    # Start server (using aiohttp)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8000)
    await site.start()
    
    print("✓ NPE service running on http://localhost:8000")
    return runner

# Cleanup
# await runner.cleanup()
```

### 2.3 Health Verification

```python
from cnsc.haai.nsc.proposer_client import ProposerClient

def check_npe_health():
    """Verify NPE service is healthy."""
    
    client = ProposerClient(base_url="http://localhost:8000")
    
    # Quick health check
    is_healthy = client.health()
    print(f"Health check: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
    
    # Detailed health info
    details = client.get_health_details()
    if details:
        print(f"  Version: {details.get('version', 'unknown')}")
        print(f"  Registry hash: {details.get('registry_hash', 'unknown')}")
        print(f"  Corpus chunks: {details.get('corpus_chunks', 0)}")
    
    client.close()
    return is_healthy
```

---

## 3. Submitting a Proposal

### 3.1 Using CLI

```bash
# Create proposal request file
cat > /tmp/proposal_request.json << 'EOF'
{
  "spec": "NPE-REQUEST-1.0",
  "request_type": "propose",
  "domain": "gr",
  "determinism_tier": "d0",
  "seed": 0,
  "budgets": {
    "max_wall_ms": 1000,
    "max_candidates": 8,
    "max_evidence_items": 50,
    "max_search_expansions": 25
  },
  "inputs": {
    "candidate_type": "explanation",
    "context": {
      "query": "Explain the coherence principle",
      "constraints": ["formal", "accessible"]
    }
  }
}
EOF

# Submit proposal
cnsc-haai npe propose --request /tmp/proposal_request.json --output /tmp/proposal_response.json
```

**Output:**
```
✓ Proposal request submitted
  Request ID: abc123-def456
  Domain: gr
  Candidates: 3 returned
```

### 3.2 Using Python API

```python
from cnsc.haai.nsc.proposer_client import ProposerClient

def submit_proposal():
    """Submit a proposal request to NPE."""
    
    client = ProposerClient(base_url="http://localhost:8000")
    
    # Define proposal request
    response = client.propose(
        domain="gr",
        candidate_type="explanation",
        context={
            "query": "Explain the coherence principle",
            "constraints": ["formal", "accessible"],
            "style": "technical",
        },
        budget={
            "max_wall_ms": 1000,
            "max_candidates": 8,
        },
    )
    
    print(f"Response ID: {response.get('response_id')}")
    print(f"Registry Hash: {response.get('registry_hash')}")
    print(f"Candidates: {len(response.get('candidates', []))}")
    
    # Process candidates
    for candidate in response.get("candidates", []):
        print(f"  - {candidate.get('candidate_type')}: "
              f"score={candidate.get('scores', {}).get('confidence', 'N/A')}")
    
    client.close()
    return response
```

### 3.3 Understanding the Response

```python
def parse_proposal_response(response: dict) -> None:
    """Parse and understand NPE proposal response."""
    
    print("=" * 60)
    print("NPE Proposal Response Analysis")
    print("=" * 60)
    
    # Response metadata
    print(f"\n[Metadata]")
    print(f"  Response ID: {response.get('response_id')}")
    print(f"  Request ID: {response.get('request_id')}")
    print(f"  Domain: {response.get('domain')}")
    print(f"  Registry Hash: {response.get('registry_hash')}")
    print(f"  Determinism Tier: {response.get('determinism_tier')}")
    print(f"  Seed: {response.get('seed')}")
    
    # Candidates
    print(f"\n[Candidates: {len(response.get('candidates', []))}]")
    for i, candidate in enumerate(response.get("candidates", []), 1):
        scores = candidate.get("scores", {})
        print(f"\n  [{i}] {candidate.get('candidate_type')}")
        print(f"      Hash: {candidate.get('candidate_hash')}")
        print(f"      Risk: {scores.get('risk', 'N/A')}")
        print(f"      Utility: {scores.get('utility', 'N/A')}")
        print(f"      Cost: {scores.get('cost', 'N/A')}")
        print(f"      Confidence: {scores.get('confidence', 'N/A')}")
    
    # Diagnostics
    diagnostics = response.get("diagnostics", {})
    print(f"\n[Diagnostics]")
    print(f"  Request Count: {diagnostics.get('request_count', 0)}")
    print(f"  Budget Summary: {diagnostics.get('budget_summary', {})}")
```

---

## 4. Gate Repair Workflow

### 4.1 Scenario: Gate Fails During NSC Execution

```python
from cnsc.haai.nsc.gates import GatePolicy, Gate, GateDecision
from cnsc.haai.nsc.vm import VM, VMState

def execute_with_gate_failure():
    """Execute bytecode that triggers a gate failure."""
    
    # Create gate policy with strict evidence threshold
    policy = GatePolicy(policy_id="strict-policy")
    policy.add_gate(Gate(
        name="evidence_sufficiency",
        gate_type="hard",
        threshold=0.95,  # Very high threshold
        description="Require 95% evidence sufficiency"
    ))
    
    # Create VM with low evidence state
    vm = VM(
        bytecode=bytecode,
        gate_policy=policy,
    )
    
    # Simulate low evidence state
    vm.state.evidence = 0.7  # Below 0.95 threshold
    
    # Execute - gate will fail
    while not vm.halted:
        result = vm.execute_step()
        
        # Check gates
        for gate in policy.gates:
            if gate.name == "evidence_sufficiency":
                if vm.state.evidence < gate.threshold:
                    print(f"✗ GATE FAILURE: {gate.name}")
                    print(f"  Evidence: {vm.state.evidence} < {gate.threshold}")
                    return gate.name, ["Insufficient evidence"]
    
    return None, []
```

### 4.2 Requesting Repair from NPE

```python
from cnsc.haai.nsc.proposer_client import ProposerClient

def request_gate_repair(gate_name: str, failure_reasons: list) -> dict:
    """Request repair proposal from NPE for failed gate."""
    
    client = ProposerClient(base_url="http://localhost:8000")
    
    # Build repair context
    context = {
        "gate_name": gate_name,
        "policy_id": "strict-policy",
        "current_evidence": 0.7,
        "threshold": 0.95,
        "goal_evidence": 0.95,
        "strategy": "increase_evidence",
    }
    
    # Submit repair request
    response = client.repair(
        gate_name=gate_name,
        failure_reasons=failure_reasons,
        context=context,
    )
    
    print(f"Repair Response ID: {response.get('response_id')}")
    print(f"Candidates: {len(response.get('candidates', []))}")
    
    client.close()
    return response
```

### 4.3 Applying the Repair

```python
def apply_repair(repair_response: dict, vm: VM) -> bool:
    """Apply NPE repair proposal to fix gate failure."""
    
    candidates = repair_response.get("candidates", [])
    if not candidates:
        print("No repair candidates available")
        return False
    
    # Get highest confidence candidate
    best_candidate = max(candidates, 
        key=lambda c: c.get("scores", {}).get("confidence", 0))
    
    repair = best_candidate.get("candidate", {})
    repair_type = repair.get("type")
    
    print(f"Applying repair: {repair_type}")
    
    if repair_type == "evidence_boost":
        # Increase evidence score
        boost_amount = repair.get("boost_amount", 0.3)
        vm.state.evidence = min(1.0, vm.state.evidence + boost_amount)
        print(f"  Boosted evidence: {vm.state.evidence}")
        return True
    
    elif repair_type == "relax_constraint":
        # Relax gate constraint
        new_threshold = repair.get("new_threshold", 0.8)
        for gate in vm.gate_policy.gates:
            if gate.name == repair.get("gate_name"):
                gate.threshold = new_threshold
                print(f"  Relaxed threshold: {new_threshold}")
        return True
    
    else:
        print(f"Unknown repair type: {repair_type}")
        return False
```

---

## 5. Receipt Tracking

### 5.1 NPE-Specific Receipt Fields

The [`Receipt`](src/cnsc/haai/gml/receipts.py:356) class includes NPE-specific fields:

```python
from cnsc.haai.gml.receipts import (
    Receipt,
    ReceiptContent,
    ReceiptSignature,
    ReceiptProvenance,
    ReceiptStepType,
    ReceiptDecision,
)

# Receipt fields for NPE tracking
receipt = Receipt(
    receipt_id="receipt_abc123",
    content=ReceiptContent(
        step_type=ReceiptStepType.CUSTOM,
        decision=ReceiptDecision.PASS,
        details={"npe_domain": "gr"},
    ),
    signature=ReceiptSignature(signer="npe"),
    provenance=ReceiptProvenance(source="npe", phase="proposal"),
    
    # NPE-specific fields
    npe_request_id="req_xyz789",
    npe_response_status="success",
    npe_proposals=[...],  # List of proposal dicts
    npe_provenance={
        "source": "npe",
        "episode_id": "episode_001",
        "phase": "proposal",
        "npe_request_id": "req_xyz789",
        "npe_response_id": "resp_abc123",
    },
)
```

### 5.2 Recording NPE Data on Receipts

```python
def record_npe_on_receipt(receipt: Receipt, request_id: str, response: dict) -> None:
    """Record NPE request and response on a receipt."""
    
    # Record request
    receipt.record_npe_request(
        request_id=request_id,
        domain=response.get("domain", "gr"),
        candidate_type=response.get("inputs", {}).get("candidate_type", "unknown"),
        seed=response.get("seed", 0),
        budgets=response.get("budgets", {}),
        inputs=response.get("inputs", {}),
    )
    
    # Record response
    receipt.record_npe_response(
        status="success",
        proposals=response.get("candidates", []),
        budget_used=response.get("diagnostics", {}).get("budget_summary", {}),
        npe_version="1.0.0",
    )
    
    # Record provenance
    receipt.record_npe_provenance(
        episode_id="episode_001",
        phase="proposal",
        npe_request_id=request_id,
        npe_response_id=response.get("response_id"),
    )
```

### 5.3 Retrieving Proposal Metadata

```python
def get_npe_metadata(receipt: Receipt) -> dict:
    """Extract NPE metadata from a receipt."""
    
    metadata = receipt.get_npe_metadata()
    
    return {
        "has_npe_data": metadata["has_npe_data"],
        "request_id": metadata["request_id"],
        "response_status": metadata["response_status"],
        "proposal_count": metadata["proposal_count"],
        "proposals": metadata["proposals"],
        "provenance": metadata["provenance"],
        "request_details": metadata["request_details"],
        "response_details": metadata["response_details"],
    }
```

### 5.4 Audit and Replay

```python
from cnsc.haai.gml.receipts import HashChain, ChainValidator

def audit_npe_receipt_chain(receipts: list) -> tuple:
    """Audit receipt chain with NPE data for integrity."""
    
    # Create validator
    validator = ChainValidator(signing_key="demo-vm-key")
    
    # Validate each receipt
    for receipt in receipts:
        if receipt.has_npe_data():
            valid, message = validator.validate_receipt(receipt)
            print(f"Receipt {receipt.receipt_id[:8]}: {message}")
            
            # Show NPE metadata for audit
            meta = get_npe_metadata(receipt)
            if meta["has_npe_data"]:
                print(f"  NPE Request: {meta['request_id']}")
                print(f"  NPE Proposals: {meta['proposal_count']}")
                print(f"  Episode: {meta['provenance'].get('episode_id', 'N/A')}")
    
    return True
```

---

## 6. Full Example Code

Complete Python script demonstrating the full NPE workflow:

```python
#!/usr/bin/env python3
"""
NPE Proposal Workflow - Complete End-to-End Example

This script demonstrates:
1. Starting NPE service
2. Creating ProposerClient
3. Submitting proposal request
4. Handling response
5. Recording receipt with NPE data
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from cnsc.haai.nsc.proposer_client import ProposerClient
from cnsc.haai.gml.receipts import (
    Receipt,
    ReceiptContent,
    ReceiptSignature,
    ReceiptProvenance,
    ReceiptStepType,
    ReceiptDecision,
    HashChain,
)
from cnsc.haai.nsc.gates import GatePolicy, Gate, GateDecision


class NPEWorkflow:
    """Complete NPE proposal workflow."""
    
    def __init__(self, npe_url: str = "http://localhost:8000"):
        self.npe_url = npe_url
        self.client: Optional[ProposerClient] = None
        self.receipts: list = []
        self.chain = HashChain()
        self.signing_key = "workflow-demo-key"
    
    def start(self) -> bool:
        """Start NPE client and verify service health."""
        print("=" * 60)
        print("Step 1: Starting NPE Client")
        print("=" * 60)
        
        self.client = ProposerClient(base_url=self.npe_url)
        is_healthy = self.client.health()
        
        if is_healthy:
            print(f"✓ Connected to NPE at {self.npe_url}")
            details = self.client.get_health_details()
            if details:
                print(f"  Version: {details.get('version', 'unknown')}")
                print(f"  Registry: {details.get('registry_hash', 'unknown')[:16]}...")
        else:
            print(f"✗ NPE service at {self.npe_url} is not healthy")
        
        return is_healthy
    
    def submit_proposal(
        self,
        domain: str = "gr",
        candidate_type: str = "explanation",
        context: Dict[str, Any] = None,
        budget: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Submit proposal request to NPE."""
        print("\n" + "=" * 60)
        print("Step 2: Submitting Proposal Request")
        print("=" * 60)
        
        if not self.client:
            raise RuntimeError("NPE client not started")
        
        request_context = context or {
            "query": "Explain the coherence principle",
            "constraints": ["formal", "accessible"],
        }
        
        request_budget = budget or {
            "max_wall_ms": 1000,
            "max_candidates": 8,
        }
        
        print(f"  Domain: {domain}")
        print(f"  Candidate Type: {candidate_type}")
        print(f"  Context: {request_context}")
        
        response = self.client.propose(
            domain=domain,
            candidate_type=candidate_type,
            context=request_context,
            budget=request_budget,
        )
        
        print(f"\n✓ Response received")
        print(f"  Response ID: {response.get('response_id')}")
        print(f"  Candidates: {len(response.get('candidates', []))}")
        
        return response
    
    def handle_gate_failure(self) -> Dict[str, Any]:
        """Simulate gate failure and request repair."""
        print("\n" + "=" * 60)
        print("Step 3: Gate Failure and Repair Request")
        print("=" * 60)
        
        if not self.client:
            raise RuntimeError("NPE client not started")
        
        # Simulate gate failure
        gate_name = "evidence_sufficiency"
        failure_reasons = ["Evidence below threshold", "Current: 0.7, Required: 0.95"]
        
        print(f"✗ Gate failed: {gate_name}")
        print(f"  Reasons: {failure_reasons}")
        
        # Request repair
        repair_context = {
            "gate_name": gate_name,
            "current_evidence": 0.7,
            "threshold": 0.95,
            "policy_id": "strict-policy",
        }
        
        response = self.client.repair(
            gate_name=gate_name,
            failure_reasons=failure_reasons,
            context=repair_context,
        )
        
        print(f"\n✓ Repair response received")
        print(f"  Candidates: {len(response.get('candidates', []))}")
        
        return response
    
    def record_receipt(
        self,
        step_type: str,
        request_id: str,
        response: Dict[str, Any],
        decision: str = "PASS",
    ) -> Receipt:
        """Record NPE interaction as a receipt."""
        print("\n" + "=" * 60)
        print("Step 4: Recording Receipt with NPE Data")
        print("=" * 60)
        
        # Create receipt content
        content = ReceiptContent(
            step_type=ReceiptStepType[step_type] if step_type in ReceiptStepType.__members__ else ReceiptStepType.CUSTOM,
            decision=ReceiptDecision[decision] if decision in ReceiptDecision.__members__ else ReceiptDecision.PASS,
            details={
                "npe_domain": response.get("domain", "gr"),
                "candidate_count": len(response.get("candidates", [])),
            },
        )
        
        # Create signature
        signature = ReceiptSignature(signer="npe-client")
        
        # Create provenance
        provenance = ReceiptProvenance(
            source="npe-client",
            phase=step_type.lower(),
            timestamp=datetime.utcnow(),
        )
        
        # Create receipt
        receipt_id = f"receipt_{uuid.uuid4().hex[:16]}"
        receipt = Receipt(
            receipt_id=receipt_id,
            content=content,
            signature=signature,
            provenance=provenance,
            previous_receipt_id=self.chain.get_tip() if self.chain.get_length() > 0 else None,
        )
        
        # Record NPE data
        receipt.record_npe_request(
            request_id=request_id,
            domain=response.get("domain", "gr"),
            candidate_type=response.get("inputs", {}).get("candidate_type", "unknown"),
            seed=response.get("seed", 0),
            budgets=response.get("budgets", {}),
            inputs=response.get("inputs", {}),
        )
        
        receipt.record_npe_response(
            status="success",
            proposals=response.get("candidates", []),
            budget_used=response.get("diagnostics", {}).get("budget_summary", {}),
        )
        
        receipt.record_npe_provenance(
            episode_id="workflow-demo-001",
            phase=step_type.lower(),
            npe_request_id=request_id,
            npe_response_id=response.get("response_id"),
        )
        
        # Compute chain hash
        receipt.chain_hash = receipt.compute_chain_hash(receipt.previous_receipt_hash)
        
        # Sign receipt
        content_hash = receipt.content.compute_hash()
        receipt.signature.sign(content_hash, self.signing_key)
        
        # Add to chain
        self.chain.append(receipt)
        self.receipts.append(receipt)
        
        print(f"✓ Receipt created: {receipt_id[:16]}")
        print(f"  NPE Request ID: {receipt.npe_request_id}")
        print(f"  Proposals: {len(receipt.npe_proposals)}")
        print(f"  Chain Length: {self.chain.get_length()}")
        
        return receipt
    
    def audit_chain(self) -> bool:
        """Audit the receipt chain."""
        print("\n" + "=" * 60)
        print("Step 5: Auditing Receipt Chain")
        print("=" * 60)
        
        validator = ChainValidator(signing_key=self.signing_key)
        
        all_valid = True
        for i, receipt in enumerate(self.receipts):
            valid, message = validator.validate_receipt(receipt)
            status = "✓" if valid else "✗"
            print(f"{status} Receipt {i+1}: {receipt.receipt_id[:16]} - {message}")
            
            if receipt.has_npe_data():
                meta = receipt.get_npe_metadata()
                print(f"    NPE Request: {meta['request_id']}")
                print(f"    Proposals: {meta['proposal_count']}")
            
            if not valid:
                all_valid = False
        
        print(f"\nChain Root: {self.chain.get_root()[:16]}...")
        print(f"Chain Tip: {self.chain.get_tip()[:16]}...")
        
        return all_valid
    
    def cleanup(self):
        """Clean up resources."""
        print("\n" + "=" * 60)
        print("Cleanup")
        print("=" * 60)
        
        if self.client:
            self.client.close()
            print("✓ NPE client closed")
        
        print(f"✓ Total receipts recorded: {len(self.receipts)}")
        print(f"✓ Chain length: {self.chain.get_length()}")


def main():
    """Run complete NPE workflow demonstration."""
    
    workflow = NPEWorkflow()
    
    try:
        # Step 1: Start
        if not workflow.start():
            print("Cannot proceed without healthy NPE service")
            return
        
        # Step 2: Submit proposal
        proposal_response = workflow.submit_proposal(
            domain="gr",
            candidate_type="explanation",
            context={
                "query": "Explain the coherence principle",
                "constraints": ["formal", "accessible"],
            },
        )
        
        # Record proposal receipt
        workflow.record_receipt(
            step_type="CUSTOM",
            request_id=proposal_response.get("request_id", ""),
            response=proposal_response,
            decision="PASS",
        )
        
        # Step 3: Handle gate failure
        repair_response = workflow.handle_gate_failure()
        
        # Record repair receipt
        workflow.record_receipt(
            step_type="GATE_EVAL",
            request_id=repair_response.get("request_id", ""),
            response=repair_response,
            decision="WARN",
        )
        
        # Step 5: Audit
        workflow.audit_chain()
        
    finally:
        workflow.cleanup()


if __name__ == "__main__":
    main()
```

**Expected Output:**
```
============================================================
Step 1: Starting NPE Client
============================================================
✓ Connected to NPE at http://localhost:8000
  Version: 1.0.0
  Registry: abc123def456...

============================================================
Step 2: Submitting Proposal Request
============================================================
  Domain: gr
  Candidate Type: explanation
  Context: {'query': 'Explain the coherence principle', ...}

✓ Response received
  Response ID: resp_xyz789
  Candidates: 3

============================================================
Step 3: Gate Failure and Repair Request
============================================================
✗ Gate failed: evidence_sufficiency
  Reasons: ['Evidence below threshold', ...]

✓ Repair response received
  Candidates: 2

============================================================
Step 4: Recording Receipt with NPE Data
============================================================
✓ Receipt created: receipt_abc123...
  NPE Request ID: req_xyz789
  Proposals: 3
  Chain Length: 2

============================================================
Step 5: Auditing Receipt Chain
============================================================
✓ Receipt 1: receipt_abc123 - Receipt valid
    NPE Request: req_xyz789
    Proposals: 3
✓ Receipt 2: receipt_def456 - Receipt valid
    NPE Request: req_abc789
    Proposals: 2

Chain Root: genesis123...
Chain Tip: tip456...

============================================================
Cleanup
============================================================
✓ NPE client closed
✓ Total receipts recorded: 2
✓ Chain length: 2
```

---

## Summary

This example demonstrates the complete CNSC-NPE integration workflow:

1. **Service Setup**: CLI and Python API for starting the NPE service
2. **Proposal Submission**: Using [`ProposerClient.propose()`](src/cnsc/haai/nsc/proposer_client.py:162) for general proposals
3. **Repair Workflow**: Using [`ProposerClient.repair()`](src/cnsc/haai/nsc/proposer_client.py:213) for gate failures
4. **Receipt Integration**: Recording NPE data via [`Receipt.record_npe_request()`](src/cnsc/haai/gml/receipts.py:479) and [`record_npe_response()`](src/cnsc/haai/gml/receipts.py:511)
5. **Audit**: Verifying receipt chains with [`ChainValidator`](src/cnsc/haai/gml/receipts.py:764)

The workflow ensures full traceability from proposal requests through receipt emission, enabling complete audit and replay of NPE interactions.
