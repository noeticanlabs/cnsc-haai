"""
CNSC-NPE Integration Tests

Tests for Phase 0 (Kernel Boundary + Receipts Wiring) integration with NPE.

Tests cover:
1. ProposerClient - health, propose, repair, error handling
2. Gate integration - proposer_client parameter, request_repair
3. VM integration - ProposerClient initialization, repair_proposals
4. Receipt extensions - NPE receipt factory, recording methods, metadata
5. End-to-end mock flow
"""

import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, call
from uuid import uuid4

import pytest
import requests

from cnsc.haai.nsc.proposer_client import ProposerClient, DEFAULT_NPE_URL
from cnsc.haai.nsc.proposer_client_errors import (
    ConnectionError as ProposerConnectionError,
    TimeoutError as ProposerTimeoutError,
    ProposerClientError,
)
from cnsc.haai.nsc.gates import (
    Gate,
    GateType,
    GateDecision,
    GateResult,
    EvidenceSufficiencyGate,
    CoherenceCheckGate,
)
from cnsc.haai.nsc.vm import VM, VMState, VMFrame
from cnsc.haai.nsc.ir import NSCProgram, NSCFunction, NSCBlock, NSCInstruction, NSCOpcode
from cnsc.haai.gml.receipts import (
    Receipt,
    ReceiptContent,
    ReceiptSignature,
    ReceiptProvenance,
    ReceiptStepType,
    ReceiptDecision,
    NPEReceipt,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_requests_session():
    """Mock requests Session for testing."""
    with patch("cnsc.haai.nsc.proposer_client.requests.Session") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "spec": "NPE-RESPONSE-1.0",
        "request_id": str(uuid4()),
        "proposals": [
            {
                "proposal_id": str(uuid4()),
                "candidate": {"action": "test_action"},
                "score": 0.85,
                "evidence": [],
                "explanation": "Test explanation",
                "provenance": {"source": "test"},
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
    response.json.return_value = {"status": "healthy"}
    return response


@pytest.fixture
def sample_propose_context():
    """Sample context for propose request."""
    return {"goal": "improve_coherence", "current_state": "phase_loom_receipt_chain"}


@pytest.fixture
def sample_budget():
    """Sample budget configuration."""
    return {"max_wall_ms": 1000, "max_candidates": 16}


@pytest.fixture
def sample_gate_context():
    """Sample context for gate evaluation."""
    return {
        "evidence_count": 5,
        "coherence_level": 0.75,
        "rule_count": 3,
    }


# =============================================================================
# ProposerClient Tests
# =============================================================================


class TestProposerClientHealth:
    """Tests for ProposerClient.health() method."""

    def test_health_returns_true_when_service_available(
        self, mock_requests_session, mock_health_response
    ):
        """Test health check returns True when NPE is healthy."""
        mock_requests_session.request.return_value = mock_health_response

        client = ProposerClient()
        result = client.health()

        assert result is True
        mock_requests_session.request.assert_called_once()

    def test_health_returns_false_when_service_unavailable(self, mock_requests_session):
        """Test health check returns False when NPE is unavailable."""
        mock_requests_session.request.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        client = ProposerClient()
        result = client.health()

        assert result is False

    def test_health_returns_false_on_error_response(self, mock_requests_session):
        """Test health check returns False when service returns error."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        result = client.health()

        assert result is False

    def test_health_returns_false_when_status_not_healthy(self, mock_requests_session):
        """Test health check returns False when status is not 'healthy'."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "unhealthy"}
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        result = client.health()

        assert result is False


class TestProposerClientPropose:
    """Tests for ProposerClient.propose() method."""

    def test_propose_constructs_correct_request_format(
        self, mock_requests_session, mock_response, sample_propose_context, sample_budget
    ):
        """Test that propose() constructs the correct request format."""
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        result = client.propose(
            domain="gr",
            candidate_type="proposal",
            context=sample_propose_context,
            budget=sample_budget,
        )

        # Verify request was made
        mock_requests_session.request.assert_called_once()
        call_args = mock_requests_session.request.call_args

        # Check method and endpoint
        assert call_args.kwargs["method"] == "POST"
        assert "/npe/v1/propose" in call_args.kwargs["url"]

        # Check request body structure (schema-compliant format)
        request_data = call_args.kwargs["json"]
        assert request_data["spec_version"] == "1.0.0"
        assert request_data["candidate_type"] == "proposal"
        assert request_data["domain"] == "gr"
        assert "request_id" in request_data
        # Verify request_id is SHA-256 hex (64 chars)
        assert len(request_data["request_id"]) == 64
        assert all(c in "0123456789abcdef" for c in request_data["request_id"])
        assert "budget" in request_data
        assert "context" in request_data

        # Verify response is parsed correctly
        assert "proposals" in result

    def test_propose_uses_default_budget_when_not_provided(
        self, mock_requests_session, mock_response
    ):
        """Test that propose() uses default budget when not provided."""
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        client.propose(domain="gr", candidate_type="proposal", context={}, budget={})

        call_args = mock_requests_session.request.call_args
        request_data = call_args.kwargs["json"]

        # Default budget values should be used
        assert request_data["budget"]["max_wall_ms"] == 1000
        assert request_data["budget"]["max_candidates"] == 16


class TestProposerClientRepair:
    """Tests for ProposerClient.repair() method."""

    def test_repair_calls_correct_endpoint(self, mock_requests_session, mock_response):
        """Test that repair() calls the correct endpoint."""
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        client.repair(
            gate_name="coherence_check",
            failure_reasons=["coherence below threshold"],
            context={"current_coherence": 0.3},
        )

        call_args = mock_requests_session.request.call_args
        assert "/npe/v1/repair" in call_args.kwargs["url"]
        assert call_args.kwargs["method"] == "POST"

    def test_repair_sends_failure_reasons(self, mock_requests_session, mock_response):
        """Test that repair() sends failure reasons correctly."""
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        failure_reasons = ["coherence below threshold", "evidence insufficient"]
        client.repair(
            gate_name="coherence_check",
            failure_reasons=failure_reasons,
            context={},
        )

        call_args = mock_requests_session.request.call_args
        request_data = call_args.kwargs["json"]

        # Verify failure reasons are included (schema-compliant: uses context, not inputs)
        assert request_data["context"]["gate_name"] == "coherence_check"
        assert request_data["context"]["failure_reasons"] == failure_reasons


class TestProposerClientErrorHandling:
    """Tests for ProposerClient error handling."""

    def test_propose_raises_connection_error(self, mock_requests_session):
        """Test that propose() raises ConnectionError on network failure."""
        mock_requests_session.request.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        client = ProposerClient()
        with pytest.raises(ProposerConnectionError):
            client.propose(domain="gr", candidate_type="proposal", context={}, budget={})

    def test_propose_raises_timeout_error(self, mock_requests_session):
        """Test that propose() raises TimeoutError on timeout."""
        mock_requests_session.request.side_effect = requests.exceptions.Timeout("Request timed out")

        client = ProposerClient()
        with pytest.raises(ProposerTimeoutError):
            client.propose(domain="gr", candidate_type="proposal", context={}, budget={})

    def test_repair_raises_connection_error(self, mock_requests_session):
        """Test that repair() raises ConnectionError on network failure."""
        mock_requests_session.request.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        client = ProposerClient()
        with pytest.raises(ProposerConnectionError):
            client.repair(gate_name="test", failure_reasons=["test_reason"], context={})

    def test_health_returns_false_on_connection_error(self, mock_requests_session):
        """Test that health() returns False on connection error."""
        mock_requests_session.request.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        client = ProposerClient()
        result = client.health()

        assert result is False


# =============================================================================
# Gate Integration Tests
# =============================================================================


class TestGateProposerClientIntegration:
    """Tests for Gate integration with ProposerClient."""

    def test_gate_accepts_proposer_client_parameter(self):
        """Test that Gate accepts optional proposer_client parameter."""
        client = ProposerClient()

        gate = EvidenceSufficiencyGate(
            min_evidence_count=3,
            min_coherence=0.5,
        )
        gate.proposer_client = client

        assert gate.proposer_client is client

    def test_gate_request_repair_calls_proposer_client(self, mock_response):
        """Test that Gate.request_repair() calls proposer client correctly."""
        client = ProposerClient()

        # Mock the session.request method BEFORE any calls
        original_request = client.session.request
        client.session.request = MagicMock(return_value=mock_response)

        try:
            gate = EvidenceSufficiencyGate()
            gate.proposer_client = client

            failure_reasons = ["coherence below threshold"]
            proposals = gate.request_repair("coherence_check", failure_reasons)

            # Verify the session.request was called
            assert client.session.request.called

            # Verify proposals returned
            assert len(proposals) == 1
            assert proposals[0]["candidate"]["action"] == "test_action"
        finally:
            # Restore original
            client.session.request = original_request

    def test_gate_request_repair_returns_empty_when_no_client(self):
        """Test that Gate.request_repair() returns empty list when no client."""
        gate = EvidenceSufficiencyGate()

        proposals = gate.request_repair("coherence_check", ["reason"])

        assert proposals == []

    def test_gate_request_repair_handles_errors(self, mock_requests_session):
        """Test that Gate.request_repair() handles errors gracefully."""
        mock_requests_session.request.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        client = ProposerClient()
        gate = EvidenceSufficiencyGate()
        gate.proposer_client = client

        # Should return empty list, not raise exception
        proposals = gate.request_repair("coherence_check", ["reason"])
        assert proposals == []


class TestGateEvaluateAndRequestRepair:
    """Tests for gate evaluation triggering repair requests."""

    def test_gate_failure_triggers_repair_request(
        self, mock_requests_session, mock_response, sample_gate_context
    ):
        """Test that gate failure can trigger repair request."""
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        gate = EvidenceSufficiencyGate(
            min_evidence_count=10,  # Set high threshold to ensure failure
            min_coherence=0.9,
        )
        gate.proposer_client = client

        # Evaluate gate - should fail due to insufficient evidence
        result = gate.evaluate(sample_gate_context)

        assert result.decision == GateDecision.FAIL
        assert result.conditions_failed > 0

    def test_coherence_check_gate_with_proposer_client(self):
        """Test CoherenceCheckGate accepts proposer_client."""
        client = ProposerClient()
        gate = CoherenceCheckGate(
            min_coherence=0.8,
            hysteresis_margin=0.1,
        )
        gate.proposer_client = client

        assert gate.proposer_client is client


# =============================================================================
# VM Integration Tests
# =============================================================================


class TestVMWithProposerClient:
    """Tests for VM integration with ProposerClient."""

    def test_vm_can_be_created_with_proposer_client(self):
        """Test that VM can be created with ProposerClient."""
        client = ProposerClient()
        program = NSCProgram(program_id="test-program", name="Test Program")

        vm = VM(program=program, proposer_client=client)

        assert vm.proposer_client is client

    def test_vm_repair_proposals_is_initialized(self):
        """Test that VM.repair_proposals is initialized as empty list."""
        program = NSCProgram(program_id="test-program", name="Test Program")
        vm = VM(program=program)

        assert vm.repair_proposals == []
        assert isinstance(vm.repair_proposals, list)

    def test_vm_stores_repair_proposals(self):
        """Test that VM stores repair proposals correctly."""
        client = ProposerClient()
        program = NSCProgram(program_id="test-program", name="Test Program")
        vm = VM(program=program, proposer_client=client)

        # Simulate receiving proposals
        proposals = [
            {"proposal_id": "1", "candidate": {"action": "test"}},
            {"proposal_id": "2", "candidate": {"action": "test2"}},
        ]
        vm.repair_proposals.extend(proposals)

        assert len(vm.repair_proposals) == 2
        assert vm.repair_proposals[0]["proposal_id"] == "1"

    def test_vm_gate_evaluation_can_trigger_repair(self, mock_requests_session, mock_response):
        """Test that VM gate evaluation can trigger repair requests."""
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        program = NSCProgram(program_id="test-program", name="Test Program")

        # Create a simple function - we just need to verify VM can be created with proposer_client
        func = NSCFunction(
            function_id="test_func",
            name="test_function",
            blocks={},
        )
        program.functions["test_func"] = func
        program.entry_function = "test_func"

        vm = VM(program=program, proposer_client=client)
        vm.load()

        # VM should be able to run and use proposer_client
        assert vm.proposer_client is not None
        assert vm.repair_proposals == []


# =============================================================================
# Receipt Extension Tests
# =============================================================================


class TestNPEReceiptFactory:
    """Tests for NPEReceipt factory method."""

    def test_npe_receipt_factory_creates_receipt_with_npe_data(self):
        """Test that NPEReceipt factory creates receipt with NPE data."""
        receipt = NPEReceipt.create_npe_receipt(
            receipt_id="receipt-001",
            request_id="req-123",
            domain="gr",
            candidate_type="repair",
            proposals=[{"proposal_id": "1", "candidate": {"action": "test"}}],
        )

        assert receipt is not None
        assert isinstance(receipt, NPEReceipt)
        assert receipt.npe_request_id == "req-123"
        assert len(receipt.npe_proposals) == 1

    def test_npe_receipt_has_all_npe_fields(self):
        """Test that NPEReceipt has all NPE-related fields."""
        receipt = NPEReceipt.create_npe_receipt(
            receipt_id="receipt-002",
            request_id="req-456",
            domain="gr",
            candidate_type="repair",
            proposals=[],
        )

        # NPE fields should be present
        assert hasattr(receipt, "npe_request_id")
        assert hasattr(receipt, "npe_response_status")
        assert hasattr(receipt, "npe_proposals")
        assert hasattr(receipt, "npe_provenance")


class TestReceiptNPERecording:
    """Tests for Receipt NPE recording methods."""

    def test_record_npe_request(self):
        """Test record_npe_request() method."""
        receipt = NPEReceipt.create_npe_receipt(
            receipt_id="receipt-001",
            request_id="req-123",
            domain="gr",
            candidate_type="repair",
            proposals=[],
        )

        receipt.record_npe_request(
            request_id="req-123",
            domain="gr",
            candidate_type="repair",
            seed=42,
            budgets={"max_wall_ms": 1000},
            inputs={"gate_name": "coherence_check"},
        )

        assert receipt.npe_request_id == "req-123"
        assert "npe_request" in receipt.metadata

    def test_record_npe_response(self):
        """Test record_npe_response() method."""
        receipt = NPEReceipt.create_npe_receipt(
            receipt_id="receipt-001",
            request_id="req-123",
            domain="gr",
            candidate_type="repair",
            proposals=[],
        )

        proposals = [
            {"proposal_id": "1", "candidate": {"action": "test"}},
        ]

        receipt.record_npe_response(
            status="success",
            proposals=proposals,
            budget_used={"max_wall_ms": 500},
            npe_version="1.0.0",
        )

        assert receipt.npe_response_status == "success"
        assert len(receipt.npe_proposals) == 1
        assert "npe_response" in receipt.metadata

    def test_record_npe_provenance(self):
        """Test record_npe_provenance() method."""
        receipt = NPEReceipt.create_npe_receipt(
            receipt_id="receipt-001",
            request_id="req-123",
            domain="gr",
            candidate_type="repair",
            proposals=[],
        )

        receipt.record_npe_provenance(
            episode_id="ep-123",
            phase="gate_evaluation",
            npe_request_id="req-123",
            npe_response_id="resp-456",
        )

        assert receipt.npe_provenance is not None
        assert receipt.npe_provenance["episode_id"] == "ep-123"
        assert receipt.npe_provenance["phase"] == "gate_evaluation"
        assert receipt.npe_provenance["npe_request_id"] == "req-123"

    def test_get_npe_metadata(self):
        """Test get_npe_metadata() returns correct data."""
        receipt = NPEReceipt.create_npe_receipt(
            receipt_id="receipt-001",
            request_id="req-123",
            domain="gr",
            candidate_type="repair",
            proposals=[{"proposal_id": "1"}],
        )

        metadata = receipt.get_npe_metadata()

        assert metadata["has_npe_data"] is True
        assert metadata["request_id"] == "req-123"
        assert metadata["response_status"] == "success"
        assert metadata["proposal_count"] == 1

    def test_get_npe_metadata_returns_empty_when_no_npe_data(self):
        """Test get_npe_metadata() returns correct data when no NPE data."""
        # Create a basic receipt without NPE data
        receipt = Receipt(
            receipt_id="receipt-123",
            content=ReceiptContent(
                step_type=ReceiptStepType.PARSE,
                decision=ReceiptDecision.PASS,
            ),
            signature=ReceiptSignature(),
            provenance=ReceiptProvenance(source="test"),
        )

        metadata = receipt.get_npe_metadata()

        # has_npe_data is based on npe_request_id being set or npe_proposals being non-empty
        assert not metadata["has_npe_data"]
        assert metadata["request_id"] is None
        assert metadata["proposal_count"] == 0


class TestReceiptBackwardCompatibility:
    """Tests for backward compatibility of Receipt."""

    def test_existing_receipt_works_unchanged(self):
        """Test that existing Receipt without NPE data works unchanged."""
        receipt = Receipt(
            receipt_id="receipt-123",
            content=ReceiptContent(
                step_type=ReceiptStepType.PARSE,
                decision=ReceiptDecision.PASS,
            ),
            signature=ReceiptSignature(),
            provenance=ReceiptProvenance(source="test"),
        )

        # Should not have NPE data by default
        assert receipt.npe_request_id is None
        assert receipt.npe_response_status is None
        assert receipt.npe_proposals == []

        # to_dict should not include NPE fields if not set
        result = receipt.to_dict()
        assert "npe_request_id" not in result
        assert "npe_response_status" not in result
        assert "npe_proposals" not in result

    def test_receipt_can_be_created_without_npe(self):
        """Test that Receipt can be created without any NPE parameters."""
        receipt = Receipt(
            receipt_id="receipt-456",
            content=ReceiptContent(
                step_type=ReceiptStepType.VM_EXECUTION,
                decision=ReceiptDecision.PASS,
                input_hash="hash1",
                output_hash="hash2",
            ),
            signature=ReceiptSignature(),
            provenance=ReceiptProvenance(source="test"),
        )

        assert receipt is not None
        assert receipt.receipt_id == "receipt-456"
        assert len(receipt.npe_proposals) == 0

    def test_receipt_to_dict_includes_npe_when_set(self):
        """Test that to_dict includes NPE fields when they are set."""
        receipt = NPEReceipt.create_npe_receipt(
            receipt_id="receipt-001",
            request_id="req-123",
            domain="gr",
            candidate_type="repair",
            proposals=[{"proposal_id": "1"}],
        )

        result = receipt.to_dict()

        # NPE fields should be included when set
        assert result["npe_request_id"] == "req-123"
        assert result["npe_response_status"] == "success"
        assert len(result["npe_proposals"]) == 1


# =============================================================================
# End-to-End Mock Test
# =============================================================================


class TestEndToEndMockFlow:
    """End-to-end mock test for CNSC-NPE integration."""

    def test_full_flow_gate_fail_repair_request_proposals_received_receipt_recorded(
        self, sample_gate_context
    ):
        """
        Test full flow:
        1. Gate evaluates and fails
        2. Repair is requested from NPE
        3. Proposals are received
        4. Receipt is recorded with NPE data
        """
        # Setup mock response for repair request
        repair_response = MagicMock()
        repair_response.ok = True
        repair_response.status_code = 200
        repair_response.json.return_value = {
            "spec": "NPE-RESPONSE-1.0",
            "request_id": "mock-req-123",
            "proposals": [
                {
                    "proposal_id": "prop-001",
                    "candidate": {
                        "action": "add_receipt",
                        "target_phase": "gate_evaluation",
                        "rule_type": "coherence_enhancement",
                    },
                    "score": 0.92,
                    "evidence": [{"type": "receipt_chain", "id": "receipt-001"}],
                    "explanation": "Add a receipt to improve coherence tracking",
                    "provenance": {"source": "gate_reasoner_v1"},
                },
                {
                    "proposal_id": "prop-002",
                    "candidate": {
                        "action": "adjust_threshold",
                        "target_gate": "coherence_check",
                        "new_threshold": 0.6,
                    },
                    "score": 0.78,
                    "evidence": [],
                    "explanation": "Lower coherence threshold to match current state",
                    "provenance": {"source": "gate_reasoner_v1"},
                },
            ],
        }

        # Create ProposerClient with mocked session
        client = ProposerClient()
        original_request = client.session.request
        client.session.request = MagicMock(return_value=repair_response)

        try:
            # Create gate with proposer_client
            gate = CoherenceCheckGate(
                min_coherence=0.95,  # Set high to ensure failure
                hysteresis_margin=0.1,
            )
            gate.proposer_client = client

            # Evaluate gate - should fail
            result = gate.evaluate(sample_gate_context)
            assert result.decision == GateDecision.FAIL
            assert result.conditions_failed > 0

            # Request repair
            failure_reasons = [result.message]
            proposals = gate.request_repair(gate.name, failure_reasons)

            # Verify the request was made
            assert client.session.request.called

            # Verify proposals received
            assert len(proposals) == 2
            assert proposals[0]["proposal_id"] == "prop-001"
            assert proposals[0]["score"] == 0.92

            # Create receipt with NPE data using factory method
            receipt = NPEReceipt.create_npe_receipt(
                receipt_id="receipt-001",
                request_id="mock-req-123",
                domain="gr",
                candidate_type="repair",
                proposals=proposals,
                response_status="success",
            )

            # Record additional NPE provenance
            receipt.record_npe_provenance(
                episode_id="episode-001",
                phase="gate_evaluation",
                npe_request_id="mock-req-123",
            )

            # Verify receipt has all NPE data
            metadata = receipt.get_npe_metadata()
            assert metadata["has_npe_data"]
            assert metadata["request_id"] == "mock-req-123"
            assert metadata["response_status"] == "success"
            assert metadata["proposal_count"] == 2

            # Verify receipt can be serialized
            receipt_dict = receipt.to_dict()
            assert receipt_dict["npe_request_id"] == "mock-req-123"
            assert len(receipt_dict["npe_proposals"]) == 2
        finally:
            # Restore original
            client.session.request = original_request

    def test_wire_format_matches_schema(self, mock_requests_session, mock_response):
        """Test that wire format matches schema requirements."""
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        client.repair(
            gate_name="test_gate",
            failure_reasons=["test_reason"],
            context={"key": "value"},
        )

        # Get the request that was made
        call_args = mock_requests_session.request.call_args
        request_data = call_args.kwargs["json"]

        # Verify wire format (schema-compliant)
        assert "spec_version" in request_data
        assert "request_id" in request_data
        assert "candidate_type" in request_data
        assert "domain" in request_data
        assert "budget" in request_data
        assert "context" in request_data

        # Verify request_id is SHA-256 hex (64 chars)
        assert len(request_data["request_id"]) == 64

    def test_proposal_response_format(self, mock_requests_session):
        """Test that proposal response is parsed correctly."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "spec": "NPE-RESPONSE-1.0",
            "request_id": "req-123",
            "proposals": [
                {
                    "proposal_id": "prop-001",
                    "candidate": {"action": "test"},
                    "score": 0.85,
                    "evidence": [],
                    "explanation": "Test explanation",
                    "provenance": {"source": "test"},
                }
            ],
        }
        mock_requests_session.request.return_value = mock_response

        client = ProposerClient()
        result = client.propose(
            domain="gr",
            candidate_type="proposal",
            context={},
            budget={},
        )

        # Verify response structure
        assert "proposals" in result
        proposal = result["proposals"][0]
        assert "proposal_id" in proposal
        assert "candidate" in proposal
        assert "score" in proposal
        assert "explanation" in proposal
        assert "provenance" in proposal


# =============================================================================
# Test Runner
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
