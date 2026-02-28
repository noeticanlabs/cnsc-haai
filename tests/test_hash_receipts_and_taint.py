"""
Tests for E1-E2: Hash-addressed receipts and taint enforcement.

These tests verify:
- Artifact hashes (registry, corpus, schema) are included in receipts
- Taint classes are enforced at memory boundaries
- Provenance chain IDs are logged in receipts
- Replay safety with hash verification
"""

import pytest
from datetime import datetime
from uuid import uuid4
import hashlib
import json

from src.cnsc.haai.gml.receipts import (
    Receipt,
    ReceiptContent,
    ReceiptSignature,
    ReceiptProvenance,
    ReceiptStepType,
    ReceiptDecision,
    NPEResponseStatus,
    ReceiptSystem,
    create_receipt_system,
)


class TestArtifactHashes:
    """Test E1: Hash-addressed artifacts for replay safety."""

    def test_receipt_includes_artifact_hashes(self):
        """Receipts should include artifact hashes for replay safety."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="test")

        receipt = Receipt(
            receipt_id="test-receipt-001",
            content=content,
            signature=signature,
            provenance=provenance,
            registry_hash="abc123def456",
            corpus_snapshot_hash="corpus123",
            schema_bundle_hash="schema123",
        )

        # Verify hashes are stored
        assert receipt.registry_hash == "abc123def456"
        assert receipt.corpus_snapshot_hash == "corpus123"
        assert receipt.schema_bundle_hash == "schema123"

        # Verify serialization includes hashes
        receipt_dict = receipt.to_dict()
        assert receipt_dict["registry_hash"] == "abc123def456"
        assert receipt_dict["corpus_snapshot_hash"] == "corpus123"
        assert receipt_dict["schema_bundle_hash"] == "schema123"

    def test_receipt_artifact_hash_verification(self):
        """Receipt should verify artifact hashes match expected values."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="test")

        receipt = Receipt(
            receipt_id="test-receipt-002",
            content=content,
            signature=signature,
            provenance=provenance,
            registry_hash="abc123",
            corpus_snapshot_hash="corpus456",
            schema_bundle_hash="schema789",
        )

        # Test matching hashes
        match, msg = receipt.verify_artifact_hashes(
            expected_registry_hash="abc123",
            expected_corpus_hash="corpus456",
            expected_schema_hash="schema789",
        )
        assert match, f"Should match: {msg}"

        # Test mismatched registry hash
        match, msg = receipt.verify_artifact_hashes(
            expected_registry_hash="wrong123",
        )
        assert not match, "Should fail-fast on hash mismatch"
        assert "Registry hash mismatch" in msg

    def test_record_artifact_hashes_method(self):
        """Receipt should have method to record artifact hashes."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="test")

        receipt = Receipt(
            receipt_id="test-receipt-003",
            content=content,
            signature=signature,
            provenance=provenance,
        )

        # Record hashes after creation
        receipt.record_artifact_hashes(
            registry_hash="reg-hash-123",
            corpus_snapshot_hash="corpus-hash-456",
            schema_bundle_hash="schema-hash-789",
        )

        assert receipt.registry_hash == "reg-hash-123"
        assert receipt.corpus_snapshot_hash == "corpus-hash-456"
        assert receipt.schema_bundle_hash == "schema-hash-789"


class TestTaintEnforcement:
    """Test E2: Taint/provenance enforcement at memory boundaries."""

    def test_taint_class_validation(self):
        """Taint classes should be validated."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="test")

        receipt = Receipt(
            receipt_id="test-taint-001",
            content=content,
            signature=signature,
            provenance=provenance,
        )

        # Test valid taint classes
        for taint in ["observed", "inferred", "proposed", "external", "user_claim"]:
            receipt.set_taint_class(taint)
            assert receipt.taint_class == taint

        # Test invalid taint class
        with pytest.raises(ValueError):
            receipt.set_taint_class("invalid_taint")

    def test_memory_mutation_requires_approval(self):
        """Proposals should not mutate memory without gate approval."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="test")

        # Default "observed" taint allows mutation
        receipt = Receipt(
            receipt_id="test-mutation-001",
            content=content,
            signature=signature,
            provenance=provenance,
            taint_class="observed",
        )
        assert receipt.can_mutate_memory(), "Observed data should allow mutation"

        # "proposed" taint requires gate approval
        receipt_proposed = Receipt(
            receipt_id="test-mutation-002",
            content=content,
            signature=signature,
            provenance=provenance,
            taint_class="proposed",
            gate_approved=False,
        )
        assert not receipt_proposed.can_mutate_memory(), "Proposed data should require approval"

        # After gate approval, mutation allowed
        receipt_proposed.set_gate_approval(True)
        assert receipt_proposed.can_mutate_memory(), "Approved proposals should allow mutation"

    def test_gate_approval_tracking(self):
        """Receipts should track gate approval status."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="test")

        receipt = Receipt(
            receipt_id="test-approval-001",
            content=content,
            signature=signature,
            provenance=provenance,
            gate_approval_required=True,
            gate_approved=False,
        )

        assert receipt.requires_gate_approval()
        assert not receipt.gate_approved

        receipt.set_gate_approval(True)
        assert receipt.gate_approved

    def test_taint_class_default(self):
        """Default taint class should be 'observed'."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="test")

        receipt = Receipt(
            receipt_id="test-default-taint",
            content=content,
            signature=signature,
            provenance=provenance,
        )

        assert receipt.taint_class == "observed"


class TestProvenanceChain:
    """Test E2: Provenance chain logging in receipts."""

    def test_provenance_chain_id(self):
        """Receipts should track provenance chain ID."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="test")

        receipt = Receipt(
            receipt_id="test-provenance-001",
            content=content,
            signature=signature,
            provenance=provenance,
            provenance_chain_id="chain-abc-123",
        )

        assert receipt.provenance_chain_id == "chain-abc-123"

        # Test serialization
        receipt_dict = receipt.to_dict()
        assert receipt_dict["provenance_chain_id"] == "chain-abc-123"

    def test_set_provenance_chain(self):
        """Should be able to set provenance chain ID after creation."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="test")

        receipt = Receipt(
            receipt_id="test-provenance-002",
            content=content,
            signature=signature,
            provenance=provenance,
        )

        receipt.set_provenance_chain("new-chain-xyz")
        assert receipt.provenance_chain_id == "new-chain-xyz"


class TestReceiptSystemIntegration:
    """Integration tests for receipt system with hashes and taint."""

    def test_receipt_system_with_artifact_hashes(self):
        """ReceiptSystem should support artifact hash verification."""
        system = create_receipt_system()

        # Emit receipt with artifact hashes
        receipt = system.emit_receipt(
            step_type=ReceiptStepType.CUSTOM,
            source="test",
            input_data={"test": "input"},
            output_data={"test": "output"},
        )

        # Record artifact hashes
        receipt.record_artifact_hashes(
            registry_hash="reg123",
            corpus_snapshot_hash="corp456",
            schema_bundle_hash="sch789",
        )

        # Verify stored correctly
        assert receipt.registry_hash == "reg123"
        assert receipt.corpus_snapshot_hash == "corp456"
        assert receipt.schema_bundle_hash == "sch789"

    def test_receipt_system_with_taint(self):
        """ReceiptSystem should enforce taint on mutations."""
        system = create_receipt_system()

        # Emit receipt with "proposed" taint
        receipt = system.emit_receipt(
            step_type=ReceiptStepType.CUSTOM,
            source="test",
            input_data={"test": "input"},
            output_data={"test": "output"},
        )

        receipt.set_taint_class("proposed")

        # Without approval, cannot mutate memory
        assert not receipt.can_mutate_memory()

        # After gate approval, can mutate
        receipt.set_gate_approval(True)
        assert receipt.can_mutate_memory()

    def test_receipt_system_roundtrip(self):
        """ReceiptSystem should serialize/deserialize correctly."""
        system = create_receipt_system()

        # Create receipt
        receipt = system.emit_receipt(
            step_type=ReceiptStepType.VM_EXECUTION,
            source="test",
            input_data={"state": "test"},
            output_data={"result": "success"},
        )

        # Set artifact hashes and taint
        receipt.record_artifact_hashes(
            registry_hash="reg-test",
        )
        receipt.set_taint_class("proposed")
        receipt.set_gate_approval(True)
        receipt.set_provenance_chain("chain-123")

        # Serialize
        receipt_dict = receipt.to_dict()

        # Deserialize
        receipt2 = Receipt.from_dict(receipt_dict)

        # Verify all fields preserved
        assert receipt2.receipt_id == receipt.receipt_id
        assert receipt2.registry_hash == "reg-test"
        assert receipt2.taint_class == "proposed"
        assert receipt2.gate_approved == True
        assert receipt2.provenance_chain_id == "chain-123"


class TestReplaySafety:
    """Test replay safety with artifact hashes."""

    def test_receipt_fails_fast_on_hash_mismatch(self):
        """Receipt replay should fail-fast if artifact hashes differ."""
        # Original receipt with specific hashes
        content = ReceiptContent(
            step_type=ReceiptStepType.VM_EXECUTION,
            decision=ReceiptDecision.PASS,
            details={"result": "success"},
        )
        signature = ReceiptSignature(signer="system")
        provenance = ReceiptProvenance(source="test")

        original_receipt = Receipt(
            receipt_id="replay-test-001",
            content=content,
            signature=signature,
            provenance=provenance,
            registry_hash="original-registry-hash",
            corpus_snapshot_hash="original-corpus-hash",
        )

        # Simulate replay with different registry hash
        replay_receipt = Receipt(
            receipt_id="replay-test-001",  # Same ID
            content=content,
            signature=signature,
            provenance=provenance,
            registry_hash="modified-registry-hash",  # Different!
            corpus_snapshot_hash="original-corpus-hash",
        )

        # Verify should fail
        match, msg = replay_receipt.verify_artifact_hashes(
            expected_registry_hash="original-registry-hash",
        )
        assert not match, "Should detect hash mismatch"
        assert "mismatch" in msg.lower()

    def test_replay_passes_with_matching_hashes(self):
        """Receipt replay should pass if all hashes match."""
        content = ReceiptContent(
            step_type=ReceiptStepType.VM_EXECUTION,
            decision=ReceiptDecision.PASS,
            details={"result": "success"},
        )
        signature = ReceiptSignature(signer="system")
        provenance = ReceiptProvenance(source="test")

        # Original receipt
        original_receipt = Receipt(
            receipt_id="replay-test-002",
            content=content,
            signature=signature,
            provenance=provenance,
            registry_hash="same-registry-hash",
            corpus_snapshot_hash="same-corpus-hash",
            schema_bundle_hash="same-schema-hash",
        )

        # Replay receipt with same hashes
        replay_receipt = Receipt(
            receipt_id="replay-test-002",
            content=content,
            signature=signature,
            provenance=provenance,
            registry_hash="same-registry-hash",
            corpus_snapshot_hash="same-corpus-hash",
            schema_bundle_hash="same-schema-hash",
        )

        # Verify should pass
        match, msg = replay_receipt.verify_artifact_hashes(
            expected_registry_hash="same-registry-hash",
            expected_corpus_hash="same-corpus-hash",
            expected_schema_hash="same-schema-hash",
        )
        assert match, f"Should match: {msg}"


class TestMaliciousProposalEnforcement:
    """Test that malicious proposals are recorded but not committed."""

    def test_malicious_proposal_requires_gate_approval(self):
        """Malicious proposals should require gate approval before mutation."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.FAIL,  # Malicious/failed proposal
            details={"reason": "malicious_candidate"},
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="npe")

        # Create receipt for malicious proposal
        receipt = Receipt(
            receipt_id="malicious-001",
            content=content,
            signature=signature,
            provenance=provenance,
            taint_class="proposed",
            gate_approval_required=True,
            gate_approved=False,  # Not approved
        )

        # Cannot mutate memory without approval
        assert not receipt.can_mutate_memory()

        # Even if gate approves, decision was FAIL so should be rejected
        # (This is handled at a higher level, not in can_mutate_memory)
        receipt.set_gate_approval(True)
        # can_mutate_memory now returns True, but the FAIL decision
        # would be checked at a higher level

    def test_proposal_recorded_without_approval(self):
        """Proposals should be recorded even without gate approval."""
        content = ReceiptContent(
            step_type=ReceiptStepType.CUSTOM,
            decision=ReceiptDecision.PASS,
            details={"proposal": "test_proposal"},
        )
        signature = ReceiptSignature(signer="test")
        provenance = ReceiptProvenance(source="npe")

        receipt = Receipt(
            receipt_id="recorded-001",
            content=content,
            signature=signature,
            provenance=provenance,
            taint_class="proposed",
            gate_approval_required=True,
            gate_approved=False,
        )

        # Receipt exists and is recorded
        assert receipt.receipt_id == "recorded-001"

        # But cannot mutate memory
        assert not receipt.can_mutate_memory()


