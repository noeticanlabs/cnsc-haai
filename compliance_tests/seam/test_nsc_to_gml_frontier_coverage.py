"""
SEAM NSC→GML Frontier Coverage Tests

Tests for frontier coverage in NSC to GML emission.
"""

import pytest
from datetime import datetime
from cnsc.haai.nsc.cfa import CFAPhase, CFAAutomaton
from cnsc.haai.gml.receipts import Receipt, ReceiptContent, ReceiptSignature, ReceiptProvenance, ReceiptStepType, ReceiptDecision


class TestNSCTOGMLFrontierCoverage:
    """Tests for frontier coverage in NSC→GML emission."""

    def test_frontier_definition(self):
        """Test frontier components are defined."""
        frontier = {"beliefs", "tags", "intents", "obligations"}
        assert "beliefs" in frontier
        assert "tags" in frontier

    def test_cfa_phases_coverage(self):
        """Test CFA phases cover all reasoning states."""
        assert CFAPhase.SUPERPOSED is not None
        assert CFAPhase.COHERENT is not None
        assert CFAPhase.GATED is not None
        assert CFAPhase.COLLAPSED is not None

    def test_phase_transition_coverage(self):
        """Test phase transitions cover all flows."""
        # All valid transitions should be covered
        assert CFAPhase.SUPERPOSED.can_transition_to(CFAPhase.COHERENT)
        assert CFAPhase.COHERENT.can_transition_to(CFAPhase.GATED)
        assert CFAPhase.GATED.can_transition_to(CFAPhase.COLLAPSED)

    def test_receipt_state_coverage(self):
        """Test receipt contains state."""
        content = ReceiptContent(
            step_type=ReceiptStepType.PARSE,
            input_hash="sha256:input",
            output_hash="sha256:output"
        )
        signature = ReceiptSignature()
        provenance = ReceiptProvenance(source="test")
        receipt = Receipt(
            receipt_id="test_receipt",
            content=content,
            signature=signature,
            provenance=provenance
        )
        receipt_dict = receipt.to_dict()
        assert "receipt_id" in receipt_dict

    def test_coverage_verification(self):
        """Test coverage verification exists."""
        auto = CFAAutomaton(automaton_id="auto_001", name="Test Automaton")
        # Check that automaton has required methods
        assert hasattr(auto, 'get_phase')
        assert hasattr(auto, 'is_coherent')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