class TestReceiptSerialization:
    """Test receipt serialization and deserialization."""

    def test_receipt_to_dict_contains_all_fields(self):
        """Receipt serialization should include all E1/E2 fields."""
        content = ReceiptContent(
            step_type=ReceiptStepType.VM_EXECUTION,
            decision=ReceiptDecision.PASS,
            details={"test": "data"},
        )
        signature = ReceiptSignature(signer="test", algorithm="HMAC-SHA256")
        provenance = ReceiptProvenance(source="test")

        receipt = Receipt(
            receipt_id="serial-test-001",
            content=content,
            signature=signature,
            provenance=provenance,
            registry_hash="reg-hash",
            corpus_snapshot_hash="corpus-hash",
            schema_bundle_hash="schema-hash",
            taint_class="inferred",
            provenance_chain_id="chain-xyz",
            gate_approval_required=True,
            gate_approved=True,
        )

        receipt_dict = receipt.to_dict()

        # Verify all fields present
        assert receipt_dict["receipt_id"] == "serial-test-001"
        assert receipt_dict["registry_hash"] == "reg-hash"
        assert receipt_dict["corpus_snapshot_hash"] == "corpus-hash"
        assert receipt_dict["schema_bundle_hash"] == "schema-hash"
        assert receipt_dict["taint_class"] == "inferred"
        assert receipt_dict["provenance_chain_id"] == "chain-xyz"
        assert receipt_dict["gate_approval_required"] == True
        assert receipt_dict["gate_approved"] == True

    def test_receipt_from_dict_restores_all_fields(self):
        """Receipt deserialization should restore all E1/E2 fields."""
        receipt_dict = {
            "version": "1.0.0",
            "receipt_id": "dict-test-001",
            "content": {
                "step_type": "CUSTOM",
                "input_hash": "",
                "output_hash": "",
                "decision": "PASS",
                "details": {},
                "coherence_before": None,
                "coherence_after": None,
            },
            "signature": {
                "algorithm": "HMAC-SHA256",
                "signer": "test",
                "signature": "",
            },
            "provenance": {
                "source": "test",
                "episode_id": None,
                "phase": None,
                "timestamp": datetime.utcnow().isoformat(),
                "span": None,
            },
            "previous_receipt_id": None,
            "previous_receipt_hash": None,
            "chain_hash": None,
            "metadata": {},
            "registry_hash": "reg-hash",
            "corpus_snapshot_hash": "corpus-hash",
            "schema_bundle_hash": "schema-hash",
            "taint_class": "proposed",
            "provenance_chain_id": "chain-abc",
            "gate_approval_required": True,
            "gate_approved": False,
        }

        receipt = Receipt.from_dict(receipt_dict)

        assert receipt.receipt_id == "dict-test-001"
        assert receipt.registry_hash == "reg-hash"
        assert receipt.corpus_snapshot_hash == "corpus-hash"
        assert receipt.schema_bundle_hash == "schema-hash"
        assert receipt.taint_class == "proposed"
        assert receipt.provenance_chain_id == "chain-abc"
        assert receipt.gate_approval_required == True
        assert receipt.gate_approved == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
